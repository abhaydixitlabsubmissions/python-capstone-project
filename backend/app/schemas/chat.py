from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class SourceCitation(BaseModel):
    chunk_id: UUID
    page: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    snippet: str
    relevance_score: Optional[float] = None

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str
    top_k: int = 5

class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: List[SourceCitation] = []

class MessageRead(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    sources: List[SourceCitation] = []

    model_config = ConfigDict(from_attributes=True)

class ConversationRead(BaseModel):
    id: UUID
    book_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []

    model_config = ConfigDict(from_attributes=True)
