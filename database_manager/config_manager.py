import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class ConfigManager:
    def __init__(self):
        self._supabase = None
        self._current_url = None
        self._current_key = None

    @property
    def supabase(self) -> Client:
        # Load specifically for Management Project
        url = os.getenv("MANAGEMENT_SUPABASE_URL")
        key = os.getenv("MANAGEMENT_SUPABASE_KEY")
        
        if not url or not key:
            # Fallback for visibility (Optional, but helps user identify missing config)
            print("[ConfigManager] WARNING: MANAGEMENT_SUPABASE_URL or KEY missing in .env")
        
        if self._supabase is None or url != self._current_url or key != self._current_key:
            if url and key:
                self._supabase = create_client(url, key)
                self._current_url = url
                self._current_key = key
            else:
                # If credentials haven't been provided yet, return None or raise
                return None
            
        return self._supabase

    def save_config(self, chatbot_id, config_dict):
        """
        Save environment variables for a chatbot in a SINGLE ROW.
        EXCLUDES fixed infrastructure credentials as they are managed via deployment .env.
        ONLY saves dynamic/logic options: Models, Project Name, System Prompt, Document ID.
        """
        try:
            # Consolidate all dynamic values into one object
            full_config = {
                "OPENAI_MODEL": config_dict.get('OPENAI_MODEL', ''),
                "EMBEDDING_MODEL": config_dict.get('EMBEDDING_MODEL', ''),
                "PROJECT_NAME": config_dict.get('PROJECT_NAME', 'bot'),
                "SYSTEM_PROMPT": config_dict.get('SYSTEM_PROMPT', ''),
                "DOCUMENT_ID": config_dict.get('DOCUMENT_ID', '')
            }

            import json
            data = {
                "chatbot_id": chatbot_id,
                "env_key": "full_config", # Single key for everything
                "env_value": json.dumps(full_config),
                "is_secret": False
            }
            
            # Upsert based on unique constraint (chatbot_id, env_key)
            res = self.supabase.table("chatbot_env_configs").upsert(data, on_conflict="chatbot_id, env_key").execute()
            
            if res.data:
                return {"config": res.data[0]['id']}
            return {}
        except Exception as e:
            print(f"[ConfigManager] Error saving structured config: {e}")
            return None

    def test_connection(self):
        """Verify connection and check if the required table exists"""
        try:
            # Try to fetch just one record to see if table exists and is accessible
            self.supabase.table("chatbot_env_configs").select("id").limit(1).execute()
            return True, "Connection successful and table found!"
        except Exception as e:
            error_msg = str(e)
            if "PGRST204" in error_msg or "PGRST205" in error_msg or "not find the table" in error_msg:
                return False, "Table 'chatbot_env_configs' NOT found in your project."
            if "Invalid API key" in error_msg or "invalid-jwt" in error_msg:
                return False, "Invalid Supabase Service Key."
            return False, f"Connection error: {error_msg}"

    def get_config(self, chatbot_id):
        """Retrieve the single-row configuration for a chatbot"""
        try:
            response = self.supabase.table("chatbot_env_configs").select("*").eq("chatbot_id", chatbot_id).eq("env_key", "full_config").execute()
            config = {}
            import json
            if response.data:
                try:
                    # Parse the single JSON blob
                    item = response.data[0]
                    config = json.loads(item['env_value'])
                except Exception as e:
                    print(f"[ConfigManager] Error parsing JSON config: {e}")
            return config
        except Exception as e:
            print(f"[ConfigManager] Error retrieving config: {e}")
            return {}

# Singleton instance
_manager = None
def get_config_manager():
    global _manager
    if _manager is None:
        _manager = ConfigManager()
    return _manager
