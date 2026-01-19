from database_manager.config_manager import get_config_manager
import uuid
import json

mgr = get_config_manager()

print("--- TESTING SAVE CONFIG ---")
chatbot_id = str(uuid.uuid4())
config = {
    "OPENAI_MODEL": "gpt-4-mini",
    "EMBEDDING_MODEL": "text-embedding-3-small",
    "PROJECT_NAME": "test_bot_" + chatbot_id[:4],
    "SYSTEM_PROMPT": "You are a test.",
    "DOCUMENT_ID": "doc_123"
}

print(f"Saving for ID: {chatbot_id}")
ids = mgr.save_config(chatbot_id, config)

if ids:
    print(f"✅ SAVE SUCCESS: {ids}")
    
    print("--- TESTING GET CONFIG ---")
    fetched = mgr.get_config(chatbot_id)
    print(f"Fetched Config Keys: {list(fetched.keys())}")
    if fetched.get("DOCUMENT_ID") == "doc_123":
         print("✅ DOCUMENT_ID MATCH")
    else:
         print(f"❌ DOCUMENT_ID MISMATCH: {fetched.get('DOCUMENT_ID')}")
else:
    print("❌ SAVE FAILED (ids is empty/None)")
