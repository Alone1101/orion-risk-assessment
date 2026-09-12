from orion.models import Finding, RiskDimension, Severity, EvidenceReference
from orion.scoring import assess_submission

findings = [
    Finding(
        dimension = RiskDimension.OPERATIONAL_RESILIENCE,
        description = "No evidence of disaster recovery testing.",
        severity = Severity.HIGH,
        confidence = 0.95,
        evidence=[
            EvidenceReference(
                document_id = "doc-001",
                document_name = "business_continuity.pdf",
                page = 14,
                excerpt = "Disaster recovery testing schedule: Not provided.",
            )
        ]
    )
]

missing_information = {RiskDimension.CYBERSECURITY_DATA: ["Cybersecurity policy was not provided."]}

result = assess_submission(
    submission_id = "ORION-DEMO-001",
    findings = findings,
    missing_information_by_dimension = missing_information
)

print(result.model_dump_json(indent = 2))