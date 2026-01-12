from langchain_core.prompts import ChatPromptTemplate

from agent_FAQ.prompt_agent_faq import FAQ_SYSTEM_PROMPT
from agent_FAQ.tools import retrieve_faq_context
from utils.llms import LLMModel

class FAQAgent:
    
    def __init__(self):
        self.llm = LLMModel().get_model()
        
        from langchain_core.messages import SystemMessage
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=FAQ_SYSTEM_PROMPT),
            ("human", "Context from knowledge base:\n{context}\n\nQuestion: {question}")
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
