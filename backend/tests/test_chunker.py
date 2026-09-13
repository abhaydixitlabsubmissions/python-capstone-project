import os
from app.services.documents.extractor import DocumentExtractor
from app.services.documents.chunker import DocumentChunker

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_DIR = os.path.dirname(WORKSPACE_ROOT)

def test_chunking_pdf():
    pdf_path = os.path.join(PARENT_DIR, "MLPR lab 4 - Solutions.pdf")
    if not os.path.exists(pdf_path):
        return

    pages = DocumentExtractor.extract_pdf(pdf_path)
    chunker = DocumentChunker(target_tokens=400, overlap_tokens=80)
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert first_chunk.token_count > 0
    assert first_chunk.page_start == 1
    assert first_chunk.chunk_index == 0
    assert len(first_chunk.content) > 0

    print(f"Total chunks created: {len(chunks)}")
    print(f"First chunk span: Page {first_chunk.page_start} - {first_chunk.page_end}, tokens: {first_chunk.token_count}")
