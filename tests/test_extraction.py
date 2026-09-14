import json, pytest
from orion.models import DocumentChunk, SourceType, RiskDimension
from orion.extraction import extract_dimension

class FakeLLMProvider:
    def __init__(self, response: dict):
        self.response = response

    def generate(self, prompt: str) -> str:
        return json.dumps(self.response)


def make_chunk() -> DocumentChunk:
    return DocumentChunk(
        document_id = "doc-001",
        document_name = "continuity.pdf",
        source_type = SourceType.PDF,
        page = 14,
        text = "Disaster recovery testing schedule: Not provided."
    )

def test_extract_dimension_builds_verified_finding():
    provider = FakeLLMProvider(
        {
            "findings": [
                {
                    "description": "Disaster recovery testing is missing.",
                    "severity": "high",
                    "confidence": 0.95,
                    "evidence": [
                        {
                            "source_id": "S1",
                            "excerpt": (
                                "Disaster recovery testing schedule: "
                                "Not provided."
                            ),
                        }
                    ],
                }
            ],
            "missing_information": [],
        }
    )

    result = extract_dimension(
        provider = provider,
        dimension = RiskDimension.OPERATIONAL_RESILIENCE,
        chunks = [make_chunk()]
    )

    assert len(result.findings) == 1

    finding = result.findings[0]

    assert finding.dimension == RiskDimension.OPERATIONAL_RESILIENCE
    assert finding.evidence[0].document_id == "doc-001"
    assert finding.evidence[0].page == 14

def test_extract_dimension_rejects_unknown_source():
    provider = FakeLLMProvider(
        {
            "findings": [
                {
                    "description": "Risk found.",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence": [
                        {
                            "source_id": "S99",
                            "excerpt": "Something",
                        }
                    ],
                }
            ],
            "missing_information": [],
        }
    )

    with pytest.raises(ValueError, match = "unknown source"):
        extract_dimension(
            provider = provider,
            dimension = RiskDimension.OPERATIONAL_RESILIENCE,
            chunks = [make_chunk()]
        )