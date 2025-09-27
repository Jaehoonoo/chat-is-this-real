from google.adk.agents import Agent
from pydantic import BaseModel

"""
{
    "domain": "example.com",
    "credibility_score": 0.81,
    "bias_label": "-0.63",
    "recency_score": 1.01,
    "stance": "supports",
    "reasoning": "The domain is generally reliable, the article aligns with the claim(s), and it was published recently."
  }
"""
class ConfidenceScoreOutput(BaseModel):
    confidence_score: float = Field(
        description = "A number ranging from 0 to 1 indicating the confidence, where 0 is lowest confidence, and 1 is highest confidence"
    )
    citations: str = Field(
        description = ""
    )
    explanation: str = Field(
        description = ""
    )

CONFIDENCE_SCORE_AGENT_INSTRUCTION = ""

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="A helpful assistant for user questions.",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
    output_schema=ConfidenceScoreOutput
)
