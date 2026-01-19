import os
from supabase import create_client
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

print("--- DEEP DIAGNOSTICS ---")
supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_SERVICE_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
openai_base = os.getenv("OPENAI_BASE_URL")

# 1. Test OpenAI
print(f"\n--- Testing OpenAI (Base: {openai_base}) ---")
if openai_key:
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            api_key=openai_key,
            openai_api_base=openai_base
        )
        # Test a small embedding
        vec = embeddings.embed_query("test")
        print(f"SUCCESS: OpenAI embedding successful (Vector len: {len(vec)})")
    except Exception as e:
        print(f"FAILURE: OpenAI Error: {str(e)[:200]}")
else:
    print("FAILURE: No OpenAI Key")

# 2. Test Supabase RPC (match_documents)
print("\n--- Testing Supabase RPC ---")
if supa_url and supa_key:
    try:
        client = create_client(supa_url, supa_key)
        dummy_vec = [0.1] * 1536
        fname = os.getenv("QUERY_NAME", "match_documents")
        
        print(f"Calling RPC: {fname}...")
        # Note: If function takes p_document_id, this might fail or succeed depending on signature
        res = client.rpc(fname, {
            "query_embedding": dummy_vec,
            "match_threshold": 0.1,
            "match_count": 1
        }).execute()
        print("SUCCESS: RPC called successfully.")
    except Exception as e:
        print(f"FAILURE: RPC Error (Fallback Test): {str(e)[:200]}")
        # Try with common param names if first failed
        try:
             res = client.rpc(fname, {"query_embedding": dummy_vec}).execute()
             print("SUCCESS: RPC worked with minimal params.")
        except Exception as e2:
             print(f"FAILURE: RPC deep fail: {str(e2)[:200]}")
else:
    print("FAILURE: No Supabase Credentials")
