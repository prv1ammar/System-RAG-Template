import streamlit as st
import os
import json
from pathlib import Path
import shutil
import sys
import subprocess
import time
import importlib.util
from rag_service.service import RAGService

# Set page configuration
st.set_page_config(
    page_title="Chatbot Configuration Platform",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'config' not in st.session_state:
    st.session_state.config = {
        'SUPABASE_URL': '',
        'SUPABASE_SERVICE_KEY': '',
        'NAME_TABLE': '',
        'OPENAI_API_KEY': '',
        'OPENAI_BASE_URL': '',
        'OPENAI_MODEL': '',
        'EMBEDDING_MODEL': '',
        'QUERY_NAME': '',
        'SYSTEM_PROMPT': '',
        'PROJECT_NAME': 'custom_chatbot'
    }
if 'generated' not in st.session_state:
    st.session_state.generated = False

def save_config_to_env(config):
    """Save configuration to .env file"""
    env_content = f"""SUPABASE_URL="{config['SUPABASE_URL']}"
SUPABASE_SERVICE_KEY="{config['SUPABASE_SERVICE_KEY']}"
NAME_TABLE="{config['NAME_TABLE']}"

OPENAI_API_KEY="{config['OPENAI_API_KEY']}"
OPENAI_BASE_URL="{config['OPENAI_BASE_URL']}"
OPENAI_MODEL="{config['OPENAI_MODEL']}"
EMBEDDING_MODEL="{config['EMBEDDING_MODEL']}"
QUERY_NAME="{config['QUERY_NAME']}"
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    return True

def create_custom_chatbot(config, output_dir="custom_chatbot"):
    """Create a customized chatbot instance"""
    try:
        # Create output directory
        output_path = Path(output_dir)
        if output_path.exists():
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True)

        # Persistence: Register the bot in Supabase
        try:
            service = RAGService()
            bot_data = {
                "name": config.get('PROJECT_NAME', 'Custom Bot'),
                "description": f"RAG Bot for table {config.get('NAME_TABLE')}",
                "domain": "Enterprise RAG",
                "configuration": {
                    "default_language": "fr",
                    "response_format": "json",
                    "reasoning_level": "analytical",
                    "tone": "professional"
                }
            }
            service.create_bot(bot_data)
        except Exception as db_error:
            print(f"[UI] DB Persistence warning: {db_error}")
            # We continue even if DB fails to allow file generation
        
        # Create agent_FAQ directory
        agent_dir = output_path / "agent_FAQ"
        agent_dir.mkdir()
        
        # Create utils directory
        utils_dir = output_path / "utils"
        utils_dir.mkdir()
        
        # 1. Create .env file with user configuration
        env_content = f"""SUPABASE_URL="{config['SUPABASE_URL']}"
SUPABASE_SERVICE_KEY="{config['SUPABASE_SERVICE_KEY']}"
NAME_TABLE="{config['NAME_TABLE']}"

OPENAI_API_KEY="{config['OPENAI_API_KEY']}"
OPENAI_BASE_URL="{config['OPENAI_BASE_URL']}"
OPENAI_MODEL="{config['OPENAI_MODEL']}"
EMBEDDING_MODEL="{config['EMBEDDING_MODEL']}"
QUERY_NAME="{config['QUERY_NAME']}"
"""
        (output_path / ".env").write_text(env_content, encoding='utf-8')
        
        # 2. Create __init__.py files
        (agent_dir / "__init__.py").write_text("", encoding='utf-8')
        (utils_dir / "__init__.py").write_text("", encoding='utf-8')
        
        # 3. Create prompt_agent_faq.py with custom system prompt
        prompt_content = f'''FAQ_SYSTEM_PROMPT = """{config['SYSTEM_PROMPT']}"""
'''
        # Use UTF-8 encoding to handle special characters
        (agent_dir / "prompt_agent_faq.py").write_text(prompt_content, encoding='utf-8')
        
        # 4. Copy and modify faq_agent.py
        faq_agent_content = '''from langchain_core.prompts import ChatPromptTemplate

from agent_FAQ.prompt_agent_faq import FAQ_SYSTEM_PROMPT
from agent_FAQ.tools import retrieve_faq_context
from utils.llms import LLMModel

class FAQAgent:
    
    def __init__(self):
        self.llm = LLMModel().get_model()
        
        from langchain_core.messages import SystemMessage
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FAQ_SYSTEM_PROMPT),
            ("human", "Context from knowledge base:\\n{context}\\n\\nQuestion: {question}")
        ])
    
    def run(self, question: str) -> str:
       
        rag_result = retrieve_faq_context(question)
        
        
        if not rag_result["found"] or not rag_result["content"].strip():
            return "This information is not available in our knowledge base."
        
        
        response = self.llm.invoke(
            self.prompt.format_messages(
                context=rag_result["content"],
                question=question
            )
        )
        
        return response.content.strip()
'''
        (agent_dir / "faq_agent.py").write_text(faq_agent_content, encoding='utf-8')
        
        # 5. Copy and modify tools.py
        tools_content = f'''import os
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
        return {{"found": False, "content": ""}}
    
    try:
        # Initialize
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try with direct RPC call (Vector Search)
        try:
            query_embedding = embeddings.embed_query(question)
            
            params = {{
                "query_embedding": query_embedding,
                "match_threshold": 0.1,
                "match_count": top_k
            }}
            
            response = supabase.rpc(QUERY_NAME, params=params).execute()
            docs = response.data
            
            if not docs:
                print(f"[FAQ] No results for: {{question}}")
                return {{"found": False, "content": ""}}
            
            content_parts = []
            for doc in docs:
                if 'content' in doc and doc['content']:
                    content_parts.append(doc['content'])
                elif 'page_content' in doc and doc['page_content']:
                    content_parts.append(doc['page_content'])
                elif 'text' in doc and doc['text']:
                    content_parts.append(doc['text'])
            
            content = "\\n\\n".join(content_parts)
            print(f"[FAQ] Found {{len(docs)}} documents via vector search for: {{question}}")
            return {{"found": True, "content": content}}
            
        except Exception as vector_error:
            print(f"[FAQ] Vector search error: {{vector_error}}")
            print("[FAQ] Trying direct Supabase query (fallback)...")
            
            # Fallback to direct Supabase query (fetch recent/top rows)
            try:
                # Simple direct query to Supabase table
                # Note: This is not semantic search, just fetching rows
                response = supabase.table(TABLE_NAME).select("*").limit(top_k).execute()
                
                if not response.data:
                    print(f"[FAQ] No documents found in table: {{TABLE_NAME}}")
                    return {{"found": False, "content": ""}}
                
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
                    return {{"found": False, "content": ""}}
                
                content = "\\n\\n".join(content_parts[:top_k])
                print(f"[FAQ] Found {{len(content_parts)}} documents via direct query for: {{question}}")
                return {{"found": True, "content": content}}
                
            except Exception as direct_error:
                print(f"[FAQ] Direct query error: {{direct_error}}")
                return {{"found": False, "content": ""}}
        
    except Exception as e:
        print(f"[FAQ] General error: {{e}}")
        return {{"found": False, "content": ""}}
'''
        (agent_dir / "tools.py").write_text(tools_content, encoding='utf-8')
        
        # 6. Copy and modify llms.py
        llms_content = '''import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


class LLMModel:
    def get_model(self):
        model = os.getenv("OPENAI_MODEL")
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")

        
        if not model:
            raise ValueError("OPENAI_MODEL is missing in .env")
        if not base_url:
            raise ValueError("OPENAI_BASE_URL is missing in .env")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing in .env")

        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=0
        )
'''
        (utils_dir / "llms.py").write_text(llms_content, encoding='utf-8')
        
        # 7. Create a simple test script
        test_content = '''#!/usr/bin/env python3
import sys
import os
# Force UTF-8 encoding for Windows consoles
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_FAQ.faq_agent import FAQAgent

def test_chatbot():
    """Test the generated chatbot"""
    print("Testing your custom chatbot...")
    print("=" * 50)
    
    agent = FAQAgent()
    
    # Test questions
    test_questions = [
        "What services do you offer?",
        "How can I contact support?",
        "What are your business hours?"
    ]
    
    for question in test_questions:
        print(f"Q: {question}")
        answer = agent.run(question)
        print(f"A: {answer}")
        print("-" * 50)
    
    print("\\nChatbot test completed!")
    print("To use your chatbot in your own code:")
    print("")
    print("from agent_FAQ.faq_agent import FAQAgent")
    print("")
    print("agent = FAQAgent()")
    print('answer = agent.run("Your question here")')
    print("print(answer)")

if __name__ == "__main__":
    test_chatbot()
'''
        (output_path / "test_chatbot.py").write_text(test_content, encoding='utf-8')
        
        # 8. Create README
        readme_content = f'''# Custom Chatbot Instance

This is your custom RAG chatbot instance generated by the Chatbot Configuration Platform.

## Configuration
- **Supabase URL**: {config['SUPABASE_URL'][:30]}...
- **Supabase Table**: {config['NAME_TABLE']}
- **OpenAI Model**: {config['OPENAI_MODEL']}

## Files Structure
```
custom_chatbot/
├── .env                    # Environment variables
├── agent_FAQ/
│   ├── __init__.py
│   ├── faq_agent.py       # Main agent class
│   ├── prompt_agent_faq.py # Custom system prompt
│   └── tools.py           # Supabase retrieval
├── utils/
│   ├── __init__.py
│   └── llms.py            # OpenAI client
├── test_chatbot.py        # Test script
└── README.md              # This file
```

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Test your chatbot:
```bash
python test_chatbot.py
```

3. Use in your own code:
```python
from agent_FAQ.faq_agent import FAQAgent

agent = FAQAgent()
answer = agent.run("Your question here")
print(answer)
```

## Requirements
Create a `requirements.txt` file with:
```
streamlit>=1.28.0
langchain>=0.1.0
langchain-openai>=0.0.5
supabase>=2.3.0
python-dotenv>=1.0.0
```

## Custom Prompt
Your custom system prompt has been configured in `agent_FAQ/prompt_agent_faq.py`.
'''
        (output_path / "README.md").write_text(readme_content, encoding='utf-8')
        
        # 9. Create requirements.txt
        requirements_content = '''streamlit>=1.28.0
langchain>=0.1.0
langchain-openai>=0.0.5
supabase>=2.3.0
python-dotenv>=1.0.0
'''
        (output_path / "requirements.txt").write_text(requirements_content, encoding='utf-8')
        
        return True, output_dir
        
    except Exception as e:
        return False, str(e)

# Page rendering functions
def render_home():
    st.title("🤖 Chatbot Configuration Platform")
    st.markdown("""
    ## Welcome to the RAG Agent Chatbot Configuration Platform
    
    This platform allows you to configure and generate your own custom RAG (Retrieval-Augmented Generation) chatbot
    that retrieves answers from your knowledge base stored in Supabase.
    
    ### How it works:
    1. **Configure** your Supabase connection and OpenAI settings
    2. **Customize** your chatbot's system prompt
    3. **Generate** your personalized chatbot instance
    4. **Use** your chatbot in your own applications
    
    ### What you'll need:
    - Supabase URL and Service Key
    - Name of your documents table
    - OpenAI API Key, Base URL, and Model
    - A system prompt for your chatbot
    """)
    
    if st.button("🚀 Start Configuration", type="primary", use_container_width=True):
        st.session_state.page = 'config'
        st.rerun()

def render_config():
    st.title("⚙️ Chatbot Configuration")
    st.markdown("Configure your Supabase connection and OpenAI settings below.")
    
    with st.form("config_form"):
        st.subheader("Supabase Configuration")
        supabase_url = st.text_input(
            "SUPABASE_URL",
            value=st.session_state.config['SUPABASE_URL'],
            placeholder="https://your-project.supabase.co",
            help="Your Supabase project URL"
        )
        
        supabase_key = st.text_input(
            "SUPABASE_SERVICE_KEY",
            value=st.session_state.config['SUPABASE_SERVICE_KEY'],
            type="password",
            placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            help="Your Supabase service role key (keep this secret!)"
        )
        
        table_name = st.text_input(
            "NAME_TABLE",
            value=st.session_state.config['NAME_TABLE'],
            placeholder="documents",
            help="Name of your Supabase table containing documents"
        )

        st.subheader("Project Configuration")
        project_name = st.text_input(
            "PROJECT_NAME (Chatbot Name)",
            value=st.session_state.config.get('PROJECT_NAME', 'custom_chatbot'),
            placeholder="my_finance_bot",
            help="Unique name for your chatbot project (folder name)"
        )
        
        st.subheader("OpenAI Configuration")
        openai_key = st.text_input(
            "OPENAI_API_KEY",
            value=st.session_state.config['OPENAI_API_KEY'],
            type="password",
            placeholder="sk-...",
            help="Your OpenAI API key"
        )
        
        openai_base = st.text_input(
            "OPENAI_BASE_URL",
            value=st.session_state.config['OPENAI_BASE_URL'],
            placeholder="https://api.openai.com/v1",
            help="OpenAI API base URL (default: https://api.openai.com/v1)"
        )
        
        openai_model = st.text_input(
            "OPENAI_MODEL",
            value=st.session_state.config['OPENAI_MODEL'],
            placeholder="gpt-3.5-turbo",
            help="OpenAI model name (e.g., gpt-3.5-turbo, gpt-4)"
        )
        
        embedding_model = st.text_input(
            "EMBEDDING_MODEL",
            value=st.session_state.config['EMBEDDING_MODEL'],
            placeholder="text-embedding-3-small",
            help="OpenAI embedding model name (e.g., text-embedding-3-small, text-embedding-ada-002)"
        )
        
        query_name = st.text_input(
            "QUERY_NAME",
            value=st.session_state.config['QUERY_NAME'],
            placeholder="match_documents",
            help="Supabase query function name for vector search"
        )
        
        st.subheader("Chatbot Prompt Configuration")
        system_prompt = st.text_area(
            "SYSTEM_PROMPT",
            value=st.session_state.config['SYSTEM_PROMPT'],
            placeholder="Enter your custom system prompt here...",
            height=200,
            help="System prompt that defines your chatbot's behavior and rules"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("⬅️ Back to Home"):
                st.session_state.page = 'home'
                st.rerun()
        
        with col2:
            if st.form_submit_button("Next ➡️", type="primary"):
                # Save configuration
                st.session_state.config = {
                    'SUPABASE_URL': supabase_url.strip(),
                    'SUPABASE_SERVICE_KEY': supabase_key.strip(),
                    'NAME_TABLE': table_name.strip(),
                    'OPENAI_API_KEY': openai_key.strip(),
                    'OPENAI_BASE_URL': openai_base.strip(),
                    'OPENAI_MODEL': openai_model.strip(),
                    'EMBEDDING_MODEL': embedding_model.strip(),
                    'QUERY_NAME': query_name.strip(),
                    'SYSTEM_PROMPT': system_prompt,
                    'PROJECT_NAME': project_name.strip().replace(" ", "_") # Basic sanitization
                }
                
                # Save to .env file
                save_config_to_env(st.session_state.config)
                
                st.session_state.page = 'generate'
                st.rerun()

def render_generate():
    st.title("🚀 Generate Your Chatbot")
    st.markdown("Review your configuration and generate your custom chatbot instance.")
    
    # Display configuration summary
    st.subheader("Configuration Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Supabase Settings**")
        st.write(f"URL: `{st.session_state.config['SUPABASE_URL'][:50]}...`" if len(st.session_state.config['SUPABASE_URL']) > 50 else f"URL: `{st.session_state.config['SUPABASE_URL']}`")
        st.write(f"Table: `{st.session_state.config['NAME_TABLE']}`")
        
    with col2:
        st.markdown("**OpenAI Settings**")
        st.write(f"Model: `{st.session_state.config['OPENAI_MODEL']}`")
        st.write(f"Base URL: `{st.session_state.config['OPENAI_BASE_URL']}`")
        st.write(f"API Key: `{'*' * 20}{st.session_state.config['OPENAI_API_KEY'][-4:] if st.session_state.config['OPENAI_API_KEY'] else ''}`")
    
    st.subheader("System Prompt Preview")
    with st.expander("View your custom system prompt"):
        st.code(st.session_state.config['SYSTEM_PROMPT'], language="markdown")
    
    st.divider()
    
    # Generation section
    st.subheader("Generate Your Chatbot")
    
    if st.button("🚀 Start Generation", type="primary", use_container_width=True):
        project_name = st.session_state.config.get('PROJECT_NAME', 'custom_chatbot')
        with st.spinner(f"Generating chatbot '{project_name}'..."):
            success, result = create_custom_chatbot(st.session_state.config, output_dir=project_name)
            
            if success:
                st.session_state.generated = True
                st.session_state.auto_setup_pending = True
                st.success(f"✅ Chatbot generated successfully in directory: `{result}/`")
                
                st.markdown("### 🎉 Your Chatbot is Ready!")
                st.markdown(f"""
                Your custom RAG chatbot has been generated in the `{result}/` directory.
                
                **Next Steps:**
                1. **Navigate to the directory:**
                   ```bash
                   cd {result}
                   ```
                2. **Install dependencies:**
                   ```bash
                   pip install -r requirements.txt
                   ```
                3. **Test your chatbot:**
                   ```bash
                   python test_chatbot.py
                   ```
                4. **Use in your own code:**
                   ```python
                   from agent_FAQ.faq_agent import FAQAgent
                   
                   agent = FAQAgent()
                   answer = agent.run("Your question here")
                   print(answer)
                   ```
                
                **Files Generated:**
                - `.env` - Your configuration
                - `agent_FAQ/` - Chatbot agent code
                - `utils/` - Utility functions
                - `test_chatbot.py` - Test script
                - `README.md` - Documentation
                - `requirements.txt` - Dependencies
                """)
                
                # Offer download option
                st.download_button(
                    label="📥 Download Chatbot as ZIP",
                    data=open(f"{result}.zip", "rb").read() if os.path.exists(f"{result}.zip") else b"",
                    file_name=f"{result}.zip",
                    mime="application/zip",
                    disabled=not os.path.exists(f"{result}.zip")
                )
            else:
                st.error(f"❌ Failed to generate chatbot: {result}")

def render_test_interface():
    st.title("💬 Test Your Chatbot")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask your chatbot something..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        try:
            # Dynamic import of the agent
            if 'agent_instance' not in st.session_state:
                project_name = st.session_state.config.get('PROJECT_NAME', 'custom_chatbot')
                agent_path = os.path.join(os.getcwd(), project_name, 'agent_FAQ', 'faq_agent.py')
                
                # Use importlib to load module from path
                spec = importlib.util.spec_from_file_location("faq_agent", agent_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules["faq_agent"] = module
                spec.loader.exec_module(module)
                
                st.session_state.agent_instance = module.FAQAgent()
            
            with st.spinner("Thinking..."):
                response = st.session_state.agent_instance.run(prompt)
                
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            st.error("Please make sure the chatbot was generated successfully and dependencies are installed.")

def automate_setup(output_dir):
    """Automate dependency installation and testing"""
    status_container = st.empty()
    
    with status_container.container():
        st.info("🛠️ Setting up your chatbot environment...")
        
        # 1. Install dependencies
        progress_text = "Installing dependencies..."
        my_bar = st.progress(0, text=progress_text)
        
        try:
            # Install in current environment for instant testing
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", os.path.join(output_dir, "requirements.txt")])
            my_bar.progress(50, text="Dependencies installed! Running self-test...")
            
            # 2. Run test script
            result = subprocess.run(
                [sys.executable, os.path.join(output_dir, "test_chatbot.py")], 
                capture_output=True, 
                text=True, 
                encoding='utf-8' # Force utf-8 for capturing output
            )
            
            if result.returncode == 0:
                my_bar.progress(100, text="Self-test passed!")
                time.sleep(1)
                st.success("✅ Setup complete! Redirecting to chat...")
                time.sleep(1)
                return True
            else:
                st.error("❌ Self-test failed prior to chat.")
                st.code(result.stderr)
                return False
                
        except Exception as e:
            st.error(f"❌ Automation failed: {e}")
            return False

# Main app logic
def main():
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        st.divider()
        
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
        st.markdown("### About")
        st.markdown("""
        This platform helps you create custom RAG chatbots that retrieve answers from your Supabase knowledge base.
        
        **Features:**
        - Configure Supabase connection
        - Set OpenAI parameters
        - Customize system prompt
        - Generate ready-to-use chatbot
        """)
    
    # Render current page
    if st.session_state.page == 'home':
        render_home()
    elif st.session_state.page == 'config':
        render_config()
    elif st.session_state.page == 'generate':
        render_generate()
         # Check if generation was triggered and successful, then run automation
        if st.session_state.get('generated', False) and st.session_state.get('auto_setup_pending', True):
             project_name = st.session_state.config.get('PROJECT_NAME', 'custom_chatbot')
             if automate_setup(project_name):
                 st.session_state.auto_setup_pending = False
                 st.session_state.page = 'test_interface'
                 st.rerun()
                 
    elif st.session_state.page == 'test_interface':
        render_test_interface()

if __name__ == "__main__":
    main()
