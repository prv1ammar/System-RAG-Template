import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_rich_api():
    print("--- Testing Rich API Response Format ---")
    
    # 1. Health check
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {health.status_code} - {health.json()}")
    except Exception as e:
        print(f"Server error: {e}")
        return

    # 2. Create a bot for testing
    bot_id = str(uuid.uuid4())
    bot_payload = {
        "id": bot_id,
        "name": "Rich Test Bot",
        "description": "Bot for testing rich formats",
        "domain": "Test"
    }
    try:
        # Use existing create bot endpoint
        create_resp = requests.post(f"{BASE_URL}/bots", json=bot_payload)
        print(f"Create Bot: {create_resp.status_code}")
    except Exception as e:
        print(f"Create Bot Error: {e}")

    # 3. Test Ask Question (Should return a LIST of objects)
    ask_payload = {
        "bot_id": bot_id,
        "question": "Hello, who are you?",
        "top_k": 3
    }
    
    print(f"\nTesting /ask endpoint with Bot ID: {bot_id}")
    try:
        ask_resp = requests.post(f"{BASE_URL}/bots/{bot_id}/ask", json=ask_payload)
        print(f"Status Code: {ask_resp.status_code}")
        if ask_resp.status_code == 200:
            response_json = ask_resp.json()
            print("Response JSON (Expected to be a list):")
            print(json.dumps(response_json, indent=2))
            
            if isinstance(response_json, list):
                print("\n✅ Verification SUCCESS: Response is a LIST of objects.")
            else:
                print("\n❌ Verification FAILED: Response is NOT a list.")
        else:
            print(f"Error details: {ask_resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

    # 4. Test Message Alias
    print(f"\nTesting /message alias...")
    try:
        msg_resp = requests.post(f"{BASE_URL}/bots/{bot_id}/message", json=ask_payload)
        if msg_resp.status_code == 200:
            print("✅ /message alias returned 200 OK")
        else:
            print(f"❌ /message alias failed: {msg_resp.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_rich_api()
