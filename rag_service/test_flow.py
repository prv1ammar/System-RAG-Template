import requests
import os
import time

BASE_URL = "http://localhost:8000"

def test_flow():
    # 1. Create a bot
    print("Creating bot...")
    bot_config = {
        "name": "Finance Bot",
        "model_name": "gpt-3.5-turbo",
        "system_prompt": "You are a financial advisor.",
        "temperature": 0.0,
        "rules": ["Only answer financial questions"]
    }
    response = requests.post(f"{BASE_URL}/bots", json=bot_config)
    bot_data = response.json()
    bot_id = bot_data["bot_id"]
    print(f"Bot created: {bot_id}")

    # 2. Ingest a document (if exists)
    # We'll skip actual file upload in this script but here is how it would look:
    """
    with open("test.pdf", "rb") as f:
        response = requests.post(f"{BASE_URL}/bots/{bot_id}/ingest", files={"file": f})
        print(response.json())
    """

    # 3. Ask a question
    print("Asking a question...")
    ask_request = {
        "question": "What is the capital of France?",
        "top_k": 3
    }
    response = requests.post(f"{BASE_URL}/bots/{bot_id}/ask", json=ask_request)
    print(f"Answer: {response.json().get('answer')}")

    # 4. Export bot
    print("Exporting bot...")
    response = requests.get(f"{BASE_URL}/bots/{bot_id}/export")
    print(f"Export data: {response.json()}")

if __name__ == "__main__":
    print("Note: Ensure the service is running at http://localhost:8000 before running this script.")
    # test_flow()
