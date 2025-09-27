"""
A single Evaluator Agent that uses tools for credibility, bias, and
recency, and produces a structured JSON output.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from datetime import datetime
from typing import Dict

from .data import SOURCE_ANALYTICS_DB

def get_source_analytics(domain: str) -> dict:
    db = SOURCE_ANALYTICS_DB
    clean_domain = domain.lower().strip().replace("www.", "")
    return db.get(
        clean_domain, {"credibility_score": 0.5, "bias_label": "center"}
    )

def recency_score(published_date: str) -> float:
    """
    Computes how recent a piece of content is. Higher score is better.
    
    Args:
        published_date: ISO 8601 formatted datetime string.
    
    Returns:
        A recency score between 0.0 and 1.0.
    """
    try:
        pub_date = datetime.fromisoformat(published_date)
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=datetime.now().astimezone().tzinfo)
        now = datetime.now(pub_date.tzinfo)
        days_old = (now - pub_date).days
        
        if days_old <= 7: return 1.0
        elif days_old <= 30: return 0.8
        elif days_old <= 180: return 0.5
        return 0.2
    except (ValueError, TypeError):
        return 0.0

EVALUATOR_PROMPT = """
You are a professional fact-checking assistant, working for a highly trusted and neutral organization.

# Your task
You will be given an input as a list of sources with claims attached to it in a JSON array: {sources_output}. For each source, you must use your tools to gather information and produce a final JSON object.

# Your Strict Workflow
For each source object you are given, you must perform the following steps in order:

1.  **MANDATORY TOOL CALLS**: You MUST call the `get_source_analytics` tool using the source's `domain` and the `recency_score` tool using the `published_date`.

2.  **REPORT TOOL OUTPUT**: The values for `credibility_score`, `bias_label`, and `recency_score` in your final output MUST be the EXACT, UNCHANGED values returned by the tools. **DO NOT invent, estimate, or modify these numbers for any reason.**

3.  **ANALYZE STANCE**: After getting the tool results, analyze the `article_text` to determine the `stance` (one of: "supports", "opposes", "neutral") toward the `original_claim`.

4.  **GENERATE OUTPUT**: Create a single JSON object containing the verbatim tool outputs and your stance analysis.

# Output format
- Your final output MUST be a **strictly valid JSON array of objects**.
- Do not add any commentary or text outside the JSON structure.
- Each object in the array must correspond to a single source and contain all the evaluated fields.

# Example structure:
[
  {
    "domain": "example.com",
    "credibility_score": 0.81,
    "bias_label": "-0.63",
    "recency_score": 1.01,
    "stance": "supports",
    "reasoning": "The domain is generally reliable, the article aligns with the claim(s), and it was published recently."
  }
]

You are responsible for passing off the JSON array as your final output to the following agent:
confidence_score_agent

You also have access to the following tools:
- get_source_analytics
- recency_score
"""

evaluator_agent = Agent(
    name="evaluator_agent",
    model="gemini-2.0-flash",
    instruction=EVALUATOR_PROMPT,
    tools=[
        get_source_analytics,
        recency_score
    ],
    output_key="evaluator_results"
)

root_agent = evaluator_agent