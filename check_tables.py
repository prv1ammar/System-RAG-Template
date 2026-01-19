import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"Checking project: {supa_url}")
if not supa_url or not supa_key:
    print("Missing .env credentials")
    exit(1)

try:
    client = create_client(supa_url, supa_key)
    # Check if chatbot_env_configs exists
    res = client.table("chatbot_env_configs").select("id").limit(1).execute()
    print("SUCCESS: 'chatbot_env_configs' table EXISTS in this project.")
except Exception as e:
    print(f"FAILURE: {e}")
