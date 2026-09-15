import json
from orion.models import DocumentChunk, SourceType, RiskDimension, AssessmentStatus
from orion.pipeline import run_assessment

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

def test_pipeline_marks_unretrieved_dimensions_as_missing():
    chunks = [
        DocumentChunk(
            document_id = "doc-001",
            document_name = "continuity.pdf",
            source_type = SourceType.PDF,
            page = 1,
            text = ("The company performs annual disaster recovery and business continuity testing.")
        )
    ]

    result = run_assessment(
        submission_id = "ORION-TEST-001",
        provider = FakeLLMProvider(),
        chunks = chunks
    )

    assert result.submission_id == "ORION-TEST-001"
    assert result.composite_score is None
    assert result.recommendation.value == "request_clarification"

    # Verify if operational dimension was actuallly processed
    operational = next(assessment for assessment in result.assessments if assessment.dimension == RiskDimension.OPERATIONAL_RESILIENCE)

    assert operational.status == AssessmentStatus.ASSESSED
    assert operational.score == 0.0

def test_pipeline_scores_extracted_finding():
    class FindingLLMProvider:
        provider_name = "fake"
        model = "fake-model"

        def generate(self, prompt: str) -> str:
            return json.dumps(
                {
                    "findings": [
                        {
                            "description": ("Disaster recovery testing is not provided."),
                            "severity": "high",
                            "confidence": 0.95,
                            "evidence": [
                                {
                                    "source_id": "S1",
                                    "excerpt": ("Disaster recovery testing is not provided.")
                                }
                            ],
                        }
                    ],
                    "missing_information": []
                }
            )

    chunks = [
        DocumentChunk(
            document_id = "doc-001",
            document_name = "continuity.pdf",
            source_type = SourceType.PDF,
            page = 14,
            text = (
                "The business continuity programme is documented."
                "Disaster recovery testing is not provided."
            )
        )
    ]

    result = run_assessment(
        submission_id = "ORION-TEST-002",
        provider = FindingLLMProvider(),
        chunks = chunks
    )

    operational = next(assessment for assessment in result.assessments if assessment.dimension == RiskDimension.OPERATIONAL_RESILIENCE)

    assert operational.status == AssessmentStatus.ASSESSED
    assert operational.score == 66.5
    assert len(operational.findings) == 1
    assert operational.findings[0].evidence[0].page == 14

    assert result.composite_score is None