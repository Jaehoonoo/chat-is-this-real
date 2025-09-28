import json
import urllib.request

# --- Configuration ---
HOST = "http://localhost:8000"
AGENT_NAME = "master_agent" # This should be the name of the agent you are serving
USER_ID = "user_123"
SESSION_ID = "session_456" # Use a new session ID for a clean run

URL_TO_ANALYZE = "https://www.infowars.com/posts/rep-massie-posts-video-of-jan-6-protester-being-beaten-by-police-then-dying-in-their-custody/"
# --- End Configuration ---

def send_request():
    """
    Sends a POST request to the running ADK agent server, 
    first creating a session and then running the agent.
    """
    
    # 1. Create a Session
    session_url = f"{HOST}/apps/{AGENT_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
    session_req = urllib.request.Request(session_url, method='POST', headers={'Content-Type': 'application/json'})
    
    print(f"Creating session at: {session_url}")
    try:
        with urllib.request.urlopen(session_req) as response:
            if response.status == 200 or response.status == 201:
                print(f"Session created successfully (Status: {response.status})")
            else:
                print(f"Failed to create session. Status: {response.status}")
                print(response.read().decode('utf-8'))
                return
    except urllib.error.HTTPError as e:
        print(f"HTTP Error creating session: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
        return
    except urllib.error.URLError as e:
        print(f"URL Error creating session: {e.reason}")
        return

    # 2. Run the Agent
    run_url = f"{HOST}/run"
    run_data = {
        "app_name": AGENT_NAME,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "new_message": { # Removed the "input" wrapper
            "parts": [
                {
                    "text": f"Analyze the content at this URL: {URL_TO_ANALYZE}"
                }
            ]
        }
    }
    
    json_data = json.dumps(run_data).encode('utf-8')
    run_req = urllib.request.Request(run_url, data=json_data, headers={'Content-Type': 'application/json'})
    
    print(f"\nSending prompt to: {run_url}")
    try:
        with urllib.request.urlopen(run_req) as response:
            print(f"Status Code: {response.status}")
            response_body = response.read().decode('utf-8')
            print("Response Body:")
            try:
                parsed_json = json.loads(response_body)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print(response_body)
                
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print("Response Body:")
        print(e.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")

if __name__ == "__main__":
    send_request()