from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ChunkRead(BaseModel):
    id: UUID
    book_id: UUID
    chunk_index: int
    content: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    token_count: int
    metadata_json: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RetrievedChunk(BaseModel):
    chunk_id: UUID
    book_id: UUID
    content: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    similarity_score: float # or distance
