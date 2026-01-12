import os
import numpy as np
from supabase import create_client
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = os.getenv("NAME_TABLE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") # text-embedding-3-small

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

try:
    print(f"Connecting to Supabase... Table: {TABLE_NAME}")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Fetch one row
    print("Fetching one row...")
    response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
    
    if not response.data:
        print("No data.")
        exit()
        
    row = response.data[0]
    content = row.get('content') or row.get('text')
    old_embedding_str = row.get('embedding')
    
    # Parse old embedding (it's a string in this result)
    import json
    if isinstance(old_embedding_str, str):
        old_embedding = json.loads(old_embedding_str)
    else:
        old_embedding = old_embedding_str
        
    print(f"Content Start: {content[:50]}...")
    
    # 2. Embed content with CURRENT model
    print(f"Embedding content with {EMBEDDING_MODEL}...")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    new_embedding = embeddings.embed_query(content)
    
    # 3. Create a query
    query = "Annual Financial Report"
    query_vector = embeddings.embed_query(query)
    
    # 4. Compare
    sim_old = cosine_similarity(query_vector, old_embedding)
    sim_new = cosine_similarity(query_vector, new_embedding)
    
    print(f"\nSimilarity with OLD embedding: {sim_old:.4f}")
    print(f"Similarity with NEW embedding: {sim_new:.4f}")
    
    if sim_new > 0.7: # Threshold for 'good match'
        print("\nCONCLUSION: Re-embedding substantially IMPROVES match. The old embeddings are mismatched.")
    else:
        print("\nCONCLUSION: Even new embeddings are low? Something else is wrong.")

except Exception as e:
    print(f"Error: {e}")
