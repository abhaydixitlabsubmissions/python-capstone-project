import os
from app.services.documents.extractor import DocumentExtractor

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARENT_DIR = os.path.dirname(WORKSPACE_ROOT)

def test_extract_pdf():
    pdf_path = os.path.join(PARENT_DIR, "MLPR lab 4 - Solutions.pdf")
    if not os.path.exists(pdf_path):
        return

    pages = DocumentExtractor.extract_pdf(pdf_path)
    assert len(pages) > 0
    assert pages[0].page_number == 1
    assert len(pages[0].text) > 0
    print(f"Extracted {len(pages)} pages from PDF. Sample text: {pages[0].text[:100]}...")

def test_extract_docx():
    docx_path = os.path.join(PARENT_DIR, "MLPR lab 4 - Solutions.docx")
    if not os.path.exists(docx_path):
        return

    pages = DocumentExtractor.extract_docx(docx_path)
    assert len(pages) > 0
    assert pages[0].page_number >= 1
    assert len(pages[0].text) > 0
    print(f"Extracted {len(pages)} estimated pages from DOCX.")
