from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

class SummaryRequest(BaseModel):
    summary_type: str = "detailed" # quick, detailed, chapter, key_ideas, study_guide
    chapter: Optional[str] = None

class SummaryResponse(BaseModel):
    book_id: UUID
    summary_type: str
    title: str
    summary: str
    key_takeaways: List[str] = []
