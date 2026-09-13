from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class NoteSection(BaseModel):
    heading: str
    points: List[str]

class StructuredNoteContent(BaseModel):
    title: str
    summary: Optional[str] = None
    sections: List[NoteSection] = []

class NoteBase(BaseModel):
    title: str
    content: str
    note_type: str = "manual" # manual, ai_generated, summary, chapter_notes, study_notes

class NoteCreate(NoteBase):
    book_id: Optional[UUID] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    note_type: Optional[str] = None

class NoteRead(NoteBase):
    id: UUID
    user_id: UUID
    book_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GenerateNoteRequest(BaseModel):
    note_type: str = "study_notes" # key_points, chapter_notes, study_notes, definitions
    chapter: Optional[str] = None
    prompt_instruction: Optional[str] = None
