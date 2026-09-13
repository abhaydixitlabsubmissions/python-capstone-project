from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.book import Book
from app.models.chunk import DocumentChunk
from app.schemas.book import BookRead
from app.schemas.chunk import RetrievedChunk
from app.services.rag.retriever import RAGRetriever

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/books", response_model=List[BookRead])
async def search_books(
    q: str = Query(..., min_length=1, description="Keyword search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search user's books by title, author, or description."""
    stmt = (
        select(Book)
        .where(
            and_(
                Book.user_id == current_user.id,
                or_(
                    Book.title.ilike(f"%{q}%"),
                    Book.author.ilike(f"%{q}%"),
                    Book.description.ilike(f"%{q}%"),
                )
            )
        )
        .limit(20)
    )
    result = await db.execute(stmt)
    books = result.scalars().all()
    return [BookRead.model_validate(b) for b in books]
