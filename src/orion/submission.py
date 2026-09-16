import json
from pathlib import Path
from orion.models import ApplicationSubmission, DocumentChunk, ReviewerResult, SourceType
from orion.ingestion import parse_document
from orion.llm import LLMProvider
from orion.pipeline import run_assessment

def load_submission(path: Path) -> ApplicationSubmission:
    data = json.loads(path.read_text(encoding = "utf-8"))

    return ApplicationSubmission.model_validate(data)

def load_submission_documents(submission: ApplicationSubmission, base_dir: Path | None = None) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for document in submission.documents:
        document_path = Path(document.path)

        if base_dir is not None and not document_path.is_absolute():
            document_path = base_dir / document_path

        chunks.extend(
            parse_document(
                path = document_path,
                document_id = document.document_id
            )
        )

    return chunks

def build_submission_metadata_chunk(submission: ApplicationSubmission, source_name: str) -> DocumentChunk:
    activities = ", ".join(submission.activities)

    text = (
        f"Applicant name: {submission.applicant_name}\n"
        f"Activities: {activities}"
    )

    return DocumentChunk(
        document_id = "primary-submission",
        document_name = source_name,
        source_type = SourceType.JSON,
        section = "application_metadata",
        text = text
    )

def run_submission(path: Path, provider: LLMProvider) -> ReviewerResult:
    submission = load_submission(path)

    chunks = load_submission_documents(
        submission = submission,
        base_dir = path.parent
    )

    metadata_chunk = build_submission_metadata_chunk(
        submission = submission,
        source_name = path.name
    )

    chunks.insert(0, metadata_chunk)

    return run_assessment(
        submission_id = submission.submission_id,
        provider = provider,
        chunks = chunks
    )