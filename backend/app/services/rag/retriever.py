from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.book import Book
from app.models.chunk import DocumentChunk
from app.schemas.chunk import RetrievedChunk
from app.services.embeddings.provider import get_embedding_provider

class RAGRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_provider = get_embedding_provider()

    async def retrieve_chunks(
        self,
        user_id: UUID,
        book_id: UUID,
        query: str,
        top_k: int = 5,
        hybrid: bool = False
    ) -> List[RetrievedChunk]:
        """Retrieve the top-k most relevant chunks for a book, enforcing user ownership."""
        # 1. Authorize: Ensure the book belongs to the requesting user
        book_query = await self.db.execute(
            select(Book).where(and_(Book.id == book_id, Book.user_id == user_id))
        )
        book = book_query.scalar_one_or_none()
        if not book:
            raise PermissionError("Access denied or book not found.")

        # 2. Compute query embedding
        query_vec = await self.embedding_provider.get_embedding(query)

        # 3. Vector search using pgvector cosine distance `<=>`
        try:
            # When pgvector is active
            stmt = (
                select(
                    DocumentChunk,
                    DocumentChunk.embedding.cosine_distance(query_vec).label("distance")
                )
                .where(DocumentChunk.book_id == book_id)
                .order_by("distance")
                .limit(top_k)
            )
            result = await self.db.execute(stmt)
            rows = result.all()

            retrieved = []
            for chunk, distance in rows:
                score = max(0.0, 1.0 - (distance or 0.0))
                retrieved.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        book_id=chunk.book_id,
                        content=chunk.content,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        chapter=chunk.chapter,
                        section=chunk.section,
                        similarity_score=round(score, 4)
                    )
                )
            return retrieved
        except Exception:
            # Fallback for environments where pgvector extension or sqlite fallback is running
            all_chunks_query = await self.db.execute(
                select(DocumentChunk).where(DocumentChunk.book_id == book_id)
            )
            chunks = all_chunks_query.scalars().all()

            # Rank by simple keyword overlap or normalized dot-product
            query_words = set(query.lower().split())
            scored = []
            for chunk in chunks:
                chunk_words = set(chunk.content.lower().split())
                overlap = len(query_words.intersection(chunk_words))
                scored.append((overlap, chunk))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            top_chunks = scored[:top_k]

            return [
                RetrievedChunk(
                    chunk_id=c.id,
                    book_id=c.book_id,
                    content=c.content,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    chapter=c.chapter,
                    section=c.section,
                    similarity_score=round(float(score) / max(1, len(query_words)), 4)
                )
                for score, c in top_chunks
            ]
