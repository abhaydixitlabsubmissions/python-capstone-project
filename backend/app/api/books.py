import os
import shutil
import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.book import Book
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.book import BookRead, BookUploadResponse, SimilarDocumentItem
from app.schemas.chunk import ChunkRead
from app.services.documents.hasher import calculate_sha256
from app.services.documents.extractor import DocumentExtractor
from app.services.documents.chunker import DocumentChunker
from app.services.embeddings.provider import get_embedding_provider
from app.services.similarity.detector import SimilarityDetector
from app.core.config import settings

router = APIRouter(prefix="/books", tags=["Books"])

@router.post("", response_model=BookUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a book, calculate hash, check similarity against personal library, and register book."""
    filename = file.filename or "unknown.pdf"
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "epub", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported formats: PDF, EPUB, DOCX.",
        )

    # 1. Calculate SHA-256
    file_hash = calculate_sha256(file.file)

    # 2. Check duplicate & semantic similarity
    detector = SimilarityDetector(db)
    book_title = title or os.path.splitext(filename)[0].replace("-", " ").replace("_", " ").title()
    similarity_result = await detector.detect_similar_documents(
        user_id=current_user.id,
        file_hash=file_hash,
        title=book_title,
        author=author,
    )

    # 3. Save file to storage
    book_id = uuid.uuid4()
    storage_dir = os.path.join(settings.STORAGE_LOCAL_DIR, "users", str(current_user.id), "books", str(book_id))
    os.makedirs(storage_dir, exist_ok=True)
    destination_path = os.path.join(storage_dir, filename)

    file.file.seek(0)
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(destination_path)

    # 4. Create Book entry in database
    new_book = Book(
        id=book_id,
        user_id=current_user.id,
        title=book_title,
        author=author,
        description=description,
        file_name=filename,
        file_type=ext,
        file_size=file_size,
        storage_key=destination_path,
        file_hash=file_hash,
        status="uploaded",
    )
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)

    return BookUploadResponse(
        book=BookRead.model_validate(new_book),
        similarity_check=similarity_result
    )

@router.post("/{book_id}/process", response_model=BookRead)
async def process_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute ingestion pipeline: extract text, chunk, embed, and mark ready."""
    # 1. Authorize ownership
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    try:
        book.status = "extracting"
        await db.commit()

        # 2. Extract text pages
        pages = DocumentExtractor.extract(book.storage_key, book.file_type)
        book.page_count = len(pages)
        total_words = sum(len(p.text.split()) for p in pages)
        book.word_count = total_words

        book.status = "chunking"
        await db.commit()

        # 3. Create document version record
        doc_record = Document(
            book_id=book.id,
            version=1,
            page_count=len(pages),
            word_count=total_words,
            processing_status="processing"
        )
        db.add(doc_record)
        await db.commit()
        await db.refresh(doc_record)

        # 4. Chunk
        chunker = DocumentChunker(target_tokens=750, overlap_tokens=150)
        chunks = chunker.chunk_pages(pages)

        book.status = "embedding"
        await db.commit()

        # 5. Embed chunks
        embed_provider = get_embedding_provider()
        chunk_texts = [c.content for c in chunks]
        embeddings = await embed_provider.get_embeddings(chunk_texts)

        # 6. Save chunks
        for idx, chunk_res in enumerate(chunks):
            vec = embeddings[idx] if idx < len(embeddings) else None
            db_chunk = DocumentChunk(
                document_id=doc_record.id,
                book_id=book.id,
                chunk_index=chunk_res.chunk_index,
                content=chunk_res.content,
                page_start=chunk_res.page_start,
                page_end=chunk_res.page_end,
                chapter=chunk_res.chapter,
                section=chunk_res.section,
                token_count=chunk_res.token_count,
                embedding=vec,
                metadata_json=chunk_res.metadata,
            )
            db.add(db_chunk)

        # 7. Generate lightweight book-level embedding for cross-document similarity
        sample_text = " ".join([p.text[:300] for p in pages[:5]])
        book_embedding = await embed_provider.get_embedding(f"{book.title}\n{book.author or ''}\n{sample_text}")
        book.embedding = book_embedding

        # 8. Mark ready
        book.status = "ready"
        doc_record.processing_status = "ready"
        await db.commit()
        await db.refresh(book)

        return BookRead.model_validate(book)

    except Exception as e:
        book.status = "failed"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process book: {str(e)}",
        )

@router.get("", response_model=List[BookRead])
async def list_books(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all books in user's library."""
    stmt = select(Book).where(Book.user_id == current_user.id).order_by(Book.created_at.desc())
    result = await db.execute(stmt)
    books = result.scalars().all()
    return [BookRead.model_validate(b) for b in books]

@router.get("/{book_id}", response_model=BookRead)
async def get_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve book details by ID."""
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return BookRead.model_validate(book)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a book and its associated chunks, conversations, and notes."""
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    # Remove storage file
    if os.path.exists(book.storage_key):
        try:
            os.remove(book.storage_key)
        except OSError:
            pass

    await db.delete(book)
    await db.commit()
    return None

@router.get("/{book_id}/chunks", response_model=List[ChunkRead])
async def get_book_chunks(
    book_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chunks for a book (used for Reader view)."""
    # Authorize
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    chunks_stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.book_id == book_id)
        .order_by(DocumentChunk.chunk_index)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(chunks_stmt)
    chunks = result.scalars().all()
    return [ChunkRead.model_validate(c) for c in chunks]

@router.get("/{book_id}/related", response_model=List[SimilarDocumentItem])
async def get_related_documents(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get related documents within user's library for this book."""
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    detector = SimilarityDetector(db)
    res = await detector.detect_similar_documents(
        user_id=current_user.id,
        file_hash=book.file_hash,
        title=book.title,
        author=book.author,
        exclude_book_id=book.id,
    )
    return res.similar_documents
