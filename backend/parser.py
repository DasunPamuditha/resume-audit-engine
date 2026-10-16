# backend/pdf_parser.py

import io
import re


def sanitize_pii_text(raw_text: str) -> str:
    """
    Ethical Data Minimization (Section 3.12.1):
    Strips personal phone numbers and email addresses in memory before processing
    so sensitive personal contact details are never stored or logged.
    """
    if not raw_text:
        return ""
    # Redact email addresses
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", raw_text)
    # Redact phone numbers
    text = re.sub(r"(\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}", "[REDACTED_PHONE]", text)
    return text


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text = ""
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        if text.strip():
            return sanitize_pii_text(text)
    except Exception as e:
        print(f"[!] PyMuPDF parsing notice: {e}. Falling back to pypdf.")

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    except Exception as e:
        print(f"[!] pypdf fallback error: {e}")

    return sanitize_pii_text(text)