from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from . import agent
app = FastAPI(title="Public Records Research Agent")
HISTORY = []
class Ask(BaseModel):
    question: str
@app.post("/api/ask")
def ask(a: Ask):
    out = agent.run(a.question[:1000]); HISTORY.insert(0, out); del HISTORY[20:]; return out
@app.get("/api/history")
def history(): return HISTORY
@app.get("/healthz")
def health(): return {"ok": True, "sandbox": os.environ.get("SANDBOX_MODE", "local"), "llm": os.environ.get("LLM_PROVIDER", "openai")}
@app.get("/")
def index(): return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
