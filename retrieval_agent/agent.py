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
    domain: str
    source: str
    article_text: str
    published_date: str
    original_claim: list


class SourcesOutput(BaseModel):
    # NOTE: named "sources" per request
    sources: List[SourceItem] = Field(
        default_factory=list,
        description="Up to 15 diverse, reputable sources across all claims.",
    )


# -------------------------------------------------------------------
# Step 1: Finder Agent (tools allowed, no output_schema)
# -------------------------------------------------------------------

FINDER_PROMPT = r"""
**ROLE**: You are an expert researcher tasked with verifying a set of claims for factual correctness, based on science and research. Your sole job is to find and provide a list of relevant sources that either support or contest the provided claims. You must not provide any other analysis or commentary.

**TASK**
    - For each claim, use search tool to find reputable sources that support or refute the claims. Focus on authoritative sources like academic journals, government reports, etc.
    - Write a one-to-two-sentence summary for each source. This summary should clearly state whether the source supports, refutes, or provides no clear verdict on the claims.

Important Guidelines:
    - List Format Only: Your entire output must be a simple, non-formatted list. Do not use tables, JSON, or any other structured format.
    - Link First: For each source, the link must appear first.
    - Concise Summary: Follow the link with a one-to-two-sentence summary that clearly states the source's verdict (supports, refutes, or provides no clear verdict) and what part of the source says so.
    - No Other Content: Do not add any introductory phrases, closing remarks, or additional commentary. Your response should be nothing but the list of sources.
    - Real Sources Only: Only include real, verifiable URLs.
    - Diversity: Aim for a diverse set of sources, covering different perspectives and types of publications.
    - Original Source Avoidance: Do not use the original source from the claim.

**Example of an acceptable output**:
    Source: https://www.nytimes.com/2023/10/01/us/politics/new-policy.html
    Date: 2023-10-01
    Verdict: This New York Times article supports the claim that the new policy will reduce taxes, citing a recent government study.

    Source: https://www.cbo.gov/publication/56723
    Date: 2023-09-15
    Verdict: The CBO report refutes the claim, stating that the policy is projected to increase taxes for a majority of citizens.

Return around 1-3 sources per claim, up to a maximum of 15 sources total.
The claims you are to verify is listed in a JSON array as follows: {claims}
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
You are an expert data formatter. You are the second and final step in a verification pipeline. Your task is to process a list of claims and their corresponding research summaries and present the results in a clean, structured format.

<br>

## Task

Process the input provided from the previous agent. This input is a concise list of claims and the one-to-two-sentence summaries of supporting or refuting sources. Your job is to extract the key information from these summaries and format it into a structured JSON object.

<br>

## JSON Schema

Your final output must be a single JSON object that strictly adheres to the following schema.

```json
{
  "sources": [
    {
      "source": "The full URL as provided by the previous agent. **DO NOT** modify this URL in any way.",
      "domain": "The name of the source (New York Times, NPR, Nature.com, CDC.gov, etc.).",
      "article_text": "The one-to-two-sentence summary from the source indicating whether it supports or refutes the claim.",
      "why_reliable": "A short, concise rationale for the source's reliability (e.g., Official government data, Peer-reviewed journal).",
      "original_claim": "The original claim that was evaluated by this source."
    }
  ]
}
```

<br>

## Guidelines

  - **DO NOT** modify the original URL in any way. Use it exactly as provided.
  - **Derive `verdict`:** Use the one-to-two-sentence summary provided in the input directly as the `verdict`. Do not add any new information or modify the text.
  - **Derive `why_reliable`:** Base this rationale on the nature of the source (e.g., `NPR` is a "Major news organization," `Nature.com` is a "Peer-reviewed journal," and `CDC.gov` is "Official government data"). Keep this short, under 12 words.
  - **Final Output:** You must return **only** the JSON object. Do not include any extra commentary or text outside of the JSON block.

<br>
"""

formatter_agent = Agent(
    name="formatter_agent",
    model="gemini-2.0-flash",
    instruction=FORMATTER_PROMPT,
    output_schema=SourcesOutput,  # strict structured output named "sources"
    # IMPORTANT: no tools here when output_schema is set
    output_key="sources_output",
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
