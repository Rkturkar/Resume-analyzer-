# ═══════════════════════════════════════════
# extractor.py — PDF to plain text
# ═══════════════════════════════════════════

import pdfplumber
import io
from fastapi import HTTPException


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts all text from a PDF file given as raw bytes.
    Uses pdfplumber — works well with text-based PDFs.
    Returns a single string with all page text joined.
    """
    try:
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to read PDF: {str(e)}"
        )