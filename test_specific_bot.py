import requests
import json

bot_id = "b6a0423b-ba4a-44e3-bf4c-feb62909353c"
url = f"http://localhost:8000/bots/{bot_id}/ask"

payload = {
    "bot_id": bot_id,
    "question": "What services do you offer?",
    "top_k": 3
}

print(f"Testing Bot ID: {bot_id}")
print(f"URL: {url}")

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
