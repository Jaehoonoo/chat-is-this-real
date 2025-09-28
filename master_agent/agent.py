from google.adk.agents import SequentialAgent

# from google.adk.tools import google_search

from pydantic import BaseModel, Field
import sys

sys.path.append("../")

from extractor_agent.agent import root_agent as fetcher_agent
from fact_checker_agent.agent import root_agent as fact_checker_agent
from retrieval_agent.agent import root_agent as retrieval_agent

import dotenv

dotenv.load_dotenv()

root_agent = SequentialAgent(
    name="RootAgent",
    sub_agents=[
        fetcher_agent,
        retrieval_agent,
        fact_checker_agent, # i think delete this
    ],
)
