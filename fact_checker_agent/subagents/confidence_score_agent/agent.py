from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uuid
import asyncio
from google.adk.tools import ToolContext
from collections import defaultdict
import math

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
    {sources}

    And this is the assessment of each source:
    {evaluator_result}

    Your task is to use the get_evidence_score tool to display to the user the
    evidence score. If the value is higher than 0.25, then you must tell the
    user that the original claims are supported by the sources/evidence found.
    If evidence score is less than -0.25, then you must tell the user that the
    original claims are not supported by the sources/evidence found.

    You must also display the result of the get_confidence_score to the user.
    Make sure you call the get_confidence_score after the get_evidence_score.

    Include in your final response both the result of the get_confidence_score
    tool and the get_evidence_score tool. You must include both results.
"""

def get_evidence_score(tool_context: ToolContext) -> dict:
    """
    Calculates a weighted evidence score for each individual claim.
    Returns a dictionary mapping each claim to its evidence score.
    """
    evaluator_results = tool_context.state.get("evaluator_result", [])
    sources = tool_context.state.get("sources", [])

    # Creates a map from domain to its evaluation for easy lookup
    evaluation_map = {item["domain"]: item for item in evaluator_results}

    # Dictionary to hold the evidence score for each claim
    claim_scores = defaultdict(float)

    # Loop through the original sources to correctly group by claim
    for source in sources:
        claim = source["original_claim"]
        domain = source["domain"]
        
        if domain in evaluation_map:
            sa = evaluation_map[domain] # sa = source_assessment
            
            # Determine bias multiplier
            bias_multiplier = 1.0 if sa.get("bias_label") == "center" else 0.75
            
            # Calculate source weight including bias
            weight = sa["recency_score"] * sa["credibility_score"] * bias_multiplier
            
            # Determine stance value (+1, -1, or 0)
            stance_value = 1 if sa["stance"] == "supports" else -1 if sa["stance"] == "opposes" else 0
            
            # Add the weight to the specific claim's score
            claim_scores[claim] += stance_value * weight

    # Save the detailed scores to the state for the confidence tool to use
    tool_context.state["claim_scores"] = dict(claim_scores)
    
    return dict(claim_scores)

def get_confidence_score(tool_context: ToolContext) -> float:
    """
    Calculates the confidence score based on the strength of the evidence scores
    for all decisive (non-inconclusive) claims.
    This tool MUST be called AFTER get_evidence_score.
    """
    # Read the per-claim scores calculated by the previous tool
    claim_scores = tool_context.state.get("claim_scores")
    
    if not claim_scores:
        return "Error: `get_evidence_score` must be run first to calculate claim scores."

    decisive_scores = []
    threshold = 0.25 # Threshold for a claim to be considered "decisive"
    
    # Filter for decisive claims and get their absolute strength
    for score in claim_scores.values():
        if abs(score) > threshold:
            decisive_scores.append(abs(score))
            
    if not decisive_scores:
        # If all claims were inconclusive, confidence is 0
        return 0.0

    # Calculate the average strength of the evidence
    average_strength = sum(decisive_scores) / len(decisive_scores)
    
    # Use math.tanh to normalize the score into a 0-1 range
    confidence_score = math.tanh(average_strength)
    
    return round(confidence_score, 3) # Return rounded score

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="""A professional agent whose job is to be the judge in a
    fact-checking system to combat misinformation.""",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score",
    tools=[get_evidence_score,get_confidence_score]
)

# Executes required runner logic for unit test of conf score agnt.
async def main():
    session_service_stateful = InMemorySessionService()

    initial_state = {
        "sources": [
            {
                "domain": "nytimes.com",
                "article_text": "A recent report from the New York Times confirms that climate change is accelerating, citing new NASA data.",
                "published_date": "2025-09-20",
                "original_claim": "Climate change is accelerating due to human activity."
            },
            {
                "domain": "foxnews.com",
                "article_text": "Fox News ran a segment suggesting that the link between climate change and human activity is exaggerated.",
                "published_date": "2025-09-15",
                "original_claim": "Climate change is accelerating due to human activity."
            },
            {
                "domain": "bbc.com",
                "article_text": "BBC published an article explaining the latest UN report on the rapid increase of global warming, largely attributed to fossil fuels.",
                "published_date": "2025-09-10",
                "original_claim": "Climate change is accelerating due to human activity."
            }
        ],
        "evaluator_result": [
            {
                "domain": "nytimes.com",
                "credibility_score": 0.9,
                "bias_label": "center",
                "recency_score": 1.0,
                "stance": "supports",
                "reasoning": "The New York Times is a highly credible source, and the article explicitly confirms the claim using NASA data. The article was also published very recently."
            },
            {
                "domain": "foxnews.com",
                "credibility_score": 0.6,
                "bias_label": "right",
                "recency_score": 1.0,
                "stance": "opposes",
                "reasoning": "Fox News has a right-leaning bias, and the article suggests that the link between climate change and human activity is exaggerated, thus opposing the claim. The article was published very recently."
            },
            {
                "domain": "bbc.com",
                "credibility_score": 0.9,
                "bias_label": "center",
                "recency_score": 0.5,
                "stance": "supports",
                "reasoning": "The BBC is a highly credible source, and the article explains the UN report attributing global warming to fossil fuels, thus supporting the claim. The article was published very recently."
            }
        ]
    }

    APP_NAME = "Conf Score Agnt"
    USER_ID = "kalyanolivera"
    SESSION_ID = str(uuid.uuid4())
    stateful_session = await session_service_stateful.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initial_state
    )

    runner = Runner(
        agent=confidence_score_agent,
        app_name=APP_NAME,
        session_service=session_service_stateful
    )

    nm = types.Content(
        role="user", parts = [types.Part(text="do the tasks that you are made to do")]
    )

    # Where `e` stands for "event."
    for e in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=nm
    ):
            if e.is_final_response() and e.content and e.content.parts:
                print(
                    f"Final response: {e.content.parts[0].text}"
                )

if __name__ == "__main__":
    asyncio.run(main())
