from io import BytesIO

from docx import Document
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.
    """

    pdf_file = BytesIO(file_bytes)
    reader = PdfReader(pdf_file)

    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            extracted_pages.append(page_text)

    return "\n".join(extracted_pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text content from a DOCX file.
    """

    docx_file = BytesIO(file_bytes)
    document = Document(docx_file)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract text content from a TXT file.
    """

    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from PDF, DOCX, or TXT files based on file extension.
    """

    lower_filename = filename.lower()

    if lower_filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if lower_filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    if lower_filename.endswith(".txt"):
        return extract_text_from_txt(file_bytes)

    raise ValueError("Unsupported file type. Only PDF, DOCX, and TXT files are supported.")