from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
import uuid

CONFIDENCE_SCORE_AGENT_INSTRUCTION = """
    These are the source that we have:
    {sources}
    And this is the assessment of each source:
    {evaluator_result}
    Tell the user what the sources are, and what the assessment is
"""

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="""You are an agent responsible for giving a confidence score
    with regards to how confident you are."""
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
)

# Executes required runner logic for unit test of conf score agnt.
if __name__ == "__main__":
    session_service_stateful = InMemorySessionService()

    initial_state = {
        "sources": "hi how are u",
        "evaluator_result": "whats going on"
    }

