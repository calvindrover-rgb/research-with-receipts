"""Agent loop: plan -> write code -> run in sandbox -> self-heal on error -> explain with receipts."""
import re, time, datetime
from . import llm, sandbox
SYSTEM = """You are a public-records research agent. Answer the user's question by writing ONE Python script.
Only the `pubdata` module is available (stdlib too). Functions:
 fda_recalls(firm=None, keyword=None, category='food'|'drug'|'device', limit=50) -> newest-first list of openFDA enforcement dicts (recalling_firm, reason_for_recall, classification, report_date, product_description)
 nhtsa_recalls(make, model, year) -> list (recalls for one specific vehicle make/model/model-year)
 nhtsa_recall_campaigns(start='YYYY-MM-DD', end='YYYY-MM-DD', manufacturer=None, limit=5000) -> list of NHTSA recall campaigns filed in that date range
   (keys: nhtsa_id, report_received_date, manufacturer, subject, component, recall_type ('Vehicle','Equipment','Tire','Child Seat'), potentially_affected (string number))
 nhtsa_recall_counts_by_manufacturer(start, end, recall_type='Vehicle', top=10) -> list of {'manufacturer','recalls','potentially_affected'} sorted desc
 usaspending_awards(recipient=None, keyword=None, limit=25, start='2020-01-01', end='2026-12-31', naics=None) -> list of dicts ('Recipient Name','Award Amount','Awarding Agency','Award ID')
 usaspending_top_recipients(naics, fiscal_year, limit=10) -> list of {'name','amount','uei'} = top contract recipients by obligated $ for a NAICS code in a federal fiscal year (FY runs Oct 1 - Sep 30)
 sec_search(q, forms='10-K'), sec_facts(cik), federal_register(term, limit=20), fetch(url)
Today's date is {today}. "Last fiscal year" means the most recent COMPLETED federal fiscal year, which is FY{last_fy} (it has fully ended).
Keep API calls under 15. Never fabricate data: only use values returned by pubdata. End with pubdata.emit(result) where result is a JSON-serializable list of dicts.
Reply with only a ```python code block."""
MAX_TRIES = 3

def _system():
    d = datetime.date.today()
    last_fy = d.year if d.month >= 10 else d.year - 1  # FY N runs Oct 1 (N-1) .. Sep 30 N
    return SYSTEM.replace("{today}", d.isoformat()).replace("{last_fy}", str(last_fy))

def extract(text):
    """Pull the python script out of a model reply. Takes the longest fenced block; tolerates a missing closing fence."""
    blocks = re.findall(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len).strip()
    m = re.search(r"```(?:python|py)?[ \t]*\r?\n(.*)", text, re.S)  # unterminated fence
    return (m.group(1) if m else text).strip()

def run(question, on_event=lambda e: None):
    msgs = [{"role": "system", "content": _system()}, {"role": "user", "content": question}]
    steps = []
    for attempt in range(1, MAX_TRIES + 1):
        try:
            code = extract(llm.chat(msgs))
        except Exception as e:
            return {"question": question, "status": "failed", "steps": steps, "report": f"Model error: {e}", "receipts": []}
        on_event({"type": "code", "attempt": attempt, "code": code})
        t = time.time(); res = sandbox.run(code); res["seconds"] = round(time.time() - t, 2)
        steps.append({"attempt": attempt, "code": code, **res}); on_event({"type": "exec", **res})
        if "BLOCKED by sandbox policy" in res["stderr"] or res["timed_out"]:
            return {"question": question, "status": "contained", "steps": steps,
                    "report": "Containment triggered: the sandbox refused the action. Task environment destroyed.", "receipts": res["receipts"],
                    "blocked": res.get("blocked", [])}
        if res["exit_code"] == 0 and res["result"] is not None:
            msgs += [{"role": "assistant", "content": f"```python\n{code}\n```"},
                     {"role": "user", "content": f"SANDBOX RESULT (real, executed): {str(res['result'])[:6000]}\nSources: {[r['url'] for r in res['receipts']][:20]}\n"
                      "Write a concise markdown report answering the question. Cite sources as [n] referring to the source list order. Only state facts present in the result."}]
            return {"question": question, "status": "ok", "steps": steps, "result": res["result"],
                    "report": _safe_report(msgs, res), "receipts": res["receipts"], "blocked": res.get("blocked", [])}
        msgs += [{"role": "assistant", "content": f"```python\n{code}\n```"},
                 {"role": "user", "content": f"The script failed (exit {res['exit_code']}). stderr:\n{res['stderr'][-2000:]}\nFix it and reply with the full corrected script."}]
    return {"question": question, "status": "failed", "steps": steps, "report": "Gave up after retries.", "receipts": []}

def _safe_report(msgs, res):
    try:
        return llm.chat(msgs)
    except Exception as e:
        return f"(Report generation failed: {e}.) Raw verified result: {str(res['result'])[:2000]}"
