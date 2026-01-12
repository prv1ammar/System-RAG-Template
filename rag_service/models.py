from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BotStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class BotConfiguration(BaseModel):
    default_language: str = "fr"
    response_format: str = "json"
    reasoning_level: str = "analytical"
    tone: str = "professional"
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.0

class BotConstraints(BaseModel):
    scope_isolation: bool = True
    external_knowledge_allowed: bool = False
    hallucination_protection: bool = True

class BotCapabilities(BaseModel):
    can_answer_questions: bool = True
    supports_conversation: bool = True
    can_generate_tables: bool = True
    can_generate_charts: bool = True
    can_generate_images: bool = False

class Bot(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    version: str = "1.0.0"
    description: str
    domain: str
    status: BotStatus = BotStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    configuration: BotConfiguration = Field(default_factory=BotConfiguration)
    constraints: BotConstraints = Field(default_factory=BotConstraints)
    capabilities: BotCapabilities = Field(default_factory=BotCapabilities)
    export_json: Dict[str, Any] = Field(default_factory=dict)

class Source(BaseModel):
    document_id: str
    page: Optional[int] = None

class AskRequest(BaseModel):
    bot_id: UUID
    question: str
    top_k: int = 3

# --- Rich Messaging Models ---

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    SINGLE_CHOICE = "single-choice"
    CARD = "card"

class TextMessage(BaseModel):
    type: str = "text"
    text: str

class ImageMessage(BaseModel):
    type: str = "image"
    image: str

class AudioMessage(BaseModel):
    type: str = "audio"
    audio: str

class VideoMessage(BaseModel):
    type: str = "video"
    video: str

class DocumentMessage(BaseModel):
    type: str = "document"
    document: str
    title: str

class Choice(BaseModel):
    title: str
    value: str

class ChoiceMessage(BaseModel):
    type: str = "single-choice"
    text: str
    title: str
    choices: List[Choice]

class Action(BaseModel):
    action: str
    title: str
    url: str

class CardMessage(BaseModel):
    type: str = "card"
    title: str
    subtitle: str
    image: str
    actions: List[Action]

class AskResponse(BaseModel):
    bot_id: UUID
    answer: str
    messages: List[Dict[str, Any]] = [] # The exact JSON format requested
    sources: List[Source]
    confidence: ConfidenceLevel

class IngestResponse(BaseModel):
    bot_id: UUID
    document_id: str
    chunks_count: int
    status: str = "success"

class BotExport(BaseModel):
    bot: Dict[str, Any]
    capabilities: Dict[str, Any]
    interfaces: Dict[str, Any]
    configuration: Dict[str, Any]
    constraints: Dict[str, Any]
    integration: Dict[str, Any]
    metadata: Dict[str, Any]
