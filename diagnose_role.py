import os
import json
import base64
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def decode_jwt_payload(token):
    try:
        parts = token.split('.')
        if len(parts) < 2: return None
        # Add padding if needed
        payload = parts[1]
        padded = payload + '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        return json.loads(decoded)
    except:
        return None

print("--- DIAGNOSTICS KEY ROLE ---")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")
role = "unknown"

if supa_key:
    payload = decode_jwt_payload(supa_key)
    if payload:
        role = payload.get('role', 'unknown')
        print(f"Key Role: {role}")
    else:
        print("Key is not a valid JWT (or opaque).")
else:
    print("No key found.")

print("\n--- TESTING ---")
if role == 'anon':
    print("⚠️ WARNING: You are using an 'anon' key. This often HIDES tables if RLS policies are missing!")
    print("Recommendation: Use the 'service_role' key for the backend.")

# Proceed to check table
supa_url = os.getenv("SUPABASE_URL")
if supa_url and supa_key:
    try:
        client = create_client(supa_url, supa_key)
        # Check permissions by simple query
        print("Querying 'documents'...")
        res = client.table("documents").select("id").limit(1).execute()
        print("SUCCESS: Table found.")
    except Exception as e:
        print(f"FAILURE: {e}")
