import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def string_preview(s):
    if not s: return "EMPTY"
    if len(s) < 10: return s
    return s[:5] + "..." + s[-5:]

print("--- DIAGNOSTICS DEEP ---")

# 2. Test Vector DB Connection (from .env)
supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")
print(f"URL: {string_preview(supa_url)}")

print("\n--- TESTING VECTOR DB QUERY ---")
if supa_url and supa_key:
    try:
        client = create_client(supa_url, supa_key)
        print("Client init success")
        # Try a real query
        print("Attemping to select from 'documents' table...")
        res = client.table("documents").select("id").limit(1).execute()
        print(f"SUCCESS: Query returned {len(res.data)} rows")
    except Exception as e:
        print(f"FAILURE: Vector DB Connection/Query Failed: {e}")
else:
    print("FAILURE: Missing credentials")
