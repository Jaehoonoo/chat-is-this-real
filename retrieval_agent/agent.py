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
**ROLE**: You are an expert researcher tasked with finding reputable sources related a set of claims. Your sole job is to find and provide a list of relevant sources that either proves or disproves the provided claims. You must not provide any other analysis or commentary. Be concise.

**TASK**
    1. For each claim:
        - generate relevant search queries that prove/disprove the claim.
        - use ONLY the provided google_search tool to find reputable sources. Focus on direct, authoritative pages rather than aggregator blogs.
        - extract key information from each source, including the publication date, author, and a brief summary of the content of whether the source disprove or proves the original claim.
    2. Compile and return the final list.

Important Guidelines:
    - List Format Only: Your entire output must be a simple, non-formatted list. Do not use tables, JSON, or any other structured format.
    - Each source entry must include: domain, published date, verdict summary, and original claim.
    - Non-generic URLs: Extract a concise domain name from the source content or original URL and include it in your summary. **DO NOT** use search-engine URLs like *https://vertexaisearch.cloud.google.com* or base64-hased URLs. **DERIVE** URLs from source, such as "CDC.gov", "Nature", "BBC", "NOAA", "Stanford.edu",...
    - Do not add any introductory phrases, closing remarks, or additional commentary. 
    - Do not use the original source from the claim.

**Example output**:
    Domain: https://www.nytimes.com
    Published Date: 2023-10-01
    Verdict: This New York Times article proves the claim that the new policy will reduce taxes, citing a recent government study.
    Original Claim: The new policy will reduce taxes for the middle class.

    Domain: https://www.cbo.gov
    Date: 2023-09-15
    Verdict: The CBO report disproves the claim, stating that the policy is projected to increase taxes for a majority of citizens.
    Original Claim: The new policy will reduce taxes for the middle class.

Return up to a maximum of 15 sources total. The claims you are to verify is listed in a JSON array as follows: {claims}
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
## Task

Process the list of sources and their respective stance summaries of supporting or refuting sources. Your job is to extract the key information from these summaries and format it into a structured JSON object.

## JSON Schema

Your final output must be a single JSON object that strictly adheres to the following schema.

```json
{
  "sources": [
    {
      "domain": "The concise url of the publisher name from the URL/domain  (e.g., "CDC.gov", "Nature", "BBC", "NOAA", "Stanford.edu", "SEC").",
      "article_text": "The one-sentence summary from the source indicating whether it proves or disproves the claim.",
      "why_reliable": "A short, concise rationale for the source's reliability (e.g., Official government data, Peer-reviewed journal).",
      "original_claim": "The original claim that was evaluated by this source."
    }
  ]
}
```

## Guidelines

  - **Derive `article_text`:** Use the one-sentence summary provided in the input directly as the `verdict`. Do not add any new information or modify the text.
  - **Derive `why_reliable`:** Base this rationale on the nature of the source (e.g., `NPR` is a "Major news organization," `Nature.com` is a "Peer-reviewed journal," and `CDC.gov` is "Official government data"). Keep this short, under 12 words.
  - **Final Output:** You must return **only** the JSON object. Do not include any extra commentary or text outside of the JSON block.
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
