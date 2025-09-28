from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field
from typing import List
from typing import Literal


class SourceProfile(BaseModel):
    """Represents a single source with its analysis."""

    source_url: str = Field(..., description="The URL of the source.")
    retrieved_quote: str = Field(
        ..., description="A key quote or summary from the source."
    )
    retrieving_agent: Literal[
        "Supporting Researcher", "Refuting Researcher", "Contextual Researcher"
    ] = Field(..., description="The agent that retrieved this source.")
    credibility_rating: Literal["Very High", "High", "Mixed", "Low", "Very Low"] = (
        Field(..., description="The credibility of the source.")
    )
    bias_rating: Literal[
        "Left", "Leans Left", "Center", "Leans Right", "Right", "N/A"
    ] = Field(..., description="The bias of the source.")


class SourceProfilerOutput(BaseModel):
    """The final output schema for the entire list of sources."""

    source_profiles: List[SourceProfile] = Field(
        ..., description="An array of all analyzed sources."
    )


# --------------------------------------------------------------------------
## 2. Two-Agent Definitions
# --------------------------------------------------------------------------


# MAKE SURE PARALLEL TEAM CALLS THIS AGENT NEXT AND TO FILL PROMPT WITH PROPER OUTPUT_KEY


### --- Agent 1: Raw Data Researcher (Uses Tools) ---
RAW_RESEARCHER_PROMPT = """
You are a research assistant. Your mission is to use the google_search tool to find the source's credibility rating and potential bias in the entire list.

#### Your Workflow:
1.  **Strategize**: Extract the domain and formulate 1-2 targeted search queries to investigate its reputation (e.g., `"domain" media bias`, `"domain" ownership`).
2.  **Parallel Research**: You **MUST** call the `Google Search` tool for all your queries **at the same time (in parallel)**.
3. Output: Compile the analysis of all sources into a single, raw JSON array. Each object in the array must contain two keys: "source" (the name/domain of the source) and "summary" (a **one sentence** factual summary of the source's content). Do not include any other text, explanation, or conversational filler. Your output must be a parsable JSON array and nothing else.

Example Output:
[{source: 'somedomain.xyz', "research_summary": "AllSides rates the source as 'Center'. Media Bias/Fact Check notes 'High' factual reporting and that it is owned by The Example Corporation."},{"source": 'anotherdomain.xyz', "research_summary": "AllSides rates the source as 'Center'. Media Bias/Fact Check notes 'High' factual reporting and that it is owned by The Example Corporation."}]

Your list of source are:
{sources_output}
"""

raw_researcher_agent = Agent(
    name="raw_researcher_agent",
    model="gemini-2.0-flash",
    instruction=RAW_RESEARCHER_PROMPT,
    tools=[google_search],
    output_key="raw_research_data",  # Key for passing the raw JSON to the next agent
)

### --- Agent 2: Formatting Analyst (Uses Pydantic Schema) ---
FORMATTER_PROMPT = """
You are a senior intelligence analyst. Your job is to take the raw research summary below and synthesize it into a structured, final report.

#### Your Workflow:
1.  **Analyze**: Carefully read the `research_summary` from the raw data provided below.
2.  **Synthesize**: Based on the summary, determine the final ratings for credibility, bias, factual reporting, and ownership.
3.  **Structure**: Set the `profiler_method` to "Real-Time Research" and use the `notes` field to summarize the key evidence.
4.  **Format**: Ensure your final output is a single, valid JSON object that perfectly matches the `SourceProfilerOutput` schema.

Raw Data:
{raw_research_data}
"""

formatting_analyst_agent = Agent(
    name="formatting_analyst_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT,
    output_schema=SourceProfilerOutput,  # Enforces the final structure
    output_key="evidence_packets",
)

# --------------------------------------------------------------------------
## 3. The SequentialAgent Workflow
# --------------------------------------------------------------------------

research_workflow = SequentialAgent(
    name="research_profiling_workflow",
    sub_agents=[
        raw_researcher_agent,
        formatting_analyst_agent,
    ],
)

root_agent = research_workflow
