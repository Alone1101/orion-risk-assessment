import pytest
from pathlib import Path
from orion.ingestion import parse_document, parse_pdf, parse_docx, parse_xlsx

def test_parse_document_rejects_unsupported_extension():
    with pytest.raises(ValueError):
        parse_document(
            Path("example.txt"),
            document_id="doc-test",
        )

FIXTURES = Path(__file__).parent / "fixtures"

def test_parse_pdf_extracts_text():
    chunks = parse_pdf(
        FIXTURES / "sample.pdf",
        document_id="pdf-001",
    )

    assert len(chunks) >= 1
    assert chunks[0].document_id == "pdf-001"
    assert chunks[0].page == 1
    assert "Disaster recovery" in chunks[0].text

def test_parse_docx_extracts_paragraph():
    chunks = parse_docx(
        FIXTURES / "sample.docx",
        document_id="docx-001",
    )

    assert len(chunks) >= 1
    assert chunks[0].document_id == "docx-001"
    assert "Cybersecurity policy" in chunks[0].text


def test_parse_xlsx_extracts_row():
    chunks = parse_xlsx(
        FIXTURES / "sample.xlsx",
        document_id="xlsx-001",
    )

    assert len(chunks) >= 1
    assert chunks[0].document_id == "xlsx-001"
    assert "Revenue" in chunks[0].text
    assert "5000000" in chunks[0].text