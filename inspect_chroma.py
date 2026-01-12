import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def inspect_chroma():
    persist_directory = "data/chroma_db"
    if not os.path.exists(persist_directory):
        print(f"Directory {persist_directory} does not exist.")
        return

    embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    
    # Get all documents from Chroma
    data = vector_store.get()
    metadatas = data.get('metadatas', [])
    
    print(f"Total chunks in Chroma: {len(metadatas)}")
    
    bot_ids = set()
    for meta in metadatas:
        if 'bot_id' in meta:
            bot_ids.add(meta['bot_id'])
        else:
            bot_ids.add("MISSING")
            
    print(f"Bot IDs found in metadata: {bot_ids}")

if __name__ == "__main__":
    inspect_chroma()
