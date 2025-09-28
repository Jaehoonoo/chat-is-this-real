from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os

# Import your agent from your project
# Make sure your project is structured as a Python package
from your_agent_project.agent import root_agent
from your_agent_project.runner import create_session_and_runner # Assume you have a helper like this

# Define the expected request body from the extension
class QueryRequest(BaseModel):
    userId: str
    sessionId: str
    query: str

# Your secret API key to protect the endpoint
EXPECTED_API_KEY = os.environ.get("MY_SECRET_API_KEY")

app = FastAPI()

@app.post("/invoke-agent")
async def invoke_agent(request: QueryRequest, x_api_key: str | None = Header(None)):
    # 🔐 --- Security Check ---
    if not EXPECTED_API_KEY or x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    try:
        # This is where you'd run your ADK agent
        # The logic will depend on your runner setup
        # This is a simplified example:
        runner, session = await create_session_and_runner(request.userId, request.sessionId)
        
        final_response = ""
        # The ADK run loop logic would go here...
        # For simplicity, we'll just simulate a response.
        # In a real app, you would process the events from runner.run()
        final_response = f"Agent processed query for user {request.userId}: '{request.query}'"

        return {"response": final_response}

    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")