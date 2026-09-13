from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.note import Note
from app.schemas.note import NoteRead, NoteCreate, NoteUpdate, GenerateNoteRequest, StructuredNoteContent
from app.services.notes.generator import NoteGeneratorService

router = APIRouter(prefix="/notes", tags=["Notes"])

@router.get("", response_model=List[NoteRead])
async def list_notes(
    book_id: Optional[UUID] = Query(None, description="Filter notes by book ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notes belonging to current user."""
    stmt = select(Note).where(Note.user_id == current_user.id)
    if book_id:
        stmt = stmt.where(Note.book_id == book_id)
    stmt = stmt.order_by(Note.updated_at.desc())

    result = await db.execute(stmt)
    notes = result.scalars().all()
    return [NoteRead.model_validate(n) for n in notes]

@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_in: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new manual or saved note."""
    new_note = Note(
        user_id=current_user.id,
        book_id=note_in.book_id,
        title=note_in.title,
        content=note_in.content,
        note_type=note_in.note_type,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return NoteRead.model_validate(new_note)

@router.get("/{note_id}", response_model=NoteRead)
async def get_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single note by ID."""
    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id))
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return NoteRead.model_validate(note)

@router.put("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: UUID,
    note_in: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update note content or title."""
    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id))
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    if note_in.title is not None:
        note.title = note_in.title
    if note_in.content is not None:
        note.content = note_in.content
    if note_in.note_type is not None:
        note.note_type = note_in.note_type

    await db.commit()
    await db.refresh(note)
    return NoteRead.model_validate(note)

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete note."""
    stmt = select(Note).where(and_(Note.id == note_id, Note.user_id == current_user.id))
    note = (await db.execute(stmt)).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    await db.delete(note)
    await db.commit()
    return None

@router.post("/generate", response_model=StructuredNoteContent)
async def generate_ai_note(
    book_id: UUID,
    request: GenerateNoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate structured AI notes (definitions, study points, key arguments) from a book."""
    service = NoteGeneratorService(db)
    try:
        return await service.generate_structured_note(
            user_id=current_user.id,
            book_id=book_id,
            note_type=request.note_type,
            chapter=request.chapter
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
