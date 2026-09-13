import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, epub, docx
    file_size = Column(Integer, nullable=False)      # bytes
    storage_key = Column(String(1000), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True) # SHA-256
    page_count = Column(Integer, default=0, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="uploaded", nullable=False, index=True) # uploaded, extracting, chunking, embedding, finalizing, ready, failed
    
    # Lightweight document-level embedding for cross-book similarity discovery
    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="books")
    documents = relationship("Document", back_populates="book", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="book", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="book", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="book", cascade="all, delete-orphan")
