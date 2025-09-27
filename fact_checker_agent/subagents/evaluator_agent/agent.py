"""
A single Evaluator Agent that uses tools for credibility, bias, and
recency, and produces a structured JSON output.
"""

from google.adk.agents import Agent
from datetime import datetime
from typing import Dict

from .data import SOURCE_ANALYTICS_DB

def get_source_analytics(domain: str) -> dict:
    """
    Looks up credibility and bias information for a given news domain.
    
    Args:
        domain: The domain name of the news source (e.g., "nytimes.com").
    
    Returns:
        A dictionary with 'credibility_score' and 'bias_label'.
    """
    clean_domain = domain.lower().strip().replace("www.", "")
    # Return from DB or a default neutral value for unknown domains
    return SOURCE_ANALYTICS_DB.get(
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
            # Set timezone to local machine's for accurate comparison
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
You will be given a list of sources in a JSON array. For each source, you must use your tools to gather information and produce a final JSON object.

# Instructions for each source:
1.  **Call `get_source_analytics` tool**: Use the source's domain to get its `credibility_score` and `bias_label`.
2.  **Call `recency_score` tool**: Use the source's `published_date` to get its `recency_score`.
3.  **Analyze Content**: Read the `article_text` to determine the `stance` (one of: "supports", "opposes", "neutral") towards the `original_claim`.
4.  **Provide Reasoning**: Write a concise, one-sentence `reasoning` for the determined stance.

# Output format
- Your final output MUST be a **strictly valid JSON array of objects**.
- Do not add any commentary or text outside the JSON structure.
- Each object in the array must correspond to a single source and contain all the evaluated fields.

# Example structure:
[
  {
    "domain": "example.com",
    "credibility_score": 0.8,
    "bias_label": "center",
    "recency_score": 1.0,
    "stance": "supports",
    "reasoning": "The domain is generally reliable, the article aligns with the claim, and it was published recently."
  }
]
"""

evaluator_agent = Agent(
    name="evaluator_agent",
    model="gemini-2.0-flash",
    instruction=EVALUATOR_PROMPT,
    tools=[get_source_analytics, recency_score],
)

root_agent = evaluator_agent