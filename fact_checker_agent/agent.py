import asyncio
import os
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

# --- Import Your Sub-Agents ---
# Make sure these paths are correct for your project structure
from .subagents.retrieval_agent.agent import retrieval_agent
from .subagents.evaluator_agent.agent import evaluator_agent
from .subagents.confidence_score_agent.agent import confidence_score_agent # This will be adapted below

# --- Constants ---
GEMINI_MODEL = "gemini-2.0-flash"
MAX_ITERATIONS = 5

# --- State Keys (for passing data between agents) ---
STATE_ORIGINAL_CLAIM = "original_claim"
STATE_EVALUATED_SOURCES = "evaluated_sources"
STATE_CONFIDENCE_SCORE = "confidence_score"

# --- Tool Definition ---
def exit_loop(tool_context: ToolContext):
  """Call this function ONLY when the confidence score is 90 or greater, signaling the iterative process is complete."""
  print(f"✅ [Tool Call] exit_loop triggered by {tool_context.agent_name}. Final confidence score met.")
  tool_context.actions.escalate = True
  return {}

# --- Agent Definitions ---

# STEP 1: Initial Ingestor Agent (Runs ONCE)
# This agent's job is to set up the initial state for the loop.
ingestor_agent = LlmAgent(
    name="IngestorAgent",
    model=GEMINI_MODEL,
    instruction="""
        You will be given the raw text of a news article.
        1. Extract the primary claim being made in the article.
        2. Set the initial confidence score to 0.
        Your output must be a JSON object with two keys: 'original_claim' and 'confidence_score'.
    """,
    description="Extracts the initial claim and sets the starting confidence score to 0.",
    # This agent's output will populate the initial state for the loop
    output_key=[STATE_ORIGINAL_CLAIM, STATE_CONFIDENCE_SCORE]
)

# STEP 2: The Main Refinement Loop
# This LoopAgent contains the sub-agents that will run repeatedly.

# We need to adapt your Confidence Score Agent to be the decision-maker.
# It now has the `exit_loop` tool.
confidence_and_exit_agent = LlmAgent(
    name="ConfidenceAndExitAgent",
    model=GEMINI_MODEL,
    include_contents='none', # It will only use data from the state
    instruction=f"""
        You are the Judge in a fact-checking process. Your task is to calculate a final confidence score and decide if the process is complete.

        **CONTEXT:**
        - Original Claim: `{{{STATE_ORIGINAL_CLAIM}}}`
        - Evaluated Sources Analysis: `{{{STATE_EVALUATED_SOURCES}}}`

        **YOUR STRICT WORKFLOW:**
        1.  Review all the provided information.
        2.  Calculate a new, overall `confidence_score` as a number between 0 and 100 based on the credibility, bias, and stance of all evaluated sources.
        3.  **DECIDE THE ACTION**:
            -   **IF the new `confidence_score` is 90 or greater**: Your ONLY action is to call the `exit_loop()` tool.
            -   **IF the new `confidence_score` is less than 90**: Your output must be ONLY the new numerical confidence score. Do not add any other text or symbols. For example: `85`

        You must either call the `exit_loop` tool OR output the new score.
    """,
    description="Calculates the overall confidence score and either exits the loop if >= 90, or updates the score to continue.",
    tools=[exit_loop],
    output_key=STATE_CONFIDENCE_SCORE # Overwrites the confidence score in the state for the next loop
)

# The loop itself, which runs the core fact-checking process.
fact_checking_loop = LoopAgent(
    name="FactCheckingLoop",
    # The order of agents in the loop is critical
    sub_agents=[
        retrieval_agent,           # Agent 2: Finds sources based on the claim
        evaluator_agent,           # Agent 3: Analyzes the sources, updates STATE_EVALUATED_SOURCES
        confidence_and_exit_agent, # Agent 4: Judges the result and decides whether to continue
    ],
    max_iterations=MAX_ITERATIONS
)


# STEP 3: The Root Agent (Overall Sequential Pipeline)
# This is the main agent you will run.
root_agent = SequentialAgent(
    name="FactCheckerPipeline",
    sub_agents=[
        ingestor_agent,      # Runs first to set up the state
        fact_checking_loop,   # Then runs the iterative fact-checking process
        confidence_score_agent,  # Finally, outputs the final confidence score
    ],
    description="An orchestrator that initiates a fact-checking process and then iteratively refines the result until a high confidence score is achieved."
)