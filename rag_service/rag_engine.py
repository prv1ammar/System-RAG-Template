import os
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredExcelLoader
)
import uuid
from pathlib import Path
from .models import Bot

class RAGEngine:
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def ingest_file(self, file_path: Path, bot_id: str, document_id: str = None) -> int:
        if document_id is None:
            document_id = str(uuid.uuid4())
        
        file_ext = file_path.suffix.lower()
        if file_ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif file_ext == ".docx":
            loader = Docx2txtLoader(str(file_path))
        elif file_ext in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path))

        raw_docs = loader.load()
        
        # Enforce metadata inheritance
        for doc in raw_docs:
            doc.metadata["bot_id"] = str(bot_id)
            doc.metadata["document_id"] = document_id

        chunks = self.text_splitter.split_documents(raw_docs)
        self.vector_store.add_documents(chunks)
        
        return len(chunks)

    def query(self, bot: Bot, question: str, top_k: int = 3) -> Dict[str, Any]:
        # Strict scope filtering
        filter_dict = {"bot_id": str(bot.id)}

        relevant_docs = self.vector_store.similarity_search(
            question, 
            k=top_k, 
            filter=filter_dict
        )

        if not relevant_docs:
            return {
                "answer": "Je ne trouve pas d'informations correspondantes dans ma base de connaissances pour ce bot.",
                "sources": [],
                "confidence": "low"
            }

        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        llm = ChatOpenAI(
            model=bot.configuration.model_name,
            temperature=bot.configuration.temperature
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are an assistant named {bot.name}. domain: {bot.domain}. tone: {bot.configuration.tone}."),
            ("system", f"Context:\n{{context}}\n\nReasoning: {bot.configuration.reasoning_level}.\nRule: Use ONLY the provided context. If unsure, say the information is unavailable."),
            ("human", "{question}")
        ])

        chain = prompt | llm
        response = chain.invoke({"context": context, "question": question})

        sources = []
        for doc in relevant_docs:
            sources.append({
                "document_id": doc.metadata.get("document_id", "unknown"),
                "page": doc.metadata.get("page")
            })

        confidence = "high" if len(relevant_docs) >= 2 else "medium"

        return {
            "answer": response.content,
            "sources": sources,
            "confidence": confidence
        }
