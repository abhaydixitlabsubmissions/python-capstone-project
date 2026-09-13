from typing import List, Optional
from uuid import UUID
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.book import Book
from app.models.chunk import DocumentChunk
from app.schemas.note import StructuredNoteContent, NoteSection
from app.core.config import settings

class NoteGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = settings.LLM_PROVIDER.lower()

    async def generate_structured_note(
        self,
        user_id: UUID,
        book_id: UUID,
        note_type: str = "study_notes",
        chapter: Optional[str] = None
    ) -> StructuredNoteContent:
        """Generate structured JSON note content from book context."""
        # 1. Authorize
        book_query = await self.db.execute(
            select(Book).where(and_(Book.id == book_id, Book.user_id == user_id))
        )
        book = book_query.scalar_one_or_none()
        if not book:
            raise PermissionError("Access denied or book not found.")

        # 2. Retrieve sample chunks
        stmt = select(DocumentChunk).where(DocumentChunk.book_id == book_id)
        if chapter:
            stmt = stmt.where(DocumentChunk.chapter == chapter)
        stmt = stmt.order_by(DocumentChunk.chunk_index).limit(10)

        result = await self.db.execute(stmt)
        chunks = result.scalars().all()
        excerpt = "\n\n".join([c.content[:400] for c in chunks[:5]])

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""Generate structured {note_type} for "{book.title}".
Return STRICT JSON format with this schema:
{{
  "title": "Note title",
  "summary": "High-level summary",
  "sections": [
    {{
      "heading": "Heading name",
      "points": ["point 1", "point 2"]
    }}
  ]
}}

EXCERPTS:
{excerpt}"""
            resp = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return StructuredNoteContent(**data)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            import httpx
            model_name = settings.CHAT_MODEL.replace("models/", "")
            if "flash" in model_name:
                model_name = "gemini-flash-latest"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Generate structured {note_type} for "{book.title}".
Return strictly valid JSON matching this schema:
{{
  "title": "Note title",
  "summary": "High-level summary",
  "sections": [
    {{
      "heading": "Heading name",
      "points": ["point 1", "point 2"]
    }}
  ]
}}
Do NOT wrap the JSON in Markdown code fences. Return raw JSON only.

EXCERPTS:
{excerpt}"""
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json"
                        }
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    if raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    parsed = json.loads(raw_text.strip())
                    return StructuredNoteContent(**parsed)
                else:
                    raise RuntimeError(f"Gemini note generation failed ({resp.status_code}): {resp.text}")
        else:
            # Fallback structured notes for local testing
            return StructuredNoteContent(
                title=f"{book.title} - {note_type.replace('_', ' ').title()}",
                summary=f"Key analytical concepts and study points extracted from {book.title}.",
                sections=[
                    NoteSection(
                        heading="Foundational Principles",
                        points=[
                            "Incremental improvements compound significantly over time.",
                            "Systems and processes outlast goal-centric motivation.",
                            "Identity-based change creates durable behavior shifts."
                        ]
                    ),
                    NoteSection(
                        heading="Practical Implementations",
                        points=[
                            "Design environment cues to reduce cognitive friction.",
                            "Track progression using simple visual scoreboards."
                        ]
                    )
                ]
            )
