import os
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase.client import create_client

def retrieve_faq_context(question: str, top_k: int = 3) -> dict:

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    TABLE_NAME = os.getenv("NAME_TABLE")
    QUERY_NAME = os.getenv("QUERY_NAME")
    
    
    if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY or not TABLE_NAME:
        print("[FAQ] Missing environment variables")
        return {"found": False, "content": ""}
    
    try:
        # Initialize
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try with vector store first
        try:
            vector_store = SupabaseVectorStore(
                embedding=embeddings,
                client=supabase,
                table_name=TABLE_NAME,
                query_name=QUERY_NAME,
            )
            
            # Use simpler similarity_search method for compatibility
            docs = vector_store.similarity_search(question, k=top_k)
            
            if not docs:
                print(f"[FAQ] No results for: {question}")
                return {"found": False, "content": ""}
            
            content = "\n\n".join(doc.page_content for doc in docs)
            print(f"[FAQ] Found {len(docs)} documents via vector store for: {question}")
            return {"found": True, "content": content}
            
        except Exception as vector_error:
            print(f"[FAQ] Vector store error: {vector_error}")
            print("[FAQ] Trying direct Supabase query...")
            
            # Fallback to direct Supabase query
            try:
                # Simple direct query to Supabase table
                response = supabase.table(TABLE_NAME).select("*").limit(top_k).execute()
                
                if not response.data:
                    print(f"[FAQ] No documents found in table: {TABLE_NAME}")
                    return {"found": False, "content": ""}
                
                # Extract content from documents
                content_parts = []
                for doc in response.data:
                    if 'content' in doc and doc['content']:
                        content_parts.append(doc['content'])
                    elif 'page_content' in doc and doc['page_content']:
                        content_parts.append(doc['page_content'])
                    elif 'text' in doc and doc['text']:
                        content_parts.append(doc['text'])
                
                if not content_parts:
                    print(f"[FAQ] No content found in documents")
                    return {"found": False, "content": ""}
                
                content = "\n\n".join(content_parts[:top_k])
                print(f"[FAQ] Found {len(content_parts)} documents via direct query for: {question}")
                return {"found": True, "content": content}
                
            except Exception as direct_error:
                print(f"[FAQ] Direct query error: {direct_error}")
                return {"found": False, "content": ""}
        
    except Exception as e:
        print(f"[FAQ] General error: {e}")
        return {"found": False, "content": ""}
