from typing import List, Optional, Tuple
from uuid import UUID
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.book import Book
from app.models.relationship import DocumentRelationship
from app.schemas.book import SimilarCheckResponse, SimilarDocumentItem, BookRead
from app.services.embeddings.provider import get_embedding_provider

class SimilarityDetector:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def check_exact_duplicate(self, user_id: UUID, file_hash: str) -> Optional[Book]:
        """Check if user already has an identical file by SHA-256 hash."""
        stmt = select(Book).where(
            and_(Book.user_id == user_id, Book.file_hash == file_hash)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def classify_similarity(score: float) -> Optional[str]:
        """Classify similarity according to system threshold rules."""
        if score >= 0.95:
            return "duplicate"
        elif score >= 0.85:
            return "highly_similar"
        elif score >= 0.70:
            return "related"
        return None

    async def generate_document_summary_embedding(
        self,
        title: str,
        author: Optional[str],
        sample_text: str
    ) -> List[float]:
        """Generate lightweight document-level embedding for cross-book similarity search."""
        combined_text = f"Title: {title}\nAuthor: {author or 'Unknown'}\nExcerpt: {sample_text[:1500]}"
        return await self.embedding_provider.get_embedding(combined_text)

    async def detect_similar_documents(
        self,
        user_id: UUID,
        file_hash: str,
        title: str,
        author: Optional[str] = None,
        sample_text: str = "",
        exclude_book_id: Optional[UUID] = None
    ) -> SimilarCheckResponse:
        """Run complete duplicate and semantic similarity check against the user's library."""
        # 1. Exact duplicate check
        exact_match = await self.check_exact_duplicate(user_id, file_hash)
        exact_book_read = BookRead.model_validate(exact_match) if exact_match else None
        is_exact = exact_match is not None

        # 2. Semantic similarity search
        similar_items: List[SimilarDocumentItem] = []
        doc_vector = await self.generate_document_summary_embedding(title, author, sample_text)

        try:
            # Query existing user books with embeddings
            stmt = (
                select(
                    Book,
                    Book.embedding.cosine_distance(doc_vector).label("distance")
                )
                .where(
                    and_(
                        Book.user_id == user_id,
                        Book.embedding.isnot(None),
                        Book.id != exclude_book_id if exclude_book_id else True
                    )
                )
                .order_by("distance")
                .limit(10)
            )
            result = await self.db.execute(stmt)
            for book, distance in result.all():
                sim_score = max(0.0, 1.0 - (distance or 0.0))
                rel_type = self.classify_similarity(sim_score)
                if rel_type:
                    similar_items.append(
                        SimilarDocumentItem(
                            book_id=book.id,
                            title=book.title,
                            author=book.author,
                            similarity_score=round(sim_score, 2),
                            relationship_type=rel_type
                        )
                    )
        except Exception:
            # Fallback when pgvector distance operator is not configured
            stmt = select(Book).where(
                and_(
                    Book.user_id == user_id,
                    Book.id != exclude_book_id if exclude_book_id else True
                )
            )
            result = await self.db.execute(stmt)
            books = result.scalars().all()
            for b in books:
                # Basic string similarity as fallback
                if b.title.lower() == title.lower():
                    similar_items.append(
                        SimilarDocumentItem(
                            book_id=b.id,
                            title=b.title,
                            author=b.author,
                            similarity_score=0.98,
                            relationship_type="duplicate"
                        )
                    )

        return SimilarCheckResponse(
            is_exact_duplicate=is_exact,
            exact_duplicate_book=exact_book_read,
            similar_documents=similar_items
        )
