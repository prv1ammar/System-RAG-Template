import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def string_preview(s):
    if not s: return "EMPTY"
    if len(s) < 10: return s
    return s[:5] + "..." + s[-5:]

print("--- DIAGNOSTICS ---")

# 1. Check .env loading
print(f"LOADING .env...")
supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")
print(f"SUPABASE_URL: {string_preview(supa_url)}")
print(f"SUPABASE_KEY: {string_preview(supa_key)}")

# 2. Test Vector DB Connection (from .env)
print("\n--- TESTING VECTOR DB (User Env) ---")
if supa_url and supa_key:
    try:
        client = create_client(supa_url, supa_key)
        # Try a simple select or just init
        print("SUCCESS: Client init successful")
        # res = client.table("documents").select("count", count="exact").execute()
        # print(f"SUCCESS: Table access successful: {res}")
    except Exception as e:
        print(f"FAILURE: Vector DB Connection Failed: {e}")
else:
    print("FAILURE: Missing credentials for Vector DB")

# 3. Test Management DB Connection (ConfigManager)
print("\n--- TESTING MANAGEMENT DB (ConfigManager) ---")
try:
    from database_manager.config_manager import get_config_manager
    mgr = get_config_manager()
    print(f"Manager URL: {string_preview(str(mgr.supabase.supabase_url))}")
    # print(f"Manager Key: {string_preview(str(mgr.supabase.supabase_key))}") # Some clients hide key
    
    success, msg = mgr.test_connection()
    if success:
        print(f"SUCCESS: {msg}")
    else:
        print(f"FAILURE: {msg}")
        
except Exception as e:
    print(f"FAILURE: ConfigManager Error: {e}")
