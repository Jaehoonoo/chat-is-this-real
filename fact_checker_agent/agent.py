from google.adk.agents import Agent
from .subagents.confidence_score_agent.agent import confidence_score_agent
from .subagents.evaluator_agent.agent import evaluator_agent 
from .subagents.retrieval_agent.agent import retrieval_agent

fact_checker_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    sub_agents=[
        confidence_score_agent,
        evaluator_agent,
        retrieval_agent
    ]
)
