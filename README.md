Chat, is this real?: The AI Fact-Checking Copilot
This is a multi-agent AI system using a loop workflow designed to combat misinformation by providing real-time fact-checking and source analysis for online news articles. Acting as a "copilot" for news consumption, this is architected as a Chrome extension that helps users critically evaluate the information they read.

This project was developed for a hackathon to demonstrate a practical application of multi-agent architecture in promoting media literacy.

🚀 How It Works
This employs a sophisticated multi-agent pipeline where each agent has a specialized role. The system is designed to be iterative, refining its analysis to achieve a high degree of confidence.

The Multi-Agent Workflow:

Agent 1: The Ingestor

Input: The full text content of a news article page.

Task: Extracts the core claims and text from the article to begin the fact-checking process.

Agent 2: The Researcher

Input: The claims from Agent 1.

Task: Scours the web to find 10-15 additional news sources that report on the same claims, providing a broad base of evidence.

Agent 3: The Evaluator (This Repository)

Input: The list of sources from Agent 2.

Task: Critically analyzes each source based on four key metrics:

Credibility: How reliable is the source? (Data-driven score)

Bias: What is the political leaning of the source? (Data-driven score)

Recency: How recently was the article published?

Stance: Does the article support, oppose, or remain neutral to the original claim?

Output: A structured JSON object detailing the evaluation for each source.

Agent 4: The Judge

Input: The structured JSON analysis from Agent 3.

Task: Synthesizes all the evidence to make a final verdict on the original claim and calculates an overall confidence score.

Iterative Refinement Loop: The system is designed to loop between Agents 2, 3, and 4. If the confidence score from Agent 4 is below 90%, the process repeats (up to 5 times), with Agent 2 seeking better sources to improve the quality of the analysis.

⚙️ The Evaluator Agent (Agent 3)
This repository contains the code for the Evaluator Agent, a crucial component of the "Chat, is this real?" pipeline. Built with the Google Agent Development Kit (ADK), this agent uses function tools to ensure its analysis is grounded in data rather than abstract reasoning.

Key Responsibilities:
Data-Driven Analysis: Instead of "knowing" about news sources, the agent makes mandatory tool calls to a comprehensive database to fetch objective scores.

Structured Output: It produces a clean, predictable JSON array that serves as the input for the final "Judge" agent.

Technical Details:
Framework: Google ADK

Language: Python

Core Logic: The agent uses two primary tools:

get_source_analytics(domain): Looks up the credibility score and numerical bias rating from a database of over 200 news sources.

recency_score(published_date): Calculates a score from 0.0 to 1.0 based on the publication date.

🛠️ Setup and Usage
This agent is designed to be run using the Google ADK CLI.

1. Prerequisites
   Python 3.10+

Google ADK installed (pip install google-adk)

2. Running the Agent
   To run the Evaluator agent in interactive mode, navigate to the project directory and execute:

adk run fact_checker_agent/subagents/evaluator_agent

3. Sample Input
   The agent expects a JSON array as input. Paste the following sample at the user: prompt to test its functionality:

[
{
"original_claim": "A new study finds that intermittent fasting leads to significant long-term weight loss.",
"domain": "upi.com",
"published_date": "2025-09-27T14:30:00Z",
"article_text": "A comprehensive meta-analysis published today confirmed the benefits of intermittent fasting. Researchers found that participants on a 16:8 fasting schedule lost an average of 8% more body weight over a year compared to control groups."
},
{
"original_claim": "A new study finds that intermittent fasting leads to significant long-term weight loss.",
"domain": "infowars.com",
"published_date": "2025-09-27T11:30:00Z",
"article_text": "The globalist-backed medical establishment is now pushing 'intermittent fasting' as another tool for population control. This so-called 'study' is a smokescreen to distract from the fact that they are engineering food shortages. They want you hungry and weak."
}
]

📊 Data Source
The credibility and bias scores used in the agent's database are derived from the Ad Fontes Media ratings, as published in a report by Fractl and SEMrush. This provides a strong, data-backed foundation for the agent's analysis.
