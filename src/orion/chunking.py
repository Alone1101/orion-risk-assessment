from orion.models import DocumentChunk

def split_chunk(chunk: DocumentChunk, max_chars: int = 2000) -> list[DocumentChunk]:
    text = chunk.text.strip()

    if len(text) <= max_chars:
        return [chunk]

    pieces: list[DocumentChunk] = []

    for start in range(0, len(text), max_chars):
        piece = text[start:start + max_chars].strip()

        if not piece:
            continue

        pieces.append(
            DocumentChunk(
                document_id = chunk.document_id,
                document_name = chunk.document_name,
                source_type = chunk.source_type,
                page = chunk.page,
                section = chunk.section,
                text = piece
            )
        )

    return pieces

def split_chunks(chunks: list[DocumentChunk], max_chars: int = 2000) -> list[DocumentChunk]:
    result: list[DocumentChunk] = []

    for chunk in chunks:
        result.extend(
            split_chunk(
                chunk,
                max_chars = max_chars
            )
        )

    return result