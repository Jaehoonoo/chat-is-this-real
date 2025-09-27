# agent_b_pydantic.py
from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl, Field
from google.adk.agents import LlmAgent
from google.adk.tools import google_search  # <-- real online search tool

# ----- Output schema (unchanged) -----
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

B_SYSTEM_PROMPT = """
You are Agent B (Verifier).

Input JSON: {"claims":[{"claim":"...","evidence_quote":"..."}]}
Constraints:
- Process at most 5 claims.
- Use no more than 15 unique independent sources total.
- Prefer peer-reviewed journals, .gov/.edu, and established newsrooms; deduplicate mirrors.
- Try to provide ≥2 strong evidence URLs per claim when possible.
Return ONLY JSON matching the schema (article, claims, sources, notes). Ensure each evidence URL also appears in the top-level sources list.
"""

agent_b = LlmAgent(
    name="agent_b_verifier",
    model="gemini-2.5-flash",   # your configured model
    instruction=B_SYSTEM_PROMPT,
    tools=[google_search],      # <-- live web search
    output_schema=VerifyOutput
)
