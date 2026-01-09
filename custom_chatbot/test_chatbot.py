#!/usr/bin/env python3
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
    
    print("\nChatbot test completed!")
    print("To use your chatbot in your own code:")
    print("")
    print("from agent_FAQ.faq_agent import FAQAgent")
    print("")
    print("agent = FAQAgent()")
    print('answer = agent.run("Your question here")')
    print("print(answer)")

if __name__ == "__main__":
    test_chatbot()
