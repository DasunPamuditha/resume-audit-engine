import pymupdf

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text = ""
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    return text