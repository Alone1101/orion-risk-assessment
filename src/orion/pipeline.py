import logging, time
from orion.llm import LLMProvider
from orion.models import DocumentChunk, ReviewerResult, Finding, RiskDimension
from orion.chunking import split_chunks
from orion.retrieval import retrieve_chunks
from orion.extraction import extract_dimension
from orion.scoring import assess_submission, DEFAULT_EVIDENCE_REQUESTS

logger = logging.getLogger(__name__)

def run_assessment(submission_id: str, provider: LLMProvider, chunks: list[DocumentChunk]) -> ReviewerResult:
    start = time.perf_counter()

    logger.info(
        "Assessment started submission_id = %s input_chunks = %d",
        submission_id,
        len(chunks)
    )

    chunks = split_chunks(chunks)

    logger.info(
        "Chunking completed submission_id = %s chunks = %d",
        submission_id,
        len(chunks)
    )

    findings: list[Finding] = []
    missing_information: dict[RiskDimension, list[str]] = {}

    for dimension in RiskDimension:
        relevant_chunks = retrieve_chunks(chunks, dimension)

        logger.info(
            "Retrieval completed dimension = %s relevant_chunks = %d",
            dimension.value,
            len(relevant_chunks)
        )

        if not relevant_chunks:
            missing_information[dimension] = [DEFAULT_EVIDENCE_REQUESTS[dimension]]
            continue

        dimension_start = time.perf_counter()

        extraction = extract_dimension(
            provider = provider,
            dimension = dimension,
            chunks = relevant_chunks
        )

        dimension_elapsed = time.perf_counter() - dimension_start

        logger.info(
            "Extraction completed dimension = %s findings = %d missing_items = %d duration = %.2fs",
            dimension.value,
            len(extraction.findings),
            len(extraction.missing_information),
            dimension_elapsed
        )

        findings.extend(extraction.findings)

        if extraction.missing_information:
            missing_information[dimension] = (extraction.missing_information)

    result = assess_submission(
        submission_id = submission_id,
        findings = findings,
        missing_information_by_dimension = missing_information,
        llm_provider = provider.provider_name,
        llm_model = provider.model
    )

    elapsed = time.perf_counter() - start

    logger.info(
        "Assessment completed submission_id = %s recommendation = %s duration = %.2fs",
        submission_id,
        result.recommendation.value,
        elapsed
    )

    return result