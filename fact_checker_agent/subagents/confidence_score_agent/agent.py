from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import uuid
import asyncio

CONFIDENCE_SCORE_AGENT_INSTRUCTION = """
    These are the source that we have:
    {sources}
    And this is the assessment of each source:
    {evaluator_result}
    Tell the user what the sources are, and what the assessment is
"""

def get_source_weight(
    credibility: float,
    bias: str,
    recency: float
):
    return credibility * recency if bias == "center" else credibility * recency * 0.75

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="""You are an agent responsible for giving a confidence score
    with regards to how confident you are.""",
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
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
                "recency_score": 1.0,
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
