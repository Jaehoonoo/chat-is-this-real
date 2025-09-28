from google.adk.agents import Agent, SequentialAgent
from pydantic import BaseModel, RootModel, Field
from typing import List, Literal, Dict
from .data import SOURCE_ANALYTICS_DB

# --------------------------------------------------------------------------
## 1. Tools
# --------------------------------------------------------------------------

# --- MODIFIED ---
# This function now queries the real SOURCE_ANALYTICS_DB.
def get_source_analytics(domain: str) -> Dict:
    """
    Retrieves credibility and bias scores for a given domain from the database.
    """
    # Normalize the domain for a more reliable lookup (e.g., "www.cnn.com" -> "cnn.com")
    clean_domain = domain.lower().strip().replace("www.", "")

    # Provide a neutral default value if the domain is not found in the database
    default_scores = {"credibility_score": 0.5, "bias_label": 0.0}
    analytics = SOURCE_ANALYTICS_DB.get(clean_domain, default_scores)

    print(f"TOOL CALLED: get_source_analytics('{domain}') -> {analytics}")
    return analytics

def recency_score(published_date: str) -> float:
    """Returns a dummy recency score for a given date."""
    print(f"TOOL CALLED: recency_score(published_date='{published_date}')")
    return 1.0

# --------------------------------------------------------------------------
## 2. Pydantic Schemas for Output Validation
# --------------------------------------------------------------------------

Stance = Literal["supports", "opposes", "neutral"]

class SourceEvaluation(BaseModel):
    """A Pydantic model for a single evaluated source."""
    domain: str = Field(..., description="The domain of the source, e.g., 'example.com'.")
    credibility_score: float = Field(..., description="Credibility score from the get_source_analytics tool.")
    bias_label: float = Field(..., description="Bias score from the get_source_analytics tool.")
    recency_score: float = Field(..., description="Recency score from the recency_score tool.")
    stance: Stance = Field(..., description="The stance of the article towards the original claim.")

class EvaluatorOutput(RootModel):
    """A Pydantic RootModel representing a list of evaluations."""
    root: List[SourceEvaluation]

# --------------------------------------------------------------------------
## 3. Agent Definitions
# --------------------------------------------------------------------------

# Agent A: Gathers raw data using tools
RAW_OUTPUT_PROMPT = """
You are a fact-checking assistant. Your task is to process a list of sources.

# Your Strict Workflow
1. For each source, you MUST call the `get_source_analytics` and `recency_score` tools.
2. After calling all tools, analyze the stance for each source.
3. Finally, compile all the collected information (domain, credibility_score, bias_label, recency_score, stance) into a single, valid JSON array string. This is your only output. Do not add any other text.
4. (optional) if you cannot determine the collected information from data do your best to make an educated guess.
"""

raw_output_agent = Agent(
    name="raw_output_agent",
    model="gemini-2.0-flash",
    instruction=RAW_OUTPUT_PROMPT,
    tools=[get_source_analytics, recency_score],
    output_key="raw_json_input"
)

# Agent B: Formats the raw data into the Pydantic schema
FORMATTER_PROMPT = """
You are a data formatting expert. Your ONLY job is to take the raw JSON string below and reformat it to perfectly match the required schema. Do not change any of the data's values.

Raw JSON Input:
{{ raw_json_input }}
"""

formatting_agent = Agent(
    name="formatting_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT,
    output_schema=EvaluatorOutput,
    output_key="evaluator_results"
)

# --------------------------------------------------------------------------
## 4. The SequentialAgent Workflow
# --------------------------------------------------------------------------

# --- CORRECTED ---
# The `SequentialAgent` requires the 'agents' parameter, not 'sub_agents'.
evaluator_agent = SequentialAgent(
    name="fact_checking_workflow",
    sub_agents=[
        raw_output_agent,
        formatting_agent,
    ],
)

root_agent = evaluator_agent