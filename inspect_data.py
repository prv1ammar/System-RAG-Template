import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = os.getenv("NAME_TABLE")

if not SUPABASE_URL:
    print("Error: SUPABASE_URL not found")
    exit(1)

print(f"Connecting to Supabase: {SUPABASE_URL}")
print(f"Target Table: {TABLE_NAME}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch 5 rows to inspect content
    print("\nFetching first 5 rows...")
    response = supabase.table(TABLE_NAME).select("*").limit(5).execute()
    
    if not response.data:
        print("Table is empty or access denied.")
    else:
        print(f"Found {len(response.data)} rows.")
        for i, row in enumerate(response.data):
            print(f"\n--- Row {i+1} ---")
            # Print keys to check schema
            print(f"Keys: {list(row.keys())}")
            
            # Print content excerpt
            content = row.get('content') or row.get('page_content') or row.get('text') or "NO CONTENT FIELD FOUND"
            print(f"Content Preview: {str(content)[:200]}...")
            
            # Check embedding
            embedding = row.get('embedding')
            if embedding:
                print(f"Embedding type: {type(embedding)}")
                if isinstance(embedding, list):
                    print(f"Embedding dimension: {len(embedding)}")
                    print(f"First 5 values: {embedding[:5]}")
                elif isinstance(embedding, str):
                     print(f"Embedding is a string (len={len(embedding)})")
                     print(f"Preview: {embedding[:50]}...")
            else:
                print("No embedding found in this row.")
                
except Exception as e:
    print(f"Error: {e}")
