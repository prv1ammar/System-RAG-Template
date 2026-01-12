import requests
import json
import time
import os
from uuid import UUID

BASE_URL = "http://localhost:8000"

def test_api_workflow():
    print(f"--- Starting API Test Workflow at {BASE_URL} ---")
    
    # 1. Health Check
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Step 1: Health Check -> {resp.status_code} {resp.json()}")
    except Exception as e:
        print(f"FAILURE: Server not reachable at {BASE_URL}. Error: {e}")
        return

    # 2. Create a Bot
    bot_payload = {
        "name": "API Test Bot",
        "description": "Bot created via automated API test",
        "domain": "Testing"
    }
    resp = requests.post(f"{BASE_URL}/bots", json=bot_payload)
    if resp.status_code == 200:
        bot = resp.json()
        bot_id = bot['id']
        print(f"Step 2: Create Bot -> SUCCESS (ID: {bot_id})")
    else:
        print(f"Step 2: Create Bot -> FAILED ({resp.status_code}) {resp.text}")
        return

    # 3. Export Bot (Verify stored JSON)
    resp = requests.get(f"{BASE_URL}/bots/{bot_id}/export")
    if resp.status_code == 200:
        print(f"Step 3: Export Bot -> SUCCESS")
        # print(json.dumps(resp.json(), indent=2))
    else:
        print(f"Step 3: Export Bot -> FAILED ({resp.status_code})")

    # 4. Ask a question (Scoped)
    ask_payload = {
        "bot_id": bot_id,
        "question": "What is the purpose of this bot?",
        "top_k": 3
    }
    print(f"Step 4: Asking Question...")
    resp = requests.post(f"{BASE_URL}/bots/{bot_id}/ask", json=ask_payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"Step 4: Ask Question -> SUCCESS")
        print(f"Answer: {result['answer'][:100]}...")
        print(f"Bot ID in Response: {result['bot_id']}")
    else:
        print(f"Step 4: Ask Question -> FAILED ({resp.status_code}) {resp.text}")

    # 5. Send Message (Alias)
    print(f"Step 5: Sending Message (Alias)...")
    resp = requests.post(f"{BASE_URL}/bots/{bot_id}/message", json=ask_payload)
    if resp.status_code == 200:
        print(f"Step 5: Send Message -> SUCCESS")
    else:
        print(f"Step 5: Send Message -> FAILED ({resp.status_code})")

    print("\n--- API Test Workflow Completed! ---")

if __name__ == "__main__":
    test_api_workflow()
