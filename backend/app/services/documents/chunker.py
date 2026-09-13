import re
from typing import List, Dict, Any, Optional
from app.services.documents.extractor import ExtractedPage

CHAPTER_PATTERNS = [
    re.compile(r"^(?:CHAPTER|Chapter)\s+([0-9IVXLCDM]+|[A-Za-z]+)(?::|\s*[-–—]\s*|\s+)?(.*)$", re.MULTILINE),
    re.compile(r"^(?:PART|Part)\s+([0-9IVXLCDM]+|[A-Za-z]+)(?::|\s*[-–—]\s*|\s+)?(.*)$", re.MULTILINE),
    re.compile(r"^(?:SECTION|Section)\s+([0-9IVXLCDM]+|[A-Za-z]+)(?::|\s*[-–—]\s*|\s+)?(.*)$", re.MULTILINE),
    re.compile(r"^([0-9]+\.[0-9]*)\s+([A-Z].*)$", re.MULTILINE),
]

class ChunkResult:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        page_start: int,
        page_end: int,
        chapter: Optional[str] = None,
        section: Optional[str] = None,
        token_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_index = chunk_index
        self.content = content
        self.page_start = page_start
        self.page_end = page_end
        self.chapter = chapter
        self.section = section
        self.token_count = token_count
        self.metadata = metadata or {}

class DocumentChunker:
    def __init__(self, target_tokens: int = 750, overlap_tokens: int = 150):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count based on 1 token ≈ 0.75 words or ~4 characters."""
        words = text.split()
        return max(1, int(len(words) * 1.3))

    @classmethod
    def detect_chapter_header(cls, text: str) -> Optional[str]:
        """Detect chapter or section headings in a text block."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return None
        # Check first 3 lines of block
        for line in lines[:3]:
            for pattern in CHAPTER_PATTERNS:
                match = pattern.search(line)
                if match:
                    header = line.strip()
                    if len(header) <= 120:
                        return header
        return None

    def chunk_pages(self, pages: List[ExtractedPage]) -> List[ChunkResult]:
        """Hierarchically chunk extracted pages into semantic chunks."""
        chunks: List[ChunkResult] = []
        current_chapter: Optional[str] = None
        current_section: Optional[str] = None
        
        current_chunk_words: List[str] = []
        current_page_start: Optional[int] = None
        current_page_end: Optional[int] = None
        chunk_idx = 0

        for page in pages:
            text = page.text
            if not text.strip():
                continue

            # Detect chapter changes on this page
            detected_chapter = self.detect_chapter_header(text)
            if detected_chapter:
                current_chapter = detected_chapter

            # Split page into paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [text.strip()]

            for para in paragraphs:
                para_words = para.split()
                if not para_words:
                    continue

                if current_page_start is None:
                    current_page_start = page.page_number
                current_page_end = page.page_number

                projected_word_count = len(current_chunk_words) + len(para_words)
                projected_tokens = int(projected_word_count * 1.3)

                if projected_tokens >= self.target_tokens and current_chunk_words:
                    # Finalize current chunk
                    chunk_text = " ".join(current_chunk_words)
                    token_count = self.estimate_tokens(chunk_text)
                    chunks.append(
                        ChunkResult(
                            chunk_index=chunk_idx,
                            content=chunk_text,
                            page_start=current_page_start,
                            page_end=current_page_end,
                            chapter=current_chapter,
                            section=current_section,
                            token_count=token_count,
                            metadata={
                                "word_count": len(current_chunk_words),
                                "page_span": f"{current_page_start}-{current_page_end}"
                            }
                        )
                    )
                    chunk_idx += 1

                    # Create overlap
                    overlap_word_count = int(self.overlap_tokens / 1.3)
                    if len(current_chunk_words) > overlap_word_count:
                        current_chunk_words = current_chunk_words[-overlap_word_count:] + para_words
                    else:
                        current_chunk_words = para_words
                    current_page_start = page.page_number
                else:
                    current_chunk_words.extend(para_words)

        # Final trailing chunk
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            token_count = self.estimate_tokens(chunk_text)
            chunks.append(
                ChunkResult(
                    chunk_index=chunk_idx,
                    content=chunk_text,
                    page_start=current_page_start or 1,
                    page_end=current_page_end or 1,
                    chapter=current_chapter,
                    section=current_section,
                    token_count=token_count,
                    metadata={"word_count": len(current_chunk_words)}
                )
            )

        return chunks
