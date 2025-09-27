"""
A single Evaluator Agent that uses tools for credibility, bias, and
recency, and produces a structured JSON output.
"""

from google.adk.agents import Agent
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
You will be given an input as a list of sources with claims attached to it in a JSON array. For each source, you must use your tools to gather information and produce a final JSON object.

# Rules (non-negotiable)
1. **Tool usage**
   - You MUST call the `get_source_analytics` tool using the source's `domain`.
   - You MUST call the `recency_score` tool using the `published_date`.
   - Each tool may be called **exactly once per source**. Do not re-call, repeat, or retry once results are returned.

2. **Tool results**
   - The values for `credibility_score`, `bias_label`, and `recency_score` in your final output MUST be the EXACT, UNCHANGED values returned by the tools.  
   - Store these outputs and reuse them. Do not attempt to re-fetch, regenerate, or estimate these values.

3. **Stance analysis**
   - After tool results are available, analyze the `article_text` to determine the `stance` toward the `original_claim`.  
   - Valid stance labels: "supports", "opposes", "neutral".  
   - Perform stance analysis in a single pass only; do not repeat or revise.

4. **Output generation**
   - Create one JSON object per source containing:  
     - `domain`  
     - `credibility_score` (from tool)  
     - `bias_label` (from tool)  
     - `recency_score` (from tool)  
     - `stance` (your analysis)  
   - Place all source objects into a single JSON array.  
   - The JSON array must be strictly valid.  
   - Produce this JSON array only once, after all sources are processed.  
   - Do not include commentary or extra text.

# Example structure
[
  {
    "domain": "example.com",
    "credibility_score": 0.81,
    "bias_label": "-0.63",
    "recency_score": 1.01,
    "stance": "supports"
  }
]

# Responsibility
- You must pass the final JSON array as your output to the following agent: `confidence_score_agent`.

# Tools you may use
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