import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def preview(s):
    if not s: return "MISSING"
    return s[:10] + "..." + s[-5:]

print("--- FINAL ARCHITECTURE DIAGNOSTICS ---")

# 1. Management Project
mgmt_url = os.getenv("MANAGEMENT_SUPABASE_URL")
mgmt_key = os.getenv("MANAGEMENT_SUPABASE_KEY")
print(f"\n1. Management Project ({mgmt_url})")
try:
    c = create_client(mgmt_url, mgmt_key)
    # Check for chatbot_env_configs
    res = c.table("chatbot_env_configs").select("count", count="exact").execute()
    print(f"✅ Success: 'chatbot_env_configs' table accessible.")
except Exception as e:
    print(f"❌ Failed: {e}")

# 2. Client Project
client_url = os.getenv("SUPABASE_URL")
client_key = os.getenv("SUPABASE_SERVICE_KEY")
print(f"\n2. Client Project ({client_url})")
try:
    c = create_client(client_url, client_key)
    # Check for documents
    res = c.table("documents").select("count", count="exact").execute()
    print(f"✅ Success: 'documents' table accessible.")
    # Check for match_documents function
    dummy_vec = [0.1] * 1536
    res = c.rpc("match_documents", {
        "query_embedding": dummy_vec,
        "match_threshold": 0.1,
        "match_count": 1
    }).execute()
    print(f"✅ Success: 'match_documents' function callable.")
except Exception as e:
    print(f"❌ Failed: {e}")

# 3. OpenAI
print("\n3. OpenAI")
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
if api_key and base_url:
    print(f"✅ Credentials present (Base: {base_url})")
else:
    print(f"❌ Missing credentials (Key: {bool(api_key)}, Base: {bool(base_url)})")
