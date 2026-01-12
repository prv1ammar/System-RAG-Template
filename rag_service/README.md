# Portable RAG Service

This is a backend-first, LangChain-based RAG service designed for multi-tenant (multi-bot) AI systems.

## Key Features
- **Multi-Bot Isolation**: Each bot is identified by a unique `bot_id`. Documents and retrieval are strictly scoped.
- **Backend-First**: Pure JSON API using FastAPI.
- **Portability**: All configurations are stored in JSON, and the vector store is local.
- **Isolation**: Retrieval uses metadata filtering to ensure no cross-bot data leaks.

## Architecture
- `main.py`: FastAPI endpoints.
- `service.py`: Orchestration logic.
- `rag_engine.py`: LangChain pipeline (Loaders, Splitters, Chroma, OpenAI).
- `database.py`: Bot and document metadata storage.
- `models.py`: Pydantic schemas for API requests/responses.

## API Endpoints
- `POST /bots`: Create a new logical AI assistant.
- `POST /bots/{bot_id}/ingest`: Upload and index a document for a specific bot.
- `POST /bots/{bot_id}/ask`: Query the RAG system for a specific bot.
- `GET /bots/{bot_id}/export`: Export bot configuration and document metadata.

## Configuration
Le service nécessite une clé API OpenAI.
1. Copiez le fichier `.env.example` en `.env`.
2. Ajoutez votre clé : `OPENAI_API_KEY=sk-...`
3. Run the service:
   ```bash
   uvicorn rag_service.main:app --reload
   ```

## Export Example
The system supports exporting bot state as JSON, allowing for easy migration or integration into other systems.
