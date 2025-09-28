from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uuid
import asyncio
from google.adk.tools import ToolContext

CONFIDENCE_SCORE_AGENT_INSTRUCTION = """
    You are a professional agent whose job is to be the judge in a
    fact-checking system to combat misinformation. 

    The user of this system has come up with a request to fact-check a piece of
    information. Claims made by this piece of information were extracted by
    another agent, and then those claims were used to guide yet another agent
    an in-depth search for sources and evidence that are related to those
    claims (i.e. those sources either refute/support those claims). Yet another
    agent again did a credibility, bias, recency, and stance check on each of
    those sources.

    These are the source that we have:
    {sources_output}

    And this is the assessment of each source:
    {evaluator_results}

    Your task is to display to the user the get_evidence_score tool to display
    to the user the evidence score.
"""


def get_evidence_score(tool_context: ToolContext) -> dict:
    """
    Accepts as an argument just the tools context. Returns the evidence score.
    """

    evidence_score = 0
    sas = []

    # Corrected key "evaluator_results" and default value []
    source_assessments = tool_context.state.get("evaluator_results", [])

    # Where `sa` stands for "source assessment."
    for sa in source_assessments:
        d = sa["domain"]
        w = sa["recency_score"] * sa["credibility_score"]
        s = 1 if sa["stance"] == "supports" else -1 if sa["stance"] == "opposes" else 0
        sas.append({"domain": d, "weight": w, "stance": s})
        evidence_score += s * w

    tool_context.state["source_weights"] = sas
    return {
        "evidence_score": evidence_score
    }  # It's good practice for tools to return a dictionary


confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="""A professional agent whose job is to be the judge in a
    fact-checking system to combat misinformation.""",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score",
    tools=[get_evidence_score],
)

root_agent = confidence_score_agent
