import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

client_url = os.getenv("SUPABASE_URL")
client_key = os.getenv("SUPABASE_SERVICE_KEY")

print(f"--- DATABASE SCHEMA CHECK ({client_url}) ---")
try:
    c = create_client(client_url, client_key)
    # Query information_schema for columns of 'documents'
    res = c.rpc("get_columns", {"table_name": "documents"}).execute()
    print(f"Columns: {res.data}")
except Exception as e:
    # Fallback: create a temporary function to check columns if RPC fails
    print(f"RPC get_columns failed (expected if not setup). Trying raw query via REST...")
    try:
        # We can't do raw sql, but we can try to select * and see keys
        res = c.table("documents").select("*").limit(1).execute()
        if res.data:
            print(f"Columns found in data: {list(res.data[0].keys())}")
        else:
            print("No data in documents table to check column names.")
    except Exception as e2:
        print(f"Failed to check columns: {e2}")
