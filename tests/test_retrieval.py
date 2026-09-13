from orion.models import DocumentChunk, SourceType, RiskDimension
from orion.retrieval import keyword_score, retrieve_chunks

def make_chunk(text: str, page: int) -> DocumentChunk:
    return DocumentChunk(
        document_id = "doc-001",
        document_name = "sample.pdf",
        source_type = SourceType.PDF,
        page = page,
        text = text
    )

def test_keyword_score_matches_relevant_terms():
    chunk = make_chunk(
        "Annual disaster recovery testing is performed under the business continuity programme.",
        page = 1
    )

    score = keyword_score(
        chunk,
        RiskDimension.OPERATIONAL_RESILIENCE
    )

    assert score > 0


def test_retrieve_chunks_filters_irrelevant_content():
    chunks = [
        make_chunk(
            "The company earned revenue of RM 5 million.",
            page = 1,
        ),

        make_chunk(
            "Annual disaster recovery testing is performed.",
            page = 2,
        )
    ]

    results = retrieve_chunks(
        chunks,
        RiskDimension.OPERATIONAL_RESILIENCE
    )

    assert len(results) == 1
    assert results[0].page == 2


def test_retrieve_chunks_prioritizes_more_matches():
    chunks = [
        make_chunk(
            "The company maintains backup procedures.",
            page = 1
        ),

        make_chunk(
            "The company maintains disaster recovery, backup, resilience and business continuity procedures.",
            page = 2
        )
    ]

    results = retrieve_chunks(
        chunks,
        RiskDimension.OPERATIONAL_RESILIENCE
    )

    assert results[0].page == 2

def test_retrieve_chunks_respects_limit():
    chunks = [
        make_chunk("backup recovery resilience", page = 1),
        make_chunk("business continuity recovery", page = 2),
        make_chunk("disaster recovery backup", page = 3)
    ]

    results = retrieve_chunks(
        chunks,
        RiskDimension.OPERATIONAL_RESILIENCE,
        limit = 2
    )

    assert len(results) == 2