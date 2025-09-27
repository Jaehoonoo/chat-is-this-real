from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search

from pydantic import BaseModel, Field
import sys
import re

sys.path.append("../")
from prompt import MISLEADING_CLAIMS_EXTRACTION_INSTRUCTION, MULTIMODAL_AGENT_PROMPT
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

multimodal_reasoning_agent = Agent(
    model="gemini-2.0-flash-001",
    name="multimodal_reasoning_agent",
    description="A helpful assistant for reasoning about images and text in the context of an article.",
    instruction=MULTIMODAL_AGENT_PROMPT,
    # output_schema=ExtractedClaims,
    output_key="claims",
    tools=[google_search],
)


# Main execution block
if __name__ == "__main__":
    APP_NAME = "extractor_agent_app"
    USER_ID = "user_123"
    SESSION_ID = "session_123"

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    # Define the URL here. This would come from your user input.
    # url = "https://www.foxnews.com/politics/obama-center-deposits-just-1m-into-470m-reserve-fund-aimed-to-protect-taxpayers-fueling-new-criticism"
    # url = "https://www.whitehouse.gov/articles/2025/09/fact-evidence-suggests-link-between-acetaminophen-autism/"
    # Example social media URL
    # url = "https://x.com/GavinNewsom/status/1971770007559495899"
    url = "https://x.com/DerrickEvans4WV/status/1971903502151770580"

    # Conditional logic to choose the agent
    if re.search(r"(x.com|facebook.com)", url):
        url = re.sub(r"x.com", f"xcancel.com", url)
        print(url)
        # Use the multimodal agent for social media content
        runner = Runner(
            agent=multimodal_reasoning_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )
        print("Using Multimodal Agent for social media post...")
        # For multimodal, you might pass the URL directly to the agent's tool
        # In this simplified example, we'll just pass a placeholder message
        content = types.Content(
            role="user", parts=[types.Part(text=f"Analyze the post at {url}")]
        )
    else:
        # Use the standard article-reader agent for a typical news article
        runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=session_service
        )
        print("Using Root Agent for news article...")
        summary, full_text = extract_article(url)
        print("Article Summary:", summary)
        print("Full Article Text:", full_text)
        content = types.Content(role="user", parts=[types.Part(text=full_text)])

    # Run the agent with the appropriate content
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text.strip()
            print(final_answer)
