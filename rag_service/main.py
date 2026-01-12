from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from .models import Bot, AskRequest, AskResponse, IngestResponse, BotExport
from .service import RAGService
import shutil
from pathlib import Path
import os
import uuid
from dotenv import load_dotenv
from .queue_manager import enqueue_rag_job

load_dotenv()

app = FastAPI(title="System RAG Platform API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
_service = RAGService()

def get_service():
    return _service

@app.post("/bots", response_model=Bot)
async def create_bot(bot_data: Bot, service: RAGService = Depends(get_service)):
    try:
        service.create_bot(bot_data.dict())
        return bot_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/bots/{bot_id}")
async def delete_bot_async(
    bot_id: str, 
    service: RAGService = Depends(get_service)
):
    try:
        job_id = enqueue_rag_job("DELETE_BOT", {"bot_id": bot_id})
        return {
            "status": "queued",
            "job_id": job_id,
            "message": "Bot deletion and data cleanup started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/reindex")
async def reindex_bot_async(
    bot_id: str, 
    service: RAGService = Depends(get_service)
):
    try:
        job_id = enqueue_rag_job("RE_EMBED_BOT", {"bot_id": bot_id})
        return {
            "status": "queued",
            "job_id": job_id,
            "message": "Bot re-indexing (embeddings update) started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/ingest")
async def ingest_document(
    bot_id: str, 
    file: UploadFile = File(...), 
    service: RAGService = Depends(get_service)
):
    try:
        # Create storage for temp files accessible by worker
        upload_dir = Path("data/temp_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Enqueue the ingestion job
        job_id = enqueue_rag_job("INGEST_DOCUMENT", {
            "bot_id": bot_id,
            "file_path": str(temp_path.absolute()),
            "document_id": str(hash(file.filename))
        })
        
        return {
            "status": "queued",
            "job_id": job_id,
            "bot_id": bot_id,
            "message": "Document ingestion started in background"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/ask", response_model=List[Dict[str, Any]])
async def ask_question(
    bot_id: str, 
    request: AskRequest, 
    service: RAGService = Depends(get_service)
):
    try:
        # Security: Cross-check bot_id from path and body
        if str(request.bot_id) != bot_id:
            raise HTTPException(status_code=400, detail="Bot ID mismatch between path and body")
            
        response = service.ask(bot_id, request)
        return response.messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/message", response_model=List[Dict[str, Any]])
async def send_message(
    bot_id: str, 
    request: AskRequest, 
    service: RAGService = Depends(get_service)
):
    """Alias for ask_question to satisfy 'send message' naming"""
    return await ask_question(bot_id, request, service)

@app.get("/bots/{bot_id}/export", response_model=BotExport)
async def export_bot(
    bot_id: str, 
    service: RAGService = Depends(get_service)
):
    try:
        return service.export_bot(bot_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
