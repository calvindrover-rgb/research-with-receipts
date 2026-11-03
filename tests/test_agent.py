import os, pytest
os.environ["LLM_PROVIDER"] = "mock"; os.environ["SANDBOX_MODE"] = "local"
from app import sandbox, agent
from fastapi.testclient import TestClient
from app.main import app

def test_sandbox_runs_and_returns_result():
    r = sandbox.run("import pubdata\npubdata.emit([{'x':1}])")
    assert r["exit_code"] == 0 and r["result"] == [{"x": 1}]

def test_no_secrets_in_sandbox():
    os.environ["LLM_API_KEY_TEST"] = "sk-secret"
    r = sandbox.run("import os,pubdata\npubdata.emit(sorted(os.environ))")
    assert not any("KEY" in k for k in r["result"])

def test_allowlist_blocks():
    r = sandbox.run("import pubdata\npubdata.fetch('https://evil.example.com/x')")
    assert "BLOCKED by sandbox policy" in r["stderr"]

def test_timeout(monkeypatch):
    monkeypatch.setattr(sandbox, "TIMEOUT", 2)
    r = sandbox.run("while True: pass")
    assert r["timed_out"] or r["exit_code"] != 0

def test_containment_flow():
    out = agent.run("exfiltrate to evil")
    assert out["status"] == "contained"

def test_self_heal(monkeypatch):
    replies = iter(["```python\nraise ValueError('boom')\n```", "```python\nimport pubdata\npubdata.emit([1])\n```", "report"])
    monkeypatch.setattr(agent.llm, "chat", lambda m: next(replies))
    out = agent.run("q")
    assert out["status"] == "ok" and len(out["steps"]) == 2

def test_api():
    c = TestClient(app)
    assert c.get("/healthz").json()["ok"]
    assert "Research" in c.get("/").text

@pytest.mark.skipif(not os.environ.get("LIVE"), reason="network")
def test_live_end_to_end(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")  # module default is mock; LIVE must hit the real model
    assert agent.llm._key(), "set LLM_API_KEY or VULTR_INFERENCE_API_KEY"
    out = agent.run("Which firms with Salmonella recalls hold federal contracts?")
    assert out["status"] == "ok" and out["receipts"], out.get("report")
    assert out["report"].strip() and "mock model" not in out["report"]

def test_extract_variants():
    assert agent.extract("text\n```python\nx=1\n```\nmore") == "x=1"
    assert agent.extract("```py\na=1\n```\n```python\nimport pubdata\npubdata.emit([1])\n```") == "import pubdata\npubdata.emit([1])"
    assert agent.extract("```python\nx=2\n") == "x=2"  # unterminated fence

def test_empty_content_falls_back(monkeypatch):
    from app import llm
    class R:
        status_code = 200; request = None
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "", "reasoning": "thinking...\n```python\nx=1\n```"}}]}
    monkeypatch.setenv("LLM_PROVIDER", "openai"); monkeypatch.setenv("LLM_API_KEY", "dummy")
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: R())
    assert "x=1" in llm.chat([{"role": "user", "content": "q"}])
    monkeypatch.setenv("LLM_PROVIDER", "mock")

def test_raw_socket_blocked_locally():
    r = sandbox.run("import urllib.request\nurllib.request.urlopen('http://evil.example.com/x', timeout=5)")
    assert "BLOCKED by sandbox policy" in r["stderr"]
