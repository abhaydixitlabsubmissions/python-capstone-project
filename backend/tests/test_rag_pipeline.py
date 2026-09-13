import os
import pytest
import numpy as np
import uuid
import asyncio
from app.services.documents.extractor import DocumentExtractor
from app.services.documents.chunker import DocumentChunker
from app.services.embeddings.provider import get_embedding_provider
from app.services.rag.generator import RAGGenerator
from app.schemas.chunk import RetrievedChunk

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_DIR = os.path.dirname(WORKSPACE_ROOT)

def test_end_to_end_rag():
    async def _run():
        pdf_path = os.path.join(PARENT_DIR, "MLPR lab 4 - Solutions.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("Test PDF not present in parent directory")

        # 1. Extract
        pages = DocumentExtractor.extract_pdf(pdf_path)
        assert len(pages) > 0

        # 2. Chunk
        chunker = DocumentChunker(target_tokens=400, overlap_tokens=50)
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) > 0

        # 3. Embed
        embedder = get_embedding_provider()
        chunk_texts = [c.content for c in chunks]
        embeddings = await embedder.get_embeddings(chunk_texts)
        assert len(embeddings) == len(chunks)

        # 4. Query vector & cosine similarity ranking
        query = "linear discriminant analysis decision boundary"
        query_vec = await embedder.get_embedding(query)
        
        scored = []
        for idx, c in enumerate(chunks):
            c_vec = embeddings[idx]
            # Cosine similarity
            cos_sim = float(np.dot(query_vec, c_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(c_vec) + 1e-9))
            scored.append((cos_sim, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_3 = scored[:3]

        retrieved = [
            RetrievedChunk(
                chunk_id=uuid.uuid4(),
                book_id=uuid.uuid4(),
                content=c.content,
                page_start=c.page_start,
                page_end=c.page_end,
                chapter=c.chapter,
                section=c.section,
                similarity_score=round(score, 4)
            )
            for score, c in top_3
        ]

        # 5. Generate Answer with Citations
        generator = RAGGenerator()
        answer, citations = await generator.generate_answer(query, retrieved)

        assert answer is not None
        assert len(answer) > 0
        assert len(citations) == len(retrieved)
        assert citations[0].page is not None
        assert len(citations[0].snippet) > 0

        print("\n--- RAG QA Test Successful ---")
        print(f"Question: {query}")
        print(f"Answer:\n{answer}")
        print("\nCitations:")
        for cit in citations:
            print(f"  - Page {cit.page} (Score: {cit.relevance_score}): {cit.snippet[:80]}...")

    asyncio.run(_run())
