from orion.models import DocumentChunk, SourceType
from orion.chunking import split_chunk, split_chunks

def make_chunk(text: str) -> DocumentChunk:
    return DocumentChunk(
        document_id = "doc-001",
        document_name = "sample.pdf",
        source_type = SourceType.PDF,
        page = 3,
        text = text
    )

def test_short_chunk_is_returned_unchanged():
    chunk = make_chunk("Short text.")

    result = split_chunk(chunk, max_chars = 100)

    assert len(result) == 1
    assert result[0] == chunk


def test_long_chunk_is_split():
    chunk = make_chunk("A" * 250)

    result = split_chunk(chunk, max_chars = 100)

    assert len(result) == 3
    assert len(result[0].text) == 100
    assert len(result[1].text) == 100
    assert len(result[2].text) == 50


def test_split_chunk_preserves_provenance():
    chunk = make_chunk("A" * 250)

    result = split_chunk(chunk, max_chars = 100)

    for piece in result:
        assert piece.document_id == "doc-001"
        assert piece.document_name == "sample.pdf"
        assert piece.source_type == SourceType.PDF
        assert piece.page == 3


def test_split_chunks_flattens_results():
    chunks = [
        make_chunk("A" * 150),
        make_chunk("B" * 50),
    ]

    result = split_chunks(chunks, max_chars = 100)

    assert len(result) == 3