from orion.llm import LLMProvider
from orion.models import DocumentChunk, ReviewerResult, Finding, RiskDimension
from orion.chunking import split_chunks
from orion.retrieval import retrieve_chunks
from orion.extraction import extract_dimension
from orion.scoring import assess_submission

def run_assessment(submission_id: str, provider: LLMProvider, chunks: list[DocumentChunk]) -> ReviewerResult:
    chunks = split_chunks(chunks)

    findings: list[Finding] = []
    missing_information: dict[RiskDimension, list[str]] = {}

    for dimension in RiskDimension:
        relevant_chunks = retrieve_chunks(chunks, dimension)

        if not relevant_chunks:
            missing_information[dimension] = [f"No relevant evidence found for {dimension.value}."]
            continue

        extraction = extract_dimension(
            provider = provider,
            dimension = dimension,
            chunks = relevant_chunks
        )

        findings.extend(extraction.findings)

        if extraction.missing_information:
            missing_information[dimension] = (extraction.missing_information)

    return assess_submission(
        submission_id = submission_id,
        findings = findings,
        missing_information_by_dimension = missing_information,
        llm_provider = provider.provider_name,
        llm_model = provider.model
    )