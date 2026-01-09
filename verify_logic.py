import sys
from unittest.mock import MagicMock
import os
import shutil

# Mock streamlit
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

# Add current directory to path
sys.path.append(os.getcwd())

def test_generation():
    # Import app after mocking
    import app

    # Load real .env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test create_custom_chatbot with real config
    config = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL'),
        'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY'),
        'NAME_TABLE': os.getenv('NAME_TABLE'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'OPENAI_BASE_URL': os.getenv('OPENAI_BASE_URL'),
        'OPENAI_MODEL': os.getenv('OPENAI_MODEL'),
        'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL'),
        'QUERY_NAME': os.getenv('QUERY_NAME'),
        'SYSTEM_PROMPT': 'You are a helpful assistant.',
        'PROJECT_NAME': 'test_verification_bot'
    }

    output_dir = config['PROJECT_NAME']
    
    # Clean up previous run
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    print(f"Generating chatbot in {output_dir}...")
    success, result = app.create_custom_chatbot(config, output_dir=output_dir)

    if success:
        print(f"Successfully created chatbot in {result}")
        # Verify files exist
        files_to_check = [
            ".env",
            "agent_FAQ/__init__.py",
            "agent_FAQ/faq_agent.py",
            "agent_FAQ/prompt_agent_faq.py",
            "agent_FAQ/tools.py",
            "utils/__init__.py",
            "utils/llms.py",
            "test_chatbot.py",
            "README.md",
            "requirements.txt"
        ]
        all_exist = True
        missing = []
        for f in files_to_check:
            path = os.path.join(result, f)
            if not os.path.exists(path):
                print(f"Missing file: {f}")
                missing.append(f)
                all_exist = False
        
        if all_exist:
            print("All expected files created.")
            return True
        else:
            print(f"Verification failed due to missing files: {missing}")
            return False
    else:
        print(f"Failed to create chatbot: {result}")
        return False

if __name__ == "__main__":
    try:
        if test_generation():
            print("TEST PASSED")
            sys.exit(0)
        else:
            print("TEST FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
