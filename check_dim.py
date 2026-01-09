import os
import json
import ast
from supabase import create_client
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = os.getenv("NAME_TABLE")
QUERY_NAME = os.getenv("QUERY_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

print(f"Model in .env: {EMBEDDING_MODEL}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Check Dimension
    print("Fetching one row to check dimension...")
    response = supabase.table(TABLE_NAME).select("embedding").limit(1).execute()
    
    if response.data:
        emb_str = response.data[0]['embedding']
        # Handle if it's already a list or a string
        if isinstance(emb_str, str):
            emb_list = json.loads(emb_str)
        else:
            emb_list = emb_str
            
        print(f"Actual Embedding Dimension in DB: {len(emb_list)}")
    else:
        print("No data found.")
        exit()

    # 2. Test Relevant Query
    print("\nTesting retrieval with RELEVANT query...")
    question = "Who is the Director General?"
    print(f"Question: {question}")
    
    print(f"Testing with '{EMBEDDING_MODEL}'...")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    query_embedding = embeddings.embed_query(question)
    print(f"Generated Query Embedding Dimension: {len(query_embedding)}")
    
    if len(emb_list) != len(query_embedding):
        print("WARNING: Dimension mismatch!")
    else:
        print("Dimensions match.")
        
    params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.1,
        "match_count": 5
    }
    
    print(f"Calling RPC {QUERY_NAME} with threshold 0.1...")
    rpc_response = supabase.rpc(QUERY_NAME, params).execute()
    
    if rpc_response.data:
        print(f"Success! Found {len(rpc_response.data)} documents.")
        print(f"First result content: {str(rpc_response.data[0].get('content', ''))[:100]}...")
        if 'similarity' in rpc_response.data[0]:
             print(f"Similarity score: {rpc_response.data[0]['similarity']}")
    else:
        print("RPC returned NO results.")
        
except Exception as e:
    print(f"Error: {e}")
