import json
from pathlib import Path
from orion.models import ApplicationSubmission
from orion.submission import load_submission, load_submission_documents, run_submission

class FakeLLMProvider:
    provider_name = "fake"
    model = "fake-model"

    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "findings": [],
                "missing_information": []
            }
        )

def test_load_submission(tmp_path):
    submission_path = tmp_path / "application.json"

    submission_path.write_text(
        json.dumps(
            {
                "submission_id": "ORION-TEST-001",
                "applicant_name": "Example Ltd",
                "activities": ["digital infrastructure"],
                "documents": [
                    {
                        "document_id": "doc-001",
                        "path": "continuity.pdf",
                    }
                ],
            }
        ),
        encoding = "utf-8",
    )

    submission = load_submission(submission_path)

    assert submission.submission_id == "ORION-TEST-001"
    assert submission.applicant_name == "Example Ltd"
    assert len(submission.documents) == 1
    assert submission.documents[0].document_id == "doc-001"

def test_load_submission_documents():
    submission_data = {
        "submission_id": "ORION-TEST-002",
        "applicant_name": "Example Ltd",
        "activities": ["digital infrastructure"],
        "documents": [
            {
                "document_id": "doc-001",
                "path": "sample.pdf"
            }
        ],
    }

    submission = ApplicationSubmission.model_validate(submission_data)

    chunks = load_submission_documents(
        submission = submission,
        base_dir = Path("tests/fixtures")
    )

    assert len(chunks) > 0
    assert chunks[0].document_id == "doc-001"
    assert chunks[0].document_name == "sample.pdf"
    assert chunks[0].text.strip()

def test_run_submission(tmp_path):
    submission_path = tmp_path / "application.json"

    fixture_path = Path("tests/fixtures/sample.pdf").resolve()

    submission_path.write_text(
        json.dumps(
            {
                "submission_id": "ORION-TEST-003",
                "applicant_name": "Example Ltd",
                "activities": ["digital infrastructure"],
                "documents": [
                    {
                        "document_id": "doc-001",
                        "path": str(fixture_path),
                    }
                ],
            }
        ),
        encoding = "utf-8",
    )

    result = run_submission(
        path = submission_path,
        provider = FakeLLMProvider()
    )

    assert result.submission_id == "ORION-TEST-003"
    assert result.audit.llm_provider == "fake"
    assert result.audit.llm_model == "fake-model"