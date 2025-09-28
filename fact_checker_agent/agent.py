from google.adk.agents import LoopAgent
from google.adk.tools.tool_context import ToolContext

# --- Import Sub-Agents ---
# Make sure these imports point to your actual project structure
from .subagents.evaluator_agent.agent import evaluator_agent
from .subagents.confidence_score_agent.agent import confidence_score_agent
from .subagents.review_agent.agent import review_agent

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
MAX_ITERATIONS = 2

# --- State Keys ---
STATE_ORIGINAL_CLAIM = "original_claim"
STATE_EVALUATED_SOURCES = "evaluated_sources"
STATE_CONFIDENCE_SCORE = "confidence_score"


# --- Exit Tool ---
def exit_loop(tool_context: ToolContext):
    """Stop the loop when confidence score >= 90."""
    print(
        f"✅ exit_loop triggered by {tool_context.agent_name}. Confidence threshold reached."
    )
    tool_context.actions.escalate = True
    return {}


# --- Fact Checking Loop ---
fact_checker_loop = LoopAgent(
    name="FactCheckingLoop",
    sub_agents=[
        evaluator_agent,  # Evaluates sources and updates STATE_EVALUATED_SOURCES
        confidence_score_agent,  # Updates confidence and triggers exit when >= 90
        review_agent,  # Reviews and refines the original claim if needed
    ],
    max_iterations=MAX_ITERATIONS,
    description="Loop that repeatedly gathers sources, evaluates them, and increases confidence until threshold is met.",
)

root_agent = fact_checker_loop
