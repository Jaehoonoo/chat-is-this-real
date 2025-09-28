# your_main_file.py

from fastapi import FastAPI
from pydantic import BaseModel
import sys

# Your existing imports for the multi-agent system
sys.path.append("../")
from extractor_agent.agent import root_agent as fetcher_agent
from fact_checker_agent.agent import root_agent as fact_checker_agent
from retrieval_agent.agent import root_agent as retrieval_agent
import dotenv
dotenv.load_dotenv()

# ADK imports for running the agent programmatically
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import SequentialAgent
from google.adk.types import Content, Part

# Pydantic model for the API request body
class LinkInput(BaseModel):
    url: str

# ---------------------------------------------
# 1. Define your multi-agent system
# ---------------------------------------------
root_agent = SequentialAgent(
    name="RootAgent",
    sub_agents=[
        fetcher_agent,
        retrieval_agent,
        # fact_checker_agent, # As per your comment, you might remove this
    ],
)

# ---------------------------------------------
# 2. Define the API server
# ---------------------------------------------
api_app = FastAPI(title="Multi-Agent Pipeline API")
session_service = InMemorySessionService()

# Define the new API endpoint
@api_app.post("/analyze_link")
async def analyze_link(link_input: LinkInput):
    """
    Kicks off the multi-agent pipeline with a URL as input.
    """
    user_url = link_input.url

    # Create a runner for your root agent
    runner = Runner(agent=root_agent, session_service=session_service)
    
    # You need a user_id and session_id to run the agent
    user_id = "api_user"  # or generate a unique ID
    session_id = "session_for_link_analysis"  # or generate a unique ID

    # Create a message content for the agent to process
    # This is the crucial step: passing the URL to the agent's input stream
    agent_message = Content.from_parts([Part.from_text(user_url)])

    try:
        # Run the agent with the provided URL
        # The runner will start the sequential agent, which in turn
        # passes the initial message to the first sub-agent (fetcher_agent)
        response_stream = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=agent_message
        )

        # The runner returns an async generator. We need to collect the final response.
        final_response = None
        async for event in response_stream:
            # The final response is what the last agent in the sequence returns
            if event.is_final_response():
                final_response = event.content.text
        
        # You will need to parse the text response to get the score
        # For example, if your fact_checker_agent returns a JSON string, you would parse it here.
        
        if final_response:
            return {"result": final_response}
        else:
            return {"error": "Pipeline did not produce a final response."}, 500

    except Exception as e:
        return {"error": f"An error occurred: {e}"}, 500