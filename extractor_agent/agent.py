from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from pydantic import BaseModel, Field
import sys

sys.path.append("../")
from prompt import (
    EXTRACTOR_AGENT_PROMPT,
    MISLEADING_CLAIMS_EXTRACTION_INSTRUCTION,
)
from article_reader import extract_article

import dotenv

dotenv.load_dotenv()


# Define the schema for your extractor agent's output
class ExtractedClaims(BaseModel):
    """A data model for a list of claims extracted from text."""

    claims: list[str] = Field(
        description="A list of claims found in the input text. Each claim is a string.",
    )


root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="root_agent",
    description="A helpful assistant for user questions.",
    instruction=MISLEADING_CLAIMS_EXTRACTION_INSTRUCTION,
    output_schema=ExtractedClaims,
    output_key="claims",
)


if __name__ == "__main__":
    APP_NAME = "extractor_agent_app"
    USER_ID = "user_123"
    SESSION_ID = "session_123"

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    runner = Runner(
        agent=root_agent, app_name=APP_NAME, session_service=session_service
    )

    url = "https://www.foxnews.com/politics/obama-center-deposits-just-1m-into-470m-reserve-fund-aimed-to-protect-taxpayers-fueling-new-criticism"
    # url = "https://www.whitehouse.gov/articles/2025/09/fact-evidence-suggests-link-between-acetaminophen-autism/"

    summary, full_text = extract_article(url)
    print("Article Summary:", summary)
    print("Full Article Text:", full_text)

    content = types.Content(role="user", parts=[types.Part(text=full_text)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text.strip()
            print("\n🟢 FINAL ANSWER\n", final_answer, "\n")
