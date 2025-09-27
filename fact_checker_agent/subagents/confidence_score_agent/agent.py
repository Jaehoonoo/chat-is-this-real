from google.adk.agents import Agent
from pydantic import BaseModel

CONFIDENCE_SCORE_AGENT_INSTRUCTION = "

"

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="A helpful assistant for user questions.",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
)
