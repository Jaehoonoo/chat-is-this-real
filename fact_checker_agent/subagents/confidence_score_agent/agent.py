from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uuid
import asyncio

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
    with regards to how confident you are.""",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
)

# Executes required runner logic for unit test of conf score agnt.
async def main():
    session_service_stateful = InMemorySessionService()

    initial_state = {
        "sources": "hi how are u",
        "evaluator_result": "whats going on"
    }

    APP_NAME = "Conf Score Agnt"
    USER_ID = "kalyanolivera"
    SESSION_ID = str(uuid.uuid4())
    stateful_session = await session_service_stateful.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initial_state
    )

    runner = Runner(
        agent=confidence_score_agent,
        app_name=APP_NAME,
        session_service=session_service_stateful
    )

    nm = types.Content(
        role="user", parts = [types.Part(text="do the tasks that you are made to do")]
    )

    # Where `e` stands for "event."
    for e in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=nm
    ):
            if e.is_final_response() and e.content and e.content.parts:
                print(
                    f"Final response: {e.content.parts[0].text}"
                )

if __name__ == "__main__":
    asyncio.run(main())
