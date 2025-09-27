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

"""Sources Agent (sequential)
Step 1: Find up to 15 reputable URLs for <= 5 claims (with google_search).
Step 2: Format them into {"sources":[{"url","outlet","why_reliable"}]}.
"""

from typing import List
from pydantic import BaseModel, HttpUrl, Field
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import google_search

# -------------------------------------------------------------------
# Output schema
# -------------------------------------------------------------------

class SourceItem(BaseModel):
    url: HttpUrl
    outlet: str
    why_reliable: str

class SourcesOutput(BaseModel):
    # NOTE: named "sources" per request
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="Up to 15 diverse, reputable sources across all claims."
    )

# -------------------------------------------------------------------
# Step 1: Finder Agent (tools allowed, no output_schema)
# -------------------------------------------------------------------

FINDER_PROMPT = r"""
You are the first step in a two-step pipeline.

Input JSON:
{
  "claims": ["...", "...", ...]  // up to 5 short factual claims
}

Your task:
- Use ONLY the google_search tool to find up to 15 unique, reputable URLs
  relevant to the combined set of claims.
- Prefer primary/authoritative sources: .gov, .edu, journals, official press,
  standards bodies, reputable newsrooms (diversify outlets).
- Avoid duplicates and near-duplicates (same domain + same story).
- Focus on direct, authoritative pages rather than aggregator blogs.

Output (STRICT):
{
  "raw_sources": [
    { "url": "<absolute url>", "title": "<page title or best guess>" }
  ]
}

Rules:
- Consider only the first 5 claims.
- Cap total results at 15 across ALL claims.
- Return ONLY the JSON object above. No extra commentary.
"""

finder_agent = Agent(
    name="finder_agent",
    model="gemini-2.0-flash",
    instruction=FINDER_PROMPT,
    tools=[google_search],  # tools allowed here
    # no output_schema here (cannot combine with tools)
)

# -------------------------------------------------------------------
# Step 2: Formatter Agent (no tools, structured output)
# -------------------------------------------------------------------

FORMATTER_PROMPT = r"""
You are the second step in a two-step pipeline.

Input JSON from previous step:
{
  "raw_sources": [
    { "url": "...", "title": "..." },
    ...
  ]
}

Your task:
- Convert raw_sources into the final schema:

{
  "sources": [
    { "url": "<absolute url>", "outlet": "<publisher>", "why_reliable": "<=12 words>" }
  ]
}

Guidelines:
- For "outlet": derive a concise publisher name from the URL/domain
  (e.g., "CDC.gov", "Nature", "BBC", "NOAA", "Stanford.edu", "SEC").
- For "why_reliable" (<= 12 words), use short rationales like:
  "Official government data", "Peer-reviewed journal", "University site (.edu)",
  "Company press release", "Standards body", "Major newsroom with editorial standards".
- Keep at most 15 entries total.
- Do NOT invent or change URLs; use them as given.
- Output ONLY the JSON object matching the final schema—no extra commentary.
"""

formatter_agent = Agent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT,
    output_schema=SourcesOutput,  # strict structured output named "sources"
    # IMPORTANT: no tools here when output_schema is set
)

# -------------------------------------------------------------------
# Root: Sequential coordinator
# -------------------------------------------------------------------

retrieval_agent = SequentialAgent(
    name="retrieval_agent",
    description="Step 1: find URLs with google_search; Step 2: format to {sources:[...]}.",
    sub_agents=[finder_agent, formatter_agent],
)

# Required by ADK CLI
root_agent = retrieval_agent
