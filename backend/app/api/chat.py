import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.book import Book
from app.models.conversation import Conversation
from app.models.message import Message, MessageSource
from app.schemas.chat import ChatRequest, ChatResponse, ConversationRead, MessageRead, SourceCitation
from app.services.rag.retriever import RAGRetriever
from app.services.rag.generator import RAGGenerator

router = APIRouter(tags=["Chat"])

@router.post("/books/{book_id}/chat", response_model=ChatResponse)
async def chat_with_book(
    book_id: UUID,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with a book using RAG, return answer with exact page citations."""
    # 1. Authorize ownership
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    # 2. Get or create conversation
    conv_id = request.conversation_id
    if conv_id:
        conv_stmt = select(Conversation).where(
            and_(Conversation.id == conv_id, Conversation.user_id == current_user.id)
        )
        conversation = (await db.execute(conv_stmt)).scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            book_id=book.id,
            title=request.message[:40] + ("..." if len(request.message) > 40 else "")
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # 3. Store user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()

    # 4. RAG Retrieval
    retriever = RAGRetriever(db)
    retrieved_chunks = await retriever.retrieve_chunks(
        user_id=current_user.id,
        book_id=book.id,
        query=request.message,
        top_k=request.top_k
    )

    # 5. RAG Generation
    generator = RAGGenerator()
    answer, citations = await generator.generate_answer(request.message, retrieved_chunks)

    # 6. Store assistant message and citation sources
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    for cit in citations:
        source_record = MessageSource(
            message_id=assistant_msg.id,
            chunk_id=cit.chunk_id,
            page_number=cit.page,
            relevance_score=cit.relevance_score
        )
        db.add(source_record)
    await db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        answer=answer,
        sources=citations
    )

@router.get("/books/{book_id}/chat/stream")
async def stream_chat_with_book(
    book_id: UUID,
    message: str = Query(..., description="User query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Server-Sent Events (SSE) stream for interactive streaming chat."""
    # Authorize
    stmt = select(Book).where(and_(Book.id == book_id, Book.user_id == current_user.id))
    book = (await db.execute(stmt)).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    retriever = RAGRetriever(db)
    retrieved_chunks = await retriever.retrieve_chunks(
        user_id=current_user.id,
        book_id=book.id,
        query=message,
        top_k=5
    )

    generator = RAGGenerator()
    return StreamingResponse(
        generator.stream_answer(message, retrieved_chunks),
        media_type="text/event-stream"
    )

@router.get("/books/{book_id}/conversations", response_model=List[ConversationRead])
async def list_conversations(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chat history and conversations for a book."""
    stmt = (
        select(Conversation)
        .where(and_(Conversation.book_id == book_id, Conversation.user_id == current_user.id))
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    convs = result.scalars().all()
    return [ConversationRead.model_validate(c) for c in convs]
