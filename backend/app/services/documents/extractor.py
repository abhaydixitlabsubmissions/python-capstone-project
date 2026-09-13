import os
import re
from typing import List, Dict, Any

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    ebooklib = None
    epub = None
    BeautifulSoup = None

class ExtractedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

class DocumentExtractor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        # Remove null bytes
        text = text.replace("\x00", "")
        # Normalize non-breaking spaces and unusual whitespace
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip()

    @classmethod
    def extract_pdf(cls, file_path: str) -> List[ExtractedPage]:
        """Extract text from PDF preserving page numbers."""
        pages: List[ExtractedPage] = []
        doc = fitz.open(file_path)
        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text")
                cleaned = cls.clean_text(text)
                pages.append(ExtractedPage(page_number=page_idx + 1, text=cleaned))
        finally:
            doc.close()
        return pages

    @classmethod
    def extract_docx(cls, file_path: str) -> List[ExtractedPage]:
        """Extract text from DOCX file. Estimates pages based on paragraph distribution."""
        doc = DocxDocument(file_path)
        pages: List[ExtractedPage] = []
        current_page_text: List[str] = []
        current_page_num = 1
        word_counter = 0

        for para in doc.paragraphs:
            text = cls.clean_text(para.text)
            if not text:
                continue
            current_page_text.append(text)
            word_counter += len(text.split())
            # Estimate ~300 words per page in DOCX
            if word_counter >= 300:
                pages.append(ExtractedPage(page_number=current_page_num, text="\n\n".join(current_page_text)))
                current_page_text = []
                current_page_num += 1
                word_counter = 0

        if current_page_text or not pages:
            pages.append(ExtractedPage(page_number=current_page_num, text="\n\n".join(current_page_text)))

        return pages

    @classmethod
    def extract_epub(cls, file_path: str) -> List[ExtractedPage]:
        """Extract text from EPUB by items and chapters."""
        book = epub.read_epub(file_path)
        pages: List[ExtractedPage] = []
        page_num = 1

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), "html.parser")
                text = cls.clean_text(soup.get_text())
                if text:
                    pages.append(ExtractedPage(page_number=page_num, text=text))
                    page_num += 1

        return pages

    @classmethod
    def extract(cls, file_path: str, file_type: str) -> List[ExtractedPage]:
        """Main dispatcher for extracting text according to file extension."""
        ft = file_type.lower().strip().replace(".", "")
        if ft == "pdf":
            return cls.extract_pdf(file_path)
        elif ft in ["docx", "doc"]:
            return cls.extract_docx(file_path)
        elif ft == "epub":
            return cls.extract_epub(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
