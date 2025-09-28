"""Sources Agent (sequential)
Step 1: Find up to 15 reputable URLs for <= 5 claims (with google_search).
Step 2: Format them into {"sources":[{"url","outlet","why_reliable"}]}.
"""

from typing import List
from pydantic import BaseModel, Field
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search

from retrieval_agent.prompt import FORMATTER_PROMPT, QUERY_AGENT_PROMPT

# -------------------------------------------------------------------
# Output schema
# -------------------------------------------------------------------


class SourceItem(BaseModel):
    domain: str
    article_text: str
    published_date: str


class SourcesOutput(BaseModel):
    # NOTE: named "sources" per request
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="Up to 15 diverse, reputable sources across all claims.",
    )


# Assume SourcesOutput is already defined as in your previous prompt

# The agents you already have
positive_query_agent = Agent(
    name="positive_query_agent",
    model="gemini-2.0-flash",
    instruction="You are an expert at generating **positive** search queries to find reputable sources that support a given claim. Create 5 CONCISE search queries that yield high-quality sources that **CORROBORATE** claims.",
    output_key="pos_q",
)

negative_query_agent = Agent(
    name="negative_query_agent",
    model="gemini-2.0-flash",
    instruction="You are an expert at generating **negative** search queries to find reputable sources that refute a given claim. Create 5 CONCISE search queries that yield high-quality sources that **DISPROVE** claims.",
    output_key="neg_q",
)

positive_search_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    instruction=QUERY_AGENT_PROMPT + "{pos_q}",
    tools=[google_search],
    output_key="positive_search_results",
)

negative_search_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    instruction=QUERY_AGENT_PROMPT + "{neg_q}",
    tools=[google_search],
    output_key="negative_search_results",
)

pos_agent = SequentialAgent(
    name="positive_search_agent",
    sub_agents=[positive_query_agent, positive_search_agent],
)

neg_agent = SequentialAgent(
    name="negative_search_agent",
    sub_agents=[negative_query_agent, negative_search_agent],
)

formatter_agent = Agent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT
    + " ### Positive Query Results\n {positive_search_results}  \n"
    + "### Negative Query Results\n{negative_search_results}",
    output_schema=SourcesOutput,
    output_key="sources_output",
)

# Step 1: Create a ParallelAgent to generate both sets of queries at once.
parallel_search_agent = ParallelAgent(
    name="query_generator_agent",
    description="Generates both positive and negative search queries in parallel.",
    sub_agents=[pos_agent, neg_agent],
)

# Step 2: Combine all agents into a single SequentialAgent
# This agent takes the output from the previous step and passes it to the next
# in a sequential flow.
full_analysis_agent = SequentialAgent(
    name="full_analysis_agent",
    description="A complete pipeline for generating opposing views and compiling them into a final report.",
    sub_agents=[
        parallel_search_agent,
        formatter_agent,
    ],
)

# Required by ADK CLI
root_agent = full_analysis_agent
