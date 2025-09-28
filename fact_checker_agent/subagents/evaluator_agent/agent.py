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

    domain: str = Field(
        ..., description="The domain of the source, e.g., 'example.com'."
    )
    credibility_score: float = Field(
        ..., description="Credibility score from the get_source_analytics tool."
    )
    bias_label: float = Field(
        ..., description="Bias score from the get_source_analytics tool."
    )
    recency_score: float = Field(
        ..., description="Recency score from the recency_score tool."
    )
    stance: Stance = Field(
        ..., description="The stance of the article towards the original claim."
    )


class EvaluatorOutput(RootModel):
    """A Pydantic RootModel representing a list of evaluations."""

    root: List[SourceEvaluation]


# --------------------------------------------------------------------------
## 3. Agent Definitions
# --------------------------------------------------------------------------

# Agent A: Gathers raw data using tools
RAW_OUTPUT_PROMPT = """
You are an expert fact-checker and source analyst. Your task is to evaluate a given list of sources and their associated claims based on several key metrics.

#### Your Workflow and Directives

1.  **Input Analysis**: You will be provided with a JSON array, where each object contains a `domain` and an `original_claim` to be evaluated.
2.  **Tool Execution**: For each entry in the input array, you **must** perform two actions:
    * Call the `get_source_analytics` tool with the `domain` to retrieve its `credibility_score` and `bias_label`.
    * Call the `recency_score` tool with the `original_claim` to determine how recent the information is.
3.  **Stance and Synthesis**: Based on the `original_claim` and the article content, analyze and determine the `stance` of the source ("supports", "opposes", "neutral").
4.  **Educated Guessing**: If any of the required data points (`credibility_score`, `bias_label`, `recency_score`, or `stance`) cannot be determined from the tool outputs or the article content, you **MUST** make an educated guess based on your extensive knowledge of journalism and media.
5.  **Final Output**: Compile all the collected and synthesized information for each source into a **single, valid JSON array string**. Each object in the array **must** contain the following keys: `domain`, `credibility_score`, `bias_label`, `recency_score`, and `stance`. Do not include any other text, explanation, or conversational filler in your final output. Your output must be a parsable JSON string and nothing else.
"""

raw_output_agent = Agent(
    name="raw_output_agent",
    model="gemini-2.0-flash",
    instruction=RAW_OUTPUT_PROMPT + "Your input source list is: {sources_output}",
    tools=[get_source_analytics, recency_score],
    output_key="raw_json_input",
)

# Agent B: Formats the raw data into the Pydantic schema
FORMATTER_PROMPT = """
You are a data formatting expert. Your ONLY job is to take the raw JSON string below and reformat it to perfectly match the required schema. Do not change any of the data's values.

Raw JSON Input: {raw_json_input}
"""

formatting_agent = Agent(
    name="formatting_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT,
    output_schema=EvaluatorOutput,
    output_key="evaluator_results",
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
