from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summaries.generator import SummaryService

router = APIRouter(prefix="/books", tags=["Summaries"])

@router.post("/{book_id}/summary", response_model=SummaryResponse)
async def generate_book_summary(
    book_id: UUID,
    request: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate or retrieve a structured summary (quick, detailed, chapter, study guide)."""
    service = SummaryService(db)
    try:
        return await service.generate_summary(
            user_id=current_user.id,
            book_id=book_id,
            summary_type=request.summary_type,
            chapter=request.chapter
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
