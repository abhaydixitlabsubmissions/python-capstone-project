from typing import List, AsyncGenerator, Dict, Any, Tuple
import json
from app.core.config import settings
from app.schemas.chunk import RetrievedChunk
from app.schemas.chat import SourceCitation

SYSTEM_PROMPT = """You are an assistant for a specific book.

Answer using the provided book context.

Rules:
1. Prefer information from the provided context.
2. Do not invent facts.
3. If the answer cannot be supported by the context, say that the book does not provide enough information.
4. Distinguish between the author's ideas and your own explanation.
5. Include source page references when available (e.g., [Page X])."""

class RAGGenerator:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

    def build_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks into book context."""
        context_parts = []
        for c in chunks:
            page_info = f"[Page {c.page_start}]" if c.page_start else "[Book Excerpt]"
            header = f"--- {page_info}"
            if c.chapter:
                header += f" {c.chapter}"
            header += " ---"
            context_parts.append(f"{header}\n{c.content}")
        return "\n\n".join(context_parts)

    def extract_citations(self, chunks: List[RetrievedChunk]) -> List[SourceCitation]:
        """Convert retrieved chunks into structured citations."""
        citations = []
        for c in chunks:
            snippet = c.content[:200] + "..." if len(c.content) > 200 else c.content
            citations.append(
                SourceCitation(
                    chunk_id=c.chunk_id,
                    page=c.page_start,
                    chapter=c.chapter,
                    section=c.section,
                    snippet=snippet,
                    relevance_score=c.similarity_score
                )
            )
        return citations

    async def generate_answer(
        self,
        question: str,
        chunks: List[RetrievedChunk]
    ) -> Tuple[str, List[SourceCitation]]:
        """Generate QA answer using configured LLM with citations."""
        citations = self.extract_citations(chunks)
        context = self.build_context(chunks)

        user_content = f"""BOOK CONTEXT

{context}

QUESTION

{question}"""

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2
            )
            answer = response.choices[0].message.content or ""
            return answer, citations

        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            import httpx
            model_name = settings.CHAT_MODEL.replace("models/", "")
            if "flash" in model_name:
                model_name = "gemini-flash-latest"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                        "contents": [{"parts": [{"text": user_content}]}]
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["candidates"][0]["content"]["parts"][0]["text"]
                    return answer, citations
                else:
                    raise RuntimeError(f"Gemini generation failed ({resp.status_code}): {resp.text}")

        else:
            # Deterministic mock response for offline development
            if not chunks:
                return "The book does not provide enough information to answer this question.", citations
            
            top_chunk = chunks[0]
            answer = (
                f"Based on the provided book context (particularly page {top_chunk.page_start}):\n\n"
                f"{top_chunk.content[:350]}...\n\n"
                f"This relates directly to your inquiry regarding '{question}'."
            )
            return answer, citations

    async def stream_answer(
        self,
        question: str,
        chunks: List[RetrievedChunk]
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens as Server-Sent Events (SSE)."""
        citations = self.extract_citations(chunks)
        
        # First send citation metadata
        yield f"event: citations\ndata: {json.dumps([c.model_dump(mode='json') for c in citations])}\n\n"

        context = self.build_context(chunks)
        user_content = f"BOOK CONTEXT\n\n{context}\n\nQUESTION\n\n{question}"

        if self.provider == "openai" and settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            stream = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield f"event: message\ndata: {json.dumps({'text': delta})}\n\n"
        else:
            answer, _ = await self.generate_answer(question, chunks)
            # Stream in chunks of words
            words = answer.split(" ")
            for word in words:
                yield f"event: message\ndata: {json.dumps({'text': word + ' '})}\n\n"

        yield "event: done\ndata: [DONE]\n\n"
