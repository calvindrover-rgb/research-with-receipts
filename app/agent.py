"""Agent loop: plan -> write code -> run in sandbox -> self-heal on error -> explain with receipts."""
import re, time
from . import llm, sandbox
SYSTEM = """You are a public-records research agent. Answer the user's question by writing ONE Python script.
Only the `pubdata` module is available (stdlib too). Functions:
 fda_recalls(firm=None, keyword=None, category='food'|'drug'|'device', limit=50) -> list of openFDA enforcement dicts (recalling_firm, reason_for_recall, classification, report_date, product_description)
 nhtsa_recalls(make, model, year) -> list
 usaspending_awards(recipient=None, keyword=None, limit=25) -> list of dicts ('Recipient Name','Award Amount','Awarding Agency','Award ID')
 sec_search(q, forms='10-K'), sec_facts(cik), federal_register(term, limit=20), fetch(url)
Keep API calls under 15. End with pubdata.emit(result) where result is a JSON-serializable list of dicts.
Reply with only a ```python code block."""
MAX_TRIES = 3

def extract(text):
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()

def run(question, on_event=lambda e: None):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    steps = []
    for attempt in range(1, MAX_TRIES + 1):
        code = extract(llm.chat(msgs))
        on_event({"type": "code", "attempt": attempt, "code": code})
        t = time.time(); res = sandbox.run(code); res["seconds"] = round(time.time() - t, 2)
        steps.append({"attempt": attempt, "code": code, **res}); on_event({"type": "exec", **res})
        if "BLOCKED by sandbox policy" in res["stderr"] or res["timed_out"]:
            return {"question": question, "status": "contained", "steps": steps,
                    "report": "Containment triggered: the sandbox refused the action. Task environment destroyed.", "receipts": res["receipts"]}
        if res["exit_code"] == 0 and res["result"] is not None:
            msgs += [{"role": "assistant", "content": f"```python\n{code}\n```"},
                     {"role": "user", "content": f"SANDBOX RESULT (real, executed): {str(res['result'])[:6000]}\nSources: {[r['url'] for r in res['receipts']][:20]}\n"
                      "Write a concise markdown report answering the question. Cite sources as [n] referring to the source list order. Only state facts present in the result."}]
            return {"question": question, "status": "ok", "steps": steps, "result": res["result"],
                    "report": llm.chat(msgs), "receipts": res["receipts"]}
        msgs += [{"role": "assistant", "content": f"```python\n{code}\n```"},
                 {"role": "user", "content": f"The script failed (exit {res['exit_code']}). stderr:\n{res['stderr'][-2000:]}\nFix it and reply with the full corrected script."}]
    return {"question": question, "status": "failed", "steps": steps, "report": "Gave up after retries.", "receipts": []}
