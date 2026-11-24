"""Secure text extraction from PDF, DOCX and plain-text resumes.

Security notes
--------------
* File type is checked by extension AND by file signature ("magic bytes"), so a
  renamed executable is rejected.
* Text is extracted only; embedded scripts, macros, links and form actions are
  never executed or followed.
* Extracted text is treated as untrusted data. It is never interpreted as
  instructions and is never logged in full.
* Scanned (image-only) PDFs contain no text layer. We report that OCR is needed
  instead of pretending to read them.
"""

from __future__ import annotations

import io
import unicodedata
import zipfile
from dataclasses import dataclass

PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"

SUPPORTED_EXTENSIONS = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".txt": "text/plain"}

MIN_TEXT_CHARS = 30


class ExtractionError(ValueError):
    """Raised when a document cannot be safely converted to text.

    ``code`` is a stable machine-readable identifier used by the API layer.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ExtractedDocument:
    text: str
    file_type: str
    page_count: int | None = None
    warnings: list[str] | None = None


def detect_file_type(filename: str, content: bytes) -> str:
    """Return 'pdf', 'docx' or 'txt' after validating extension and signature."""
    name = (filename or "").lower().strip()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ExtractionError(
            "unsupported_file_type",
            f"Unsupported file type '{ext or 'unknown'}'. Upload a PDF, DOCX or TXT file.",
        )
    if not content:
        raise ExtractionError("empty_file", "The uploaded file is empty.")

    if ext == ".pdf":
        if not content.startswith(PDF_SIGNATURE):
            raise ExtractionError("invalid_signature", "The file has a .pdf extension but is not a valid PDF.")
        return "pdf"
    if ext == ".docx":
        if not content.startswith(ZIP_SIGNATURE):
            raise ExtractionError("invalid_signature", "The file has a .docx extension but is not a valid DOCX file.")
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ExtractionError("invalid_signature", "The archive is not a Word document.")
        except zipfile.BadZipFile as exc:
            raise ExtractionError("invalid_signature", "The DOCX file is corrupted.") from exc
        return "docx"
    # .txt — reject binary content (NUL bytes are a strong signal of binary data)
    if b"\x00" in content[:4096]:
        raise ExtractionError("invalid_signature", "The .txt file appears to contain binary data.")
    return "txt"


def _clean_extracted(text: str) -> str:
    """Normalise unicode and strip control characters while keeping line structure."""
    text = unicodedata.normalize("NFKC", text)
    cleaned_chars = []
    for ch in text:
        if ch in "\n\t":
            cleaned_chars.append(ch)
        elif unicodedata.category(ch).startswith("C"):
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(ch)
    lines = [" ".join(line.split()) for line in "".join(cleaned_chars).splitlines()]
    # collapse runs of blank lines
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


def _extract_pdf(content: bytes) -> ExtractedDocument:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ExtractionError(
            "dependency_missing", "PDF support requires PyMuPDF. Install it with: pip install pymupdf"
        ) from exc

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ExtractionError("corrupt_document", "The PDF could not be opened. It may be corrupted.") from exc

    with doc:
        if doc.needs_pass:
            raise ExtractionError("encrypted_document", "The PDF is password protected. Remove the password and retry.")
        page_texts = [page.get_text("text") for page in doc]
        page_count = doc.page_count

    text = _clean_extracted("\n".join(page_texts))
    if len(text) < MIN_TEXT_CHARS:
        raise ExtractionError(
            "no_extractable_text",
            "No extractable text was found. This PDF looks scanned (image-only). "
            "OCR is required; run OCR (for example with Tesseract) and upload the result, or paste the text.",
        )
    return ExtractedDocument(text=text, file_type="pdf", page_count=page_count, warnings=[])


def _extract_docx(content: bytes) -> ExtractedDocument:
    try:
        import docx  # python-docx
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError(
            "dependency_missing", "DOCX support requires python-docx. Install it with: pip install python-docx"
        ) from exc
    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:
        raise ExtractionError("corrupt_document", "The DOCX file could not be read.") from exc

    parts: list[str] = [p.text for p in document.paragraphs]
    # Tables are common in resumes (e.g. skills grids)
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    text = _clean_extracted("\n".join(parts))
    if len(text) < MIN_TEXT_CHARS:
        raise ExtractionError("no_extractable_text", "The DOCX document contains no readable text.")
    return ExtractedDocument(text=text, file_type="docx", warnings=[])


def _extract_txt(content: bytes) -> ExtractedDocument:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            raw = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover - latin-1 never fails
        raise ExtractionError("decode_error", "Could not decode the text file.")
    text = _clean_extracted(raw)
    if len(text) < MIN_TEXT_CHARS:
        raise ExtractionError("no_extractable_text", "The text file is empty or too short.")
    return ExtractedDocument(text=text, file_type="txt", warnings=[])


def extract_text(filename: str, content: bytes, max_bytes: int | None = None) -> ExtractedDocument:
    """Validate and extract text from an uploaded document."""
    if max_bytes is not None and len(content) > max_bytes:
        raise ExtractionError(
            "file_too_large", f"File is larger than the {max_bytes // (1024 * 1024)} MB limit."
        )
    file_type = detect_file_type(filename, content)
    if file_type == "pdf":
        return _extract_pdf(content)
    if file_type == "docx":
        return _extract_docx(content)
    return _extract_txt(content)


def clean_pasted_text(text: str) -> str:
    """Apply the same cleaning to pasted text that we apply to uploaded files."""
    return _clean_extracted(text or "")
