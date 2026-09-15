from orion.llm import OllamaProvider
from orion.models import DocumentChunk, SourceType
from orion.pipeline import run_assessment

provider = OllamaProvider()

chunks = [
    DocumentChunk(
        document_id = "doc-001",
        document_name = "business_continuity.pdf",
        source_type = SourceType.PDF,
        page = 14,
        text = (
            "The company maintains a documented business continuity plan. "
            "Critical systems are backed up daily. "
            "Disaster recovery testing is not provided."
        )
    ),

    DocumentChunk(
        document_id = "doc-002",
        document_name = "security_policy.pdf",
        source_type = SourceType.PDF,
        page = 8,
        text = (
            "Sensitive customer data is encrypted at rest and in transit. "
            "Access control is role-based. "
            "The latest penetration test report was not provided."
        )
    )
]

result = run_assessment(
    submission_id = "ORION-DEMO-001",
    provider = provider,
    chunks = chunks
)

print(result.model_dump_json(indent = 2))