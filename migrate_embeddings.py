import os
import time
from supabase import create_client
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TABLE_NAME = os.getenv("NAME_TABLE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") 

print(f"Migrating table: {TABLE_NAME}")
print(f"Using model: {EMBEDDING_MODEL}")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    embeddings_model = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
    
    # 1. Fetch all rows (assuming small DB < 1000 rows for now)
    response = supabase.table(TABLE_NAME).select("*").execute()
    rows = response.data
    
    if not rows:
        print("No rows to migrate.")
        exit()
        
    print(f"Found {len(rows)} rows to migrate.")
    
    for i, row in enumerate(rows):
        doc_id = row['id']
        content = row.get('content') or row.get('text') or row.get('page_content')
        
        if not content:
            print(f"Skipping row {doc_id}: No content.")
            continue
            
        print(f"Processing {i+1}/{len(rows)}: ID={doc_id}...")
        
        # Generate new embedding
        try:
             new_embedding = embeddings_model.embed_query(content)
             
             # Update row
             update_res = supabase.table(TABLE_NAME).update({"embedding": new_embedding}).eq("id", doc_id).execute()
             
             if not update_res.data:
                 print(f"Failed to update row {doc_id}")
             
             # Avoid rate limits
             time.sleep(0.2)
             
        except Exception as e:
            print(f"Error processing row {doc_id}: {e}")
            
    print("Migration completed successfully.")

except Exception as e:
    print(f"Critical Error: {e}")
