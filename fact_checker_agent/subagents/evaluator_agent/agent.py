# agent_b.py
import json
from google.adk.agents import Agent
from google.adk.tools import google_search

B_SYSTEM_PROMPT = """
You are Agent B (Verifier).

Input:
{claims}

Tasks:
1. Review the provided factual claims (process at most 5).
2. Fact-check each claim using independent, high-quality sources.
   • Prefer peer-reviewed journals, government (.gov) or educational (.edu) sites,
     and established newsrooms with corrections policies.
   • Deduplicate mirrors and syndicated content.
3. Use **no more than 15 unique independent sources** across all claims.

Output JSON ONLY in **this exact schema**:
{
  "article": { "url": "", "title": "" },      // keep keys even if empty
  "claims": [                                 // same list key as input
    {
      "claim": "...",
      "status": "supported | contested | unclear",
      "evidence_urls": ["url1","url2",...]
    }
  ],
  "sources": [                                // master list of ≤15 unique sources
    { "url": "...", "outlet": "...", "why_reliable": "..." }
  ],
  "notes": "Summary or caveats"
}
"""

agent_b = Agent(
    name="agent_b_verifier",
    model="gemini-2.5-flash",
    instruction=B_SYSTEM_PROMPT,
    description="Verifies up to 5 claims with ≤15 reliable sources and returns the same output schema.",
    tools=[google_search],
    output_key="sources"
)
