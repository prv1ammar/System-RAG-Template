import sys
import os
from pathlib import Path
from uuid import UUID

# Add the current directory to sys.path to import rag_service
sys.path.append(os.getcwd())

from rag_service.service import RAGService
from rag_service.models import Bot
from dotenv import load_dotenv

load_dotenv()

def test_store_export():
    service = RAGService()
    
    # 1. Create a test bot
    print("Creating test bot...")
    bot_data = {
        "name": "Test isolation Bot",
        "description": "A bot to test export storage",
        "domain": "Testing"
    }
    
    bot_id = service.create_bot(bot_data)
    print(f"Bot created with ID: {bot_id}")
    
    # 2. Export the bot (this should update export_json in the DB)
    print("\nExporting bot to trigger storage...")
    export_data = service.export_bot(str(bot_id))
    
    # 3. Verify storage
    print("\nVerifying storage in database...")
    bot = service.db.get_bot(str(bot_id))
    
    if bot and bot.export_json:
        print("SUCCESS: export_json is populated in the database!")
        import json
        print(json.dumps(bot.export_json, indent=2))
    else:
        print("FAILURE: export_json is empty or bot not found.")

if __name__ == "__main__":
    test_store_export()
