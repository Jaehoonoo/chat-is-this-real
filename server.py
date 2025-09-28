# server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Any, Dict
import uuid

# --- USE THE MODULE THAT WORKS FOR YOU ---
from google.genai.types import Content, Part
# If the above still fails, try: from google.generativeai.types import Content, Part

# ADK imports for running the agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import your ADK agent (must expose `root_agent`)
from master_agent.agent import root_agent

api = FastAPI(title="Master Agent API")

class AnalyzeLinkIn(BaseModel):
    url: HttpUrl

# --- ADK Setup ---
session_service = InMemorySessionService()
agent_runner = Runner(
    agent=root_agent, 
    session_service=session_service,
    app_name="your-link-analyzer"
)

@api.get("/")
def health() -> Dict[str, str]:
    return {"ok": "true"}

@api.post("/analyze_link")
async def analyze_link(body: AnalyzeLinkIn) -> Dict[str, Any]:
    """
    Kicks off the multi-agent pipeline with a URL as input.
    """
    session_id = str(uuid.uuid4())
    user_id = "api_user"

    # The line that caused the error previously
    agent_message = Content(parts=[Part.from_text(str(body.url))])

    try:
        response_stream = agent_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=agent_message
        )

        final_response_text = None
        async for event in response_stream:
            if event.is_final_response():
                final_response_text = event.content.text
                break
        
        if final_response_text:
            return {"result": final_response_text}
        else:
            return {"error": "Pipeline did not produce a final response."}, 500

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {e}")