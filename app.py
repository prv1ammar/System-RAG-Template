import streamlit as st
import os
import json
from pathlib import Path
import shutil
import sys
import subprocess
import time
import importlib.util
from datetime import datetime
import uuid
from database_manager.config_manager import get_config_manager
from dotenv import load_dotenv

# 🌍 LOAD ENV & SET PAGE CONFIG
load_dotenv()

st.set_page_config(
    page_title="Chatbot Configuration Platform",
    page_icon="🤖",
    layout="wide"
)

# 🔒 PRE-CONFIGURED CREDENTIALS (Loaded from .env, not user-configurable)
# All sensitive and structural configuration is managed via environment variables
FIXED_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
FIXED_SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
FIXED_NAME_TABLE = os.getenv("NAME_TABLE", "documents")
FIXED_QUERY_NAME = os.getenv("QUERY_NAME", "match_documents")
FIXED_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FIXED_OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# 🛡️ ROBUST SESSION STATE INITIALIZATION
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if 'config' not in st.session_state:
    st.session_state.config = {
        'SUPABASE_URL': FIXED_SUPABASE_URL,
        'SUPABASE_SERVICE_KEY': FIXED_SUPABASE_SERVICE_KEY,
        'NAME_TABLE': FIXED_NAME_TABLE,
        'OPENAI_API_KEY': FIXED_OPENAI_API_KEY,
        'OPENAI_BASE_URL': FIXED_OPENAI_BASE_URL,
        'OPENAI_MODEL': 'gpt-4.1-mini',
        'EMBEDDING_MODEL': 'text-embedding-3-small',
        'QUERY_NAME': FIXED_QUERY_NAME,
        'SYSTEM_PROMPT': '',
        'PROJECT_NAME': 'custom_chatbot',
        'DOCUMENT_ID': ''
    }

if 'generated' not in st.session_state:
    st.session_state.generated = False

DEFAULT_SYSTEM_PROMPT = """You are a professional multilingual FAQ assistant.
Your goal is to provide accurate, clear, and warm responses based ONLY on the provided context.

🌍 LANGUAGE RULES:
1. Detect the user's language (Arabic, English, French, or Moroccan Darija).
2. ALWAYS respond in the same language as the user.
3. If unsure, default to French.

🎯 RESPONSE RULES:
1. Use ONLY the retrieved context. Never invent information.
2. If the answer is not in the context, respond politely:
   - FR: "Désolé, je n'ai pas trouvé cette information dans ma base de connaissances. 😊"
   - EN: "I couldn't find that information in my knowledge base right now. 😊"
   - AR: "عذراً، لم أجد هذه المعلومة في قاعدة بياناتي حالياً. 😊"
   - Darija: "Hhh ma l9itch had lma3louma daba f l'base dyali. 😊"
3. Keep answers concise and factual.
4. Avoid medical, legal, or personal booking advice."""

if not st.session_state.config.get('SYSTEM_PROMPT'):
    st.session_state.config['SYSTEM_PROMPT'] = DEFAULT_SYSTEM_PROMPT

def save_config_to_env(config):
    """Save bot-specific form configuration to a separate file"""
    config_path = Path(".platform_bot_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    return True

def load_platform_config():
    """Load bot-specific form configuration from the separate file"""
    config_path = Path(".platform_bot_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return None

class UniversalRAGAgent:
    """A RAG Agent that works purely from a configuration dictionary, no local folders needed."""
    def __init__(self, config):
        self.config = config
        # Hardening for LangChain sync client - fallback to os.getenv for fixed credentials
        self.openai_api_key = str(config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY', '')).strip()
        self.openai_base_url = str(config.get('OPENAI_BASE_URL') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')).strip()
        self.openai_model = str(config.get('OPENAI_MODEL', 'gpt-4.1-mini')).strip()
        self.embedding_model = str(config.get('EMBEDDING_MODEL', 'text-embedding-3-small')).strip()
        self.supabase_url = str(config.get('SUPABASE_URL') or os.getenv('SUPABASE_URL', '')).strip()
        self.supabase_key = str(config.get('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_SERVICE_KEY', '')).strip()
        self.table_name = str(config.get('NAME_TABLE') or os.getenv('NAME_TABLE', '')).strip()
        self.query_name = str(config.get('QUERY_NAME') or os.getenv('QUERY_NAME', 'match_documents')).strip()
        self.system_prompt = str(config.get('SYSTEM_PROMPT') or DEFAULT_SYSTEM_PROMPT).strip()
        self.document_id = str(config.get('DOCUMENT_ID') or os.getenv('DOCUMENT_ID', '')).strip()

    def run(self, question: str) -> str:
        if not self.openai_api_key: return "❌ OpenAI API Key is missing."
        try:
            from langchain_openai import OpenAIEmbeddings, ChatOpenAI
            from supabase import create_client
            
            embeddings = OpenAIEmbeddings(model=self.embedding_model, api_key=self.openai_api_key, openai_api_base=self.openai_base_url)
            query_embedding = embeddings.embed_query(str(question))
            supabase = create_client(self.supabase_url, self.supabase_key)
            
            bot_id = self.config.get('botID')
            document_id = self.document_id
            
            fallback_params = [
                # New standard: Filter by document_id
                {"query_embedding": query_embedding, "match_threshold": 0.1, "match_count": 3, "p_document_id": document_id} if document_id else None,
                # Legacy: Filter by bot_id
                {"query_embedding": query_embedding, "match_threshold": 0.1, "match_count": 3, "p_bot_id": bot_id} if bot_id else None,
                # Fallback: No filter
                {"query_embedding": query_embedding, "match_threshold": 0.1, "match_count": 3},
                {"query_embedding": query_embedding, "match_count": 3},
                {"query_embedding": query_embedding}
            ]
            
            response = None
            for p_set in [p for p in fallback_params if p is not None]:
                try:
                    response = supabase.rpc(self.query_name, params=p_set).execute()
                    break 
                except Exception as e:
                    if any(code in str(e) for code in ["42804", "PGRST202", "p_bot_id"]): continue
                    raise e
                    
            if response is None: return "Connection failed."
            if not response.data: return "No relevant information found. 😊"

            context = "\n\n".join([str(doc.get('content', doc.get('page_content', ''))) for doc in response.data])
            llm = ChatOpenAI(api_key=self.openai_api_key, base_url=self.openai_base_url, model=self.openai_model, temperature=0)
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.messages import SystemMessage
            prompt_template = ChatPromptTemplate.from_messages([SystemMessage(content=self.system_prompt), ("human", f"Context:\n{context}\n\nQuestion: {question}")])
            return llm.invoke(prompt_template.format_messages()).content.strip()
        except Exception as e: return f"Error: {str(e)}"

def create_custom_chatbot_streamlined(config):
    """Streamlined build: JSON shell + Supabase + n8n workflow.json"""
    bot_id = str(uuid.uuid4())
    try:
        mgr = get_config_manager()
        db_ids = mgr.save_config(bot_id, config)
        if not db_ids: return False, "Database error"

        final_dir = Path("chatbot_final")
        final_dir.mkdir(exist_ok=True)
        
        # Create bot configuration JSON
        chatbot_data = {
            "botID": bot_id,
            "project_name": config.get('PROJECT_NAME', 'bot'),
            "generated_at": datetime.now().isoformat(),
            "openai_id": db_ids.get('openai'),
            "supabase_id": db_ids.get('supabase'),
            "configuration": {"source": "supabase_managed"}
        }
        (final_dir / f"{config['PROJECT_NAME']}_{bot_id[:8]}.json").write_text(json.dumps(chatbot_data, indent=2), encoding='utf-8')
        
        # Create n8n-style workflow.json with LangChain nodes
        workflow_data = {
            "nodes": [
                {
                    "parameters": {
                        "promptType": "define",
                        "text": f"# System Prompt (Bot ID: {bot_id})\n# Managed centrally in Supabase\n# Fetch from chatbot_env_configs table using botID",
                        "options": {}
                    },
                    "id": str(uuid.uuid4()),
                    "name": "AI Agent",
                    "type": "@n8n/n8n-nodes-langchain.agent",
                    "typeVersion": 1.3,
                    "position": [1856, 3024]
                },
                {
                    "parameters": {
                        "model": config.get('EMBEDDING_MODEL', 'text-embedding-3-small'),
                        "options": {}
                    },
                    "id": str(uuid.uuid4()),
                    "name": "OpenAI Embeddings",
                    "type": "@n8n/n8n-nodes-langchain.embeddingsOpenAi",
                    "typeVersion": 1,
                    "position": [2256, 3424]
                },
                {
                    "parameters": {
                        "mode": "retrieve-as-tool",
                        "tableName": {
                            "__rl": True,
                            "value": config.get('NAME_TABLE', 'documents'),
                            "mode": "list",
                            "cachedResultName": config.get('NAME_TABLE', 'documents')
                        },
                        "options": {}
                    },
                    "id": str(uuid.uuid4()),
                    "name": "Supabase Vector Store",
                    "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
                    "typeVersion": 1.3,
                    "position": [2064, 3216],
                    "credentials": {
                        "supabaseApi": {
                            "id": bot_id[:16],
                            "name": f"Supabase - {config.get('PROJECT_NAME', 'bot')}"
                        }
                    }
                },
                {
                    "parameters": {
                        "model": config.get('OPENAI_MODEL', 'gpt-4.1-mini'),
                        "options": {}
                    },
                    "id": str(uuid.uuid4()),
                    "name": "OpenAI Chat Model",
                    "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "typeVersion": 1,
                    "position": [2064, 3024]
                }
            ],
            "connections": {
                "OpenAI Embeddings": {
                    "ai_embedding": [
                        [
                            {
                                "node": "Supabase Vector Store",
                                "type": "ai_embedding",
                                "index": 0
                            }
                        ]
                    ]
                },
                "Supabase Vector Store": {
                    "ai_tool": [
                        [
                            {
                                "node": "AI Agent",
                                "type": "ai_tool",
                                "index": 0
                            }
                        ]
                    ]
                },
                "OpenAI Chat Model": {
                    "ai_languageModel": [
                        [
                            {
                                "node": "AI Agent",
                                "type": "ai_languageModel",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "pinData": {},
            "meta": {
                "templateCredsSetupCompleted": True,
                "instanceId": bot_id
            }
        }
        
        (final_dir / f"workflow_{config['PROJECT_NAME']}_{bot_id[:8]}.json").write_text(json.dumps(workflow_data, indent=2), encoding='utf-8')
        
        return True, bot_id
    except Exception as e: return False, str(e)

# --- Original Visual Design Pages ---

def render_home():
    st.title("🤖 Chatbot Configuration Platform")
    st.markdown("""
    ## Welcome to the RAG Agent Chatbot Configuration Platform
    
    This platform allows you to generate your own custom RAG (Retrieval-Augmented Generation) chatbot
    with just a few clicks - all infrastructure is pre-configured!
    
    ### How it works:
    1. **Select** your preferred AI models
    2. **Generate** your chatbot instance
    3. **Deploy** and use immediately
    
    The platform automatically provides:
    - ✅ Optimized multilingual system prompt
    - ✅ Pre-configured Supabase connection
    - ✅ Secure API access
    - ✅ N8N workflow export
    
    ### What you configure:
    - Project name
    - OpenAI chat model (gpt-4.1-mini, gpt-4, etc.)
    - Embedding model (text-embedding-3-small, etc.)
    """)
    if st.button("🚀 Start Configuration", type="primary", use_container_width=True):
        st.session_state.page = 'config'
        st.rerun()

def render_config():
    st.title("⚙️ AI Model Configuration")
    st.markdown("Select the AI models for your chatbot. All other settings are pre-configured.")
    
    st.info("🔒 **Pre-configured Settings:**\n- Supabase connection\n- OpenAI API access\n- Document table and query settings")
    
    with st.form("config_form"):
        st.subheader("Project Configuration")
        project_name = st.text_input(
            "Chatbot Name", 
            value=st.session_state.config.get('PROJECT_NAME', 'custom_chatbot'),
            help="A unique name for your chatbot project"
        )
        
        document_id = st.text_input(
            "Document ID (Foreign Key)",
            value=st.session_state.config.get('DOCUMENT_ID', ''),
            help="The foreign key ID to filter documents for this specific chatbot context."
        )
        
        st.subheader("AI Model Selection")
        openai_model = st.selectbox(
            "OpenAI Chat Model",
            options=['gpt-4.1-mini', 'gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
            index=0,
            help="The language model for generating responses"
        )
        
        embedding_model = st.selectbox(
            "Embedding Model",
            options=['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'],
            index=0,
            help="The model for creating vector embeddings"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("⬅️ Back to Home"):
                st.session_state.page = 'home'
                st.rerun()
        with col2:
            if st.form_submit_button("Next ➡️", type="primary"):
                st.session_state.config.update({
                    'OPENAI_MODEL': openai_model,
                    'EMBEDDING_MODEL': embedding_model,
                    'PROJECT_NAME': project_name.strip().replace(" ", "_"),
                    'DOCUMENT_ID': document_id.strip(),
                    'SYSTEM_PROMPT': DEFAULT_SYSTEM_PROMPT
                })
                save_config_to_env(st.session_state.config)
                st.session_state.page = 'generate'
                st.rerun()

def render_generate():
    st.title("🚀 Generate Your Chatbot")
    st.markdown("Review your configuration and generate your custom chatbot instance.")
    
    st.subheader("Configuration Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Supabase Settings**")
        st.write(f"URL: `{st.session_state.config['SUPABASE_URL'][:30]}...`")
        st.write(f"Table: `{st.session_state.config['NAME_TABLE']}`")
    with col2:
        st.markdown("**OpenAI Settings**")
        st.write(f"Model: `{st.session_state.config['OPENAI_MODEL']}`")
        st.write(f"API Key: `{'*' * 15}`")
    
    with st.expander("View System Prompt"):
        st.code(st.session_state.config['SYSTEM_PROMPT'], language="markdown")
    
    st.divider()
    
    if st.button("🚀 Start Generation", type="primary", use_container_width=True):
        with st.spinner("Saving configuration to cloud..."):
            success, result = create_custom_chatbot_streamlined(st.session_state.config)
            if success:
                st.session_state.generated = True
                st.success(f"✅ Chatbot configuration successfully created!")
                st.markdown("### 🎉 Ready!")
                st.markdown(f"""
                Your bot is now saved in Supabase and `chatbot_final/`. 
                
                **Generated Files:**
                - `{st.session_state.config['PROJECT_NAME']}_{result[:8]}.json` - Bot configuration shell
                - `workflow_{st.session_state.config['PROJECT_NAME']}_{result[:8]}.json` - n8n workflow file
                
                The workflow.json can be imported directly into n8n for automation!
                """)
                if st.button("💬 Open Test Chat", use_container_width=True):
                    st.session_state.page = 'test_interface'
                    st.rerun()
            else:
                st.error(f"❌ Failed: {result}")
    
    if st.button("⬅️ Back to Config"):
        st.session_state.page = 'config'
        st.rerun()

def render_test_interface():
    st.title("💬 Test Your Chatbot")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
    if prompt := st.chat_input("Ask your chatbot something..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Thinking..."):
            agent = UniversalRAGAgent(st.session_state.config)
            response = agent.run(prompt)
            
        with st.chat_message("assistant"): st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    if st.button("⬅️ Back to Generate"):
        st.session_state.page = 'generate'
        st.rerun()

def render_fleet_tester():
    st.title("🚢 Fleet Tester")
    final_dir = Path("chatbot_final")
    bots = [f for f in final_dir.glob("*.json") if not f.name.startswith("workflow_")] if final_dir.exists() else []
    if not bots:
        st.info("No chatbots found.")
        return
    selected_bot = st.selectbox("Select bot", [f.name for f in bots])
    if selected_bot:
        with open(final_dir / selected_bot, 'r', encoding='utf-8') as f:
            bot_config = json.load(f)
        
        if 'tester_agent' not in st.session_state or st.session_state.get('current_tester_id') != bot_config.get('botID'):
            with st.spinner("Fetching cloud config..."):
                mgr = get_config_manager()
                cloud_config = mgr.get_config(bot_config.get('botID'))
                full_config = {**cloud_config, 'botID': bot_config.get('botID')}
                st.session_state.tester_agent = UniversalRAGAgent(full_config)
                st.session_state.current_tester_id = bot_config.get('botID')
                st.session_state.tester_messages = []
        
        for msg in st.session_state.tester_messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Message fleet bot..."):
            st.session_state.tester_messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            resp = st.session_state.tester_agent.run(prompt)
            st.chat_message("assistant").markdown(resp)
            st.session_state.tester_messages.append({"role": "assistant", "content": resp})

# --- Sidebar & Main ---

def main():
    if 'config_loaded' not in st.session_state:
        saved = load_platform_config()
        if saved: st.session_state.config.update(saved)
        st.session_state.config_loaded = True

    with st.sidebar:
        st.title("Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'home'
            st.rerun()
        if st.button("⚙️ Configuration", use_container_width=True):
            st.session_state.page = 'config'
            st.rerun()
        if st.button("🚀 Generate", use_container_width=True):
            st.session_state.page = 'generate'
            st.rerun()
        st.divider()
        if st.button("💬 Test Current", use_container_width=True):
            st.session_state.page = 'test_interface'
            st.rerun()
        if st.button("🚢 Fleet Tester", use_container_width=True):
            st.session_state.page = 'fleet'
            st.rerun()

    if st.session_state.page == 'home': render_home()
    elif st.session_state.page == 'config': render_config()
    elif st.session_state.page == 'generate': render_generate()
    elif st.session_state.page == 'test_interface': render_test_interface()
    elif st.session_state.page == 'fleet': render_fleet_tester()

if __name__ == "__main__":
    main()
