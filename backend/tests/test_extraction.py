import io

import pytest

from app.nlp.extraction.document_extractor import ExtractionError, detect_file_type, extract_text
from app.nlp.extraction.sections import detect_sections, mask_urls_and_emails, split_sentences
from tests.conftest import SAMPLE_RESUME


def test_txt_extraction_preserves_lines():
    doc = extract_text("cv.txt", b"EXPERIENCE\n- Built APIs in Python and Docker for clients\n")
    assert doc.file_type == "txt"
    assert "Built APIs in Python" in doc.text
    assert doc.text.splitlines()[0] == "EXPERIENCE"


def test_empty_file_rejected():
    with pytest.raises(ExtractionError) as e:
        extract_text("cv.pdf", b"")
    assert e.value.code == "empty_file"


@pytest.mark.parametrize("name", ["cv.exe", "cv.png", "cv", "cv.doc"])
def test_unsupported_types_rejected(name):
    with pytest.raises(ExtractionError) as e:
        detect_file_type(name, b"some content here")
    assert e.value.code == "unsupported_file_type"


def test_renamed_file_rejected_by_signature():
    with pytest.raises(ExtractionError) as e:
        detect_file_type("cv.pdf", b"MZ\x90\x00 not a pdf")
    assert e.value.code == "invalid_signature"
    with pytest.raises(ExtractionError):
        detect_file_type("cv.docx", b"%PDF-1.4 actually a pdf")


def test_too_short_text_rejected():
    with pytest.raises(ExtractionError) as e:
        extract_text("cv.txt", b"hi")
    assert e.value.code == "no_extractable_text"


def test_size_limit():
    with pytest.raises(ExtractionError) as e:
        extract_text("cv.txt", b"a" * 2048, max_bytes=1024)
    assert e.value.code == "file_too_large"


def test_docx_extraction_including_tables():
    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("PROJECTS")
    d.add_paragraph("Built a sentiment classifier with PyTorch and FastAPI.")
    t = d.add_table(rows=1, cols=2)
    t.rows[0].cells[0].text = "Skills"
    t.rows[0].cells[1].text = "Python, SQL"
    buf = io.BytesIO()
    d.save(buf)
    doc = extract_text("cv.docx", buf.getvalue())
    assert doc.file_type == "docx"
    assert "PyTorch" in doc.text and "Python, SQL" in doc.text


def test_pdf_extraction_and_scanned_detection():
    fitz = pytest.importorskip("fitz")
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "EXPERIENCE\nDeveloped REST APIs with Flask and PostgreSQL.")
    doc = extract_text("cv.pdf", pdf.tobytes())
    assert "Flask" in doc.text and doc.page_count == 1

    blank = fitz.open()
    blank.new_page()  # no text layer -> behaves like a scanned PDF
    with pytest.raises(ExtractionError) as e:
        extract_text("scan.pdf", blank.tobytes())
    assert e.value.code == "no_extractable_text"
    assert "OCR" in e.value.message


def test_section_detection_on_sample_resume():
    names = [s.name for s in detect_sections(SAMPLE_RESUME)]
    for expected in ("header", "summary", "education", "experience", "projects", "skills", "certifications"):
        assert expected in names


def test_sentence_offsets_point_into_original_text():
    for s in split_sentences(SAMPLE_RESUME):
        assert SAMPLE_RESUME[s.start:s.end] == s.text


def test_url_and_email_masking_keeps_offsets():
    text = "Contact me at a.b@example.com or https://github.com/me for http stuff"
    masked = mask_urls_and_emails(text)
    assert len(masked) == len(text)
    assert "github" not in masked and "example.com" not in masked
    assert masked.endswith("for http stuff")
