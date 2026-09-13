from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class BookBase(BaseModel):
    title: str
    author: Optional[str] = None
    description: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookRead(BookBase):
    id: UUID
    user_id: UUID
    file_name: str
    file_type: str
    file_size: int
    file_hash: str
    page_count: int
    word_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SimilarDocumentItem(BaseModel):
    book_id: UUID
    title: str
    author: Optional[str] = None
    similarity_score: float # 0.0 to 1.0 (e.g. 0.98 = 98%)
    relationship_type: str  # duplicate, highly_similar, related

class SimilarCheckResponse(BaseModel):
    is_exact_duplicate: bool
    exact_duplicate_book: Optional[BookRead] = None
    similar_documents: List[SimilarDocumentItem] = []

class BookUploadResponse(BaseModel):
    book: BookRead
    similarity_check: SimilarCheckResponse
