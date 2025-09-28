from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field
from typing import Literal

# --------------------------------------------------------------------------
## 1. Pydantic Schemas (Unchanged)
# --------------------------------------------------------------------------

class SourceProfilerInput(BaseModel):
    source_url: str = Field(..., description="The full URL of the source to be profiled.")

class SourceProfilerOutput(BaseModel):
    source_url: str
    retrieved_quote: str
    retrieving_agent: Literal["Supporting Researcher", "Refuting Researcher", "Contextual Researcher"]
    credibility_rating: Literal["Very High", "High", "Mixed", "Low", "Very Low"]
    bias_rating: Literal["Left", "Leans Left", "Center", "Leans Right", "Right", "N/A"]

# --------------------------------------------------------------------------
## 2. Two-Agent Definitions
# --------------------------------------------------------------------------

### --- Agent 1: Raw Data Researcher (Uses Tools) ---
RAW_RESEARCHER_PROMPT = """
You are a research assistant. Your mission is to use the google_search tool to find intelligence(credibility rating and bias rating) on a given media source.

#### Your Workflow:
1.  **Strategize**: Extract the domain from the provided `source_url` and formulate 1-2 targeted search queries to investigate its reputation (e.g., `"domain" media bias`, `"domain" ownership`).
2.  **Parallel Research**: You **MUST** call the `Google Search` tool for all your queries **at the same time (in parallel)**.
3.  **Output**: Your final output must be a single, raw JSON object with one key, "research_summary", containing your text summary. Do not add any other text or explanation.

Example Output:
{{"research_summary": "AllSides rates the source as 'Center'. Media Bias/Fact Check notes 'High' factual reporting and that it is owned by The Example Corporation."}}
"""

raw_researcher_agent = Agent(
    name="raw_researcher_agent",
    model="gemini-2.0-flash",
    instruction=RAW_RESEARCHER_PROMPT,
    tools=[google_search],
    input_schema=SourceProfilerInput,
    output_key="raw_research_data"  # Key for passing the raw JSON to the next agent
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
    output_key="final_profile"
)

# --------------------------------------------------------------------------
## 3. The SequentialAgent Workflow
# --------------------------------------------------------------------------

research_workflow = SequentialAgent(
    name="research_profiling_workflow",
    sub_agents=[
        raw_researcher_agent,
        formatting_analyst_agent,
    ]
)

root_agent = research_workflow