from google.adk.agents import Agent

CONFIDENCE_SCORE_AGENT_INSTRUCTION = """
    These are the sources that we have:
    {sources}
    And this is the assessment of each source:
    {evaluator_result}
    Notice that each source is associated with a claim.
    So basically claim is associated with source, which is associated with its
    assessment.
    I need you to associated each claim with the associated assessment of its
    associated source.
    So like, for each claim, provide the user with to level of credibility
    based on the associated source.
"""

confidence_score_agent = Agent(
    model="gemini-2.0-flash-001",
    name="confidence_score_agent",
    description="""You are an agent responsible for giving a confidence score
    with regards to how confident you are."""
    instruction=CONFIDENCE_SCORE_AGENT_INSTRUCTION,
    output_key="confidence_score"
)
