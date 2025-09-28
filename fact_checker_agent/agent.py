from google.adk.agents import LoopAgent

# --- Import Sub-Agents ---
# Make sure these imports point to your actual project structure
from .subagents.analyst_agent.agent import analyst_agent
from .subagents.review_agent.agent import review_agent
from .subagents.confidence_score_agent.agent import confidence_score_agent

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
MAX_ITERATIONS = 2


# --- Fact Checking Loop ---
fact_checker_loop = LoopAgent(
    name="FactCheckingLoop",
    sub_agents=[
        analyst_agent,  # Evaluates sources and updates STATE_EVALUATED_SOURCES
        review_agent, # Reviews and refines the original claim if needed
    ],
    max_iterations=MAX_ITERATIONS,
    description="Loop that repeatedly analyzes evidence, reviews, and increases confidence until threshold is met.",
)

root_agent = fact_checker_loop
