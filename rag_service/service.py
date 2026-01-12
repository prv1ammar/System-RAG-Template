from typing import Dict, Any, List, Optional
from pathlib import Path
import os
from datetime import datetime
from uuid import UUID
from .database import BotDatabase
from .rag_engine import RAGEngine
from .models import Bot, AskRequest, AskResponse, IngestResponse, Source, BotExport, ConfidenceLevel

class MessageHandler:
    @staticmethod
    def text(content: str) -> Dict[str, Any]:
        return {"type": "text", "text": content}

    @staticmethod
    def image(url: str) -> Dict[str, Any]:
        return {"type": "image", "image": url}

    @staticmethod
    def audio(url: str) -> Dict[str, Any]:
        return {"type": "audio", "audio": url}

    @staticmethod
    def video(url: str) -> Dict[str, Any]:
        return {"type": "video", "video": url}

    @staticmethod
    def document(url: str, title: str) -> Dict[str, Any]:
        return {"type": "document", "document": url, "title": title}

    @staticmethod
    def choices(text: str, title: str, choices: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "type": "single-choice",
            "text": text,
            "title": title,
            "choices": choices
        }

    @staticmethod
    def card(title: str, subtitle: str, image_url: str, actions: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "type": "card",
            "title": title,
            "subtitle": subtitle,
            "image": image_url,
            "actions": actions
        }

class RAGService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.temp_dir = self.data_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.db = BotDatabase(str(self.data_dir))
        self.engine = RAGEngine(str(self.data_dir / "chroma_db"))
        self.handler = MessageHandler()

    def create_bot(self, bot_data: Dict[str, Any]) -> UUID:
        bot = Bot(**bot_data)
        # Generate the standardized export JSON immediately
        bot.export_json = self._generate_export_data(bot).dict()
        return self.db.create_bot(bot)

    def _generate_export_data(self, bot: Bot) -> BotExport:
        return BotExport(
            bot={
                "id": str(bot.id),
                "name": bot.name,
                "version": bot.version,
                "description": bot.description,
                "domain": bot.domain,
                "status": bot.status,
                "created_at": bot.created_at.isoformat()
            },
            capabilities=bot.capabilities.dict(),
            interfaces={
                "inputs": [{"name": "question", "type": "string", "required": True}],
                "outputs": [{"name": "answer", "type": "string"}]
            },
            configuration=bot.configuration.dict(),
            constraints=bot.constraints.dict(),
            integration={
                "execution_mode": "sync",
                "transport": "http",
                "auth_required": True
            },
            metadata={
                "project": "System RAG Platform",
                "exported_at": datetime.utcnow().isoformat()
            }
        )

    def ingest_document(self, bot_id: str, file_path: Path, filename: str) -> IngestResponse:
        bot = self.db.get_bot(bot_id)
        if not bot:
            raise ValueError(f"Bot with ID {bot_id} not found")

        document_id = str(hash(filename))
        chunks_count = self.engine.ingest_file(file_path, str(bot.id), document_id)
        
        return IngestResponse(
            bot_id=bot.id,
            document_id=document_id,
            chunks_count=chunks_count
        )

    def ask(self, bot_id: str, request: AskRequest) -> AskResponse:
        bot = self.db.get_bot(bot_id)
        if not bot:
            raise ValueError(f"Bot with ID {bot_id} not found")

        result = self.engine.query(
            bot=bot,
            question=request.question,
            top_k=request.top_k
        )

        sources = [
            Source(
                document_id=s["document_id"],
                page=s["page"]
            ) for s in result["sources"]
        ]

        return AskResponse(
            bot_id=bot.id,
            answer=result["answer"],
            messages=[
                self.handler.text(result["answer"])
            ],
            sources=sources,
            confidence=ConfidenceLevel(result["confidence"])
        )

    def export_bot(self, bot_id: str) -> BotExport:
        bot = self.db.get_bot(bot_id)
        if not bot:
            raise ValueError(f"Bot with ID {bot_id} not found")

        # Standard, project-agnostic JSON structure
        export_data = self._generate_export_data(bot)
        
        # Persistence: Store the generated JSON in the bot record
        bot.export_json = export_data.dict()
        self.db.update_bot(bot)
        
        return export_data
