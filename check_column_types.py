import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

client_url = os.getenv("SUPABASE_URL")
client_key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"--- DATABASE SCHEMA CHECK ({client_url}) ---")
try:
    c = create_client(client_url, client_key)
    # Use a clever query to check types from REST if possible, 
    # but since we have data, let's just inspect one record carefully
    res = c.table("documents").select("*").limit(1).execute()
    if res.data:
        val = res.data[0].get('documentId')
        print(f"First record 'documentId': {val} (Type: {type(val)})")
    else:
        print("No data in documents table.")
except Exception as e:
    print(f"Failed to check columns: {e}")
