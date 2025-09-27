from google.adk.agents import Agent
from pydantic import BaseModel

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    output_key="confidence_score"
)
