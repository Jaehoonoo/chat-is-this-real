from google.adk.agents import LoopAgent, Agent, SequentialAgent

# Make sure these imports point to your actual project structure
from .subagents.analyst_agent.agent import analyst_agent
from .subagents.review_agent.agent import root_agent as review_agent
from typing import List
from pydantic import BaseModel, Field


class Claim(BaseModel):
    claim_text: str = Field(..., description="The detected claim text.")
    confidence: float = Field(
        ...,
        description="A confidence score for the claim's validity, represented as a float between 0 and 1 to 2 decimal places.",
    )
    bias_score: str = Field(
        ...,
        description="A bias score for the claim's source, represented as a string from left, lean left, neutral, lean right, and right.",
    )
    justification: str = Field(
        ...,
        description="A detailed explanation or reasoning that supports the validity, confidence, and bias scores.",
    )
    sources: List[str] = Field(
        ...,
        description="A list of sources that are USED to JUDGE OR VERIFY the claim. This shall NEVER be the original claim's sources.",
    )


class ClaimsOutput(BaseModel):
    claims: List[Claim] = Field(..., description="A list of all claims detected.")


# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
MAX_ITERATIONS = 2

# --- Fact Checking Loop ---
fact_checker_loop = LoopAgent(
    name="FactCheckingLoop",
    sub_agents=[
        analyst_agent,  # evaluates sources and updates STATE_EVALUATED_SOURCES
        review_agent,  # reviews and refines the original claim if needed
    ],
    max_iterations=MAX_ITERATIONS,
    description="Loop that repeatedly analyzes evidence, reviews, and increases confidence until threshold is met.",
)


SYNTHESIS_AGENT_PROMPT = """
You are a synthesis agent. Your sole task is to combine multiple pieces of evidence and the scores given by the analyst agent into a coherent final report. You must evaluate each claim and:

- assign a "confidence_score" between 0 and 1, where 1 means you are absolutely certain the claim is true, and 0 means you are absolutely certain the claim is false.
- assign a "bias_score" between left, lean left, neutral, lean right, and right, where left means the claim is extremely left-leaning, and right means the claim is extremely right-leaning.
- provide a brief "justification" (1-2 sentences) explaining your reasoning for the
- cite sources used for your judgement from the provided list of sources. You should NOT use the original claim's sources.

## List of claims
The claims you are to verify is listed in a JSON array as follows: {claims}

## List of sources
The sources you are to use to verify the claims is listed in a JSON array as follows: {evidence_packets}

## Analyst comments
The comments left by the Final Adjudicator, if any, are as follows: {final_report}
"""

synthesis_agent = Agent(
    name="synthesis_agent",
    model=GEMINI_MODEL,
    instruction=SYNTHESIS_AGENT_PROMPT,
    output_key="synthesis_report",
    output_schema=ClaimsOutput,  # pass into ui
)

root_agent = SequentialAgent(
    name="FactCheckerRootAgent",
    sub_agents=[
        fact_checker_loop,
        synthesis_agent,
    ],
)
