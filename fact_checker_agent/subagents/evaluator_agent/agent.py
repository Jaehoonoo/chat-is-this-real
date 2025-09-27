# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Evaluator Agent without output_schema (JSON enforcement is handled by prompt)."""

from google.adk.agents import Agent
from datetime import datetime
from typing import Dict

# -------------------------------------------------------------------
# Domain credibility database
# -------------------------------------------------------------------

CREDIBILITY_DB: Dict[str, float] = {
    "nytimes.com": 0.9,
    "foxnews.com": 0.6,
    "breitbart.com": 0.3,
    "bbc.com": 0.95,
    "cnn.com": 0.85,
    "theguardian.com": 0.9,
    "wsj.com": 0.88,
}

def get_domain_credibility(domain: str) -> float:
    """
    Look up the credibility score for a domain.
    """
    if not domain or not isinstance(domain, str):
        return 0.5
    return CREDIBILITY_DB.get(domain.lower().strip(), 0.5)

def recency_score(published_date: str) -> float:
    """
    Compute recency score from ISO8601 date string.
    """
    try:
        pub = datetime.fromisoformat(published_date)
    except Exception:
        return 0.2  # fallback for bad date format
    days_old = (datetime.now() - pub).days
    if days_old <= 7:
        return 1.0
    elif days_old <= 30:
        return 0.8
    elif days_old <= 180:
        return 0.5
    return 0.2

# -------------------------------------------------------------------
# Evaluator Agent Prompt
# -------------------------------------------------------------------

EVALUATOR_PROMPT = """
You are a professional fact-checking assistant, working for a highly trusted and neutral organization.

# Your task
You will be given a list of sources. Each source includes:
  * domain (the source domain of the article)
  * article text (the content being analyzed)
  * published_date (ISO format)
  * original_claim (the claim being fact-checked)

For each source, produce an evaluation row with the following fields:

- credibility_score (float, 0.0–1.0): Reliability of the source domain. Use the provided credibility tool, and adjust if content warrants.
- bias_label (string, one of: "left", "center", "right", "mixed"): The likely political/ideological bias of the source or article.
- recency_score (float, 0.0–1.0): How current the content is, using the recency scoring tool.
- stance (string, one of: "supports", "opposes", "neutral"): Whether the article supports, opposes, or is neutral toward the original_claim.
- reasoning (string): A concise explanation (1–2 sentences).

# Output format
- Output a **strictly valid JSON array**, where each element is an object corresponding to a single source.
- Do not add commentary or text outside the JSON.
- Example structure:

[
  {
    "domain": "example.com",
    "credibility_score": 0.8,
    "bias_label": "center",
    "recency_score": 1.0,
    "stance": "supports",
    "reasoning": "The domain is generally reliable, the article aligns with the claim, and it was published recently."
  },
  ...
]
"""

# -------------------------------------------------------------------
# Agent Definition (no output_schema)
# -------------------------------------------------------------------

evaluator_agent = Agent(
    name="evaluator_agent",
    model="gemini-2.0-flash",
    instruction=EVALUATOR_PROMPT,
    tools=[get_domain_credibility, recency_score],
    output_key="evaluator_result",
)

# Required by ADK CLI
root_agent = evaluator_agent
