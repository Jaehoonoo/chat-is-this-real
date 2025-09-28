# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Any, Dict

# Import your ADK agent (must expose `root_agent` or your "master_agent")
# e.g., master_agent/agent.py defines `root_agent`
from master_agent.agent import root_agent  # adjust to your package

api = FastAPI(title="Master Agent API")

class AnalyzeLinkIn(BaseModel):
    url: HttpUrl  # validates well-formed news URL

@api.get("/")
def health() -> Dict[str, str]:
    return {"ok": "true"}  # health check / quick GET sanity

@api.post("/")
def analyze_link(body: AnalyzeLinkIn) -> Dict[str, Any]:
    try:
        # Forward a simple payload; adjust the key if your agent expects a different shape
        result = root_agent({"url": str(body.url)})
        # Ensure the result is JSON-serializable; wrap if needed
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
