import os
import json
from typing import Dict, Any, Optional, List
from uuid import UUID
from supabase import create_client, Client
from .models import Bot
from dotenv import load_dotenv

load_dotenv()

class BotDatabase:
    def __init__(self, storage_dir: str = "data"):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            print("[ATTENTION] Identifiants Supabase manquants.")
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)

    def _bot_to_db_dict(self, bot: Bot) -> Dict[str, Any]:
        """Map Bot model to Supabase table columns based on screenshot/requirements"""
        return {
            "id": str(bot.id),
            "name": bot.name,
            "description": bot.description,
            "domain": bot.domain,
            "export_json": bot.export_json
            # We skip 'capabilities', 'constraints', etc. as they are in export_json
        }

    def create_bot(self, bot: Bot) -> UUID:
        if self.client:
            data = self._bot_to_db_dict(bot)
            self.client.table("bots").insert(data).execute()
        return bot.id

    def get_bot(self, bot_id: str) -> Optional[Bot]:
        if self.client:
            response = self.client.table("bots").select("*").eq("id", str(bot_id)).execute()
            if response.data:
                db_data = response.data[0]
                # If export_json exists, we can reconstruct the full Bot model
                # or just use the fields we have.
                # For compatibility with RAG engine, we need the Bot model.
                
                # Check if we have enough info to reconstruct
                if "export_json" in db_data and db_data["export_json"]:
                    # Merge internal data from export_json if missing in top-level
                    export = db_data["export_json"]
                    if "configuration" in export:
                        db_data["configuration"] = export["configuration"]
                    if "constraints" in export:
                        db_data["constraints"] = export["constraints"]
                    if "capabilities" in export:
                        db_data["capabilities"] = export["capabilities"]
                
                return Bot(**db_data)
        return None

    def list_bots(self) -> List[Bot]:
        if self.client:
            response = self.client.table("bots").select("*").execute()
            return [Bot(**item) for item in response.data]
        return []

    def update_bot(self, bot: Bot):
        if self.client:
            data = self._bot_to_db_dict(bot)
            self.client.table("bots").update(data).eq("id", str(bot.id)).execute()

    def delete_bot(self, bot_id: str):
        if self.client:
            self.client.table("bots").delete().eq("id", str(bot_id)).execute()
