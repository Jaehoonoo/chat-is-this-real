from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# from google.adk.tools import google_search

from pydantic import BaseModel, Field
import sys
import re

sys.path.append("../")
from extractor_agent.prompt import MULTIMODAL_AGENT_PROMPT
from extractor_agent.article_reader import article_read_tool
from fact_checker_agent.agent import root_agent as fact_checker_agent
from retrieval_agent.agent import root_agent as retrieval_agent

import dotenv
import tweepy
import os

dotenv.load_dotenv()


class ExtractedClaims(BaseModel):
    """A data model for a list of claims extracted from text."""

    claims: list[str] = Field(
        description="A list of claims found in the input text. Each claim is a string.",
    )


def x_post_fetcher_tool(url: str):
    # We use this as a simple tool, not multimodal, for the SequentialAgent to pass text
    match = re.search(r"status/(\d+)", url)
    post_id = None
    if match:
        post_id = match.group(1)
    else:
        raise ValueError("Invalid X URL provided.")

    bearer_token = os.environ.get("X_BEARER_TOKEN")
    if not bearer_token:
        raise EnvironmentError("X_BEARER_TOKEN not found in environment variables.")

    client = tweepy.Client(bearer_token)
    post_data = {}
    try:
        response = client.get_tweet(
            id=post_id,
            tweet_fields=["text"],
            expansions=["attachments.media_keys"],
            media_fields=["url"],
        )

        post_data = {"text": None, "media_urls": []}

        if response.data:
            post_data["text"] = response.data["text"]

        if "media" in response.includes:
            for media in response.includes["media"]:
                if "url" in media:
                    post_data["media_urls"].append(media["url"])

    except Exception as e:
        return {"status": "error", "error": f"An error occurred: {e}"}

    if "error" in post_data:
        return {
            "status": "error",
        }

    content_parts = []
    return {
        "status": "success",
        "content": post_data,
    }


fetcher_agent = Agent(
    model="gemini-2.0-flash",
    name="FetcherAgent",
    description="An agent that fetches content from a URL, using the appropriate tool for a news article or social media post.",
    instruction=" If the URL is from X (formerly Twitter), use the `x_post_fetcher` tool. If the URL is from an authoritative source (news agent, governmental agencies), use the `article_reader` tool. Do not make any assumptions about the content of the URL; always use the tools provided.\n\nOutput only the fetched content verbatim, without any additional commentary or explanation.",
    tools=[article_read_tool, x_post_fetcher_tool],
    output_key="fetched_content",  # Saves the raw text here
)

multimodal_reasoning_agent = Agent(
    model="gemini-2.0-flash",
    name="multimodal_reasoning_agent",
    description="A helpful assistant for reasoning about images and text in the context of an article.",
    instruction=MULTIMODAL_AGENT_PROMPT + "Extract claims from {fetched_content}.",
    output_schema=ExtractedClaims,
    output_key="claims",
)

root_agent = SequentialAgent(
    name="RootAgent",
    sub_agents=[
        fetcher_agent,
        multimodal_reasoning_agent,
    ],
    # output_schema=ExtractedClaims,
)

# Main execution block
if __name__ == "__main__":
    url = "https://x.com/DerrickEvans4WV/status/1971903502151770580"
    APP_NAME = "extractor_agent_app"
    USER_ID = "user_123"
    SESSION_ID = "session_123"

    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    # url = "https://www.whitehouse.gov/articles/2025/09/fact-evidence-suggests-link-between-acetaminophen-autism/"
    # Example social media URL
    # url = "https://x.com/GavinNewsom/status/1971770007559495899"
    # url = "https://x.com/DerrickEvans4WV/status/1971903502151770580"

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Example user request with a URL
    user_msg = types.Content(
        role="user",
        parts=[
            types.Part(
                text="Find and extract misleading claims from the post at this URL: https://x.com/DerrickEvans4WV/status/1971903502151770580"
            )
        ],
    )

    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=user_msg)

    for event in events:
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text.strip()
            print(final_answer)
