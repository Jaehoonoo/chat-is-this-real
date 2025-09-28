
import json
import urllib.request

def send_request():
    """
    Sends a POST request to the running ADK agent server.
    """
    url = "http://localhost:8000/run"
    
    # This is the data structure the master_agent is expecting,
    # based on the initial agent in its sequence.
    data = {
        "input": {
            "parts": [
                {
                    "text": "Analyze the content at this URL: https://www.infowars.com/posts/rep-massie-posts-video-of-jan-6-protester-being-beaten-by-police-then-dying-in-their-custody/"
                }
            ]
        }
    }
    
    # Encode the data to JSON
    json_data = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.status}")
            response_body = response.read().decode('utf-8')
            print("Response Body:")
            # Try to pretty-print if it's JSON
            try:
                parsed_json = json.loads(response_body)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print(response_body)
                
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Reason: {e.reason}")
        print("Response Body:")
        print(e.read().decode('utf-t'))
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")

if __name__ == "__main__":
    send_request()
