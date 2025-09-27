# agent_b.py
from typing import List, Literal, Optional, Annotated
from pydantic import BaseModel, HttpUrl, Field
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

UrlStr = Annotated[str, Field(pattern=r"^https?://")]

# ---------- Pydantic output schema ----------
class ArticleInfo(BaseModel):
    url: Optional[HttpUrl] = None
    title: str = ""

class ClaimResult(BaseModel):
    claim: str
    status: Literal["supported", "contested", "unclear"]
    evidence_urls: List[HttpUrl] = Field(default_factory=list)

class SourceItem(BaseModel):
    url: HttpUrl
    outlet: str
    why_reliable: str

class VerifyOutput(BaseModel):
    article: ArticleInfo
    claims: List[ClaimResult]
    sources: List[SourceItem]
    notes: str


# ---------- System prompt ----------
B_SYSTEM_PROMPT = """
You are Agent B (Verifier).

Input JSON: 
{
  "claims": [
    {"claim":"...", "evidence_quote":"..."},
    ...
  ]
}

Tasks:
1. Review the provided factual claims (handle **at most 5**).
2. For each claim:
   • Fact-check using independent, high-quality sources.
   • Prefer peer-reviewed journals, government (.gov) or educational (.edu) sites,
     and established newsrooms with corrections policies.
   • Deduplicate mirrors and syndicated content.
3. Use **no more than 15 unique independent sources** total across all claims.
4. Provide a concise “notes” summary of the overall credibility.

Output JSON ONLY in this exact schema:
{
  "article": { "url": "", "title": "" },
  "claims": [
    { "claim": "...", "status": "supported | contested | unclear",
      "evidence_urls": ["url1","url2", ...] }
  ],
  "sources": [
    { "url": "...", "outlet": "...", "why_reliable": "..." }
  ],
  "notes": "Summary or caveats"
}
"""


# ---------- Agent B definition ----------
retrieval_agent = LlmAgent(
    name="retrieval_agent",
    model="gemini-2.5-flash",
    instruction=B_SYSTEM_PROMPT,
    description=(
        "Takes a JSON payload with up to 5 factual claims and "
        "returns a credibility report with ≤15 unique supporting sources."
    ),
    tools=[google_search],            # live online search
    output_schema=VerifyOutput        # enforce structured JSON output
)

# Required by ADK CLI
root_agent = retrieval_agent