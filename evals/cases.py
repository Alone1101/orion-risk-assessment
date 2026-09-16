from dataclasses import dataclass, field
from orion.models import RiskDimension, Severity, DocumentChunk, SourceType

@dataclass
class ExpectedFinding:
    dimension: RiskDimension
    minimum_severity: Severity

@dataclass
class EvaluationCase:
    name: str
    chunks: list[str]
    expected_findings: list[ExpectedFinding] = field(default_factory = list)
    expected_missing_dimensions: list[RiskDimension] = field(default_factory = list)
    expected_composite: bool = False

EVALUATION_CASES = [
    EvaluationCase(
        name = "missing_disaster_recovery_test",
        chunks = [
            (
                "The company maintains a documented business continuity plan."
                "The latest disaster recovery testing report was not provided."
            )
        ],

        expected_findings = [
            ExpectedFinding(
                dimension = RiskDimension.OPERATIONAL_RESILIENCE,
                minimum_severity = Severity.MEDIUM
            )
        ],

        expected_missing_dimensions = [RiskDimension.OPERATIONAL_RESILIENCE]
    ),

    EvaluationCase(
        name = "high_risk_cybersecurity",
        chunks = [
            (
                "The company experienced a cybersecurity breach affecting customer data."
                "The incident review found that sensitive data was stored without encryption and privileged access controls were not enforced."
            )
        ],

        expected_findings = [
            ExpectedFinding(
                dimension = RiskDimension.CYBERSECURITY_DATA,
                minimum_severity = Severity.HIGH
            )
        ]
    ),

    EvaluationCase(
        name = "contradictory_disaster_recovery",
        chunks = [
            ("The organization performs disaster recovery testing annually and records the results."),
            ("The operational audit states that no disaster recovery test was conducted during the most recent reporting year.")
        ],

        expected_findings = [
            ExpectedFinding(
                dimension = RiskDimension.OPERATIONAL_RESILIENCE,
                minimum_severity = Severity.MEDIUM
            )
        ],

        expected_missing_dimensions = [RiskDimension.OPERATIONAL_RESILIENCE]
    ),

    EvaluationCase(
        name = "irrelevant_redundant_material",

        chunks = [
            "The company was incorporated in 2018 and operates three offices.",
            "The organization provides digital infrastructure services.",
            "The company employs approximately 120 staff.",
            "The organization provides digital infrastructure services.",
            ("A cybersecurity audit identified that privileged accounts did not consistently enforce multi-factor access control."),
            "The company was incorporated in 2018 and operates three offices."
        ],

        expected_findings = [
            ExpectedFinding(
                dimension = RiskDimension.CYBERSECURITY_DATA,
                minimum_severity = Severity.MEDIUM
            )
        ]
    ),

    EvaluationCase(
        name = "complete_low_risk",

        chunks = [
            ("The company maintains documented governance procedures, with identified directors, shareholders, and beneficial owners."),
            ("The company maintains adequate liquidity and capital reserves and reports no material outstanding debt."),
            ("Business continuity and disaster recovery plans are documented and tested annually."),
            (
                "Sensitive data is protected using encryption and access control."
                "Regular cybersecurity vulnerability assessments are performed."
            ),
            ("The company maintains regulatory compliance policies and conducts regular internal compliance audits.")
        ],

        expected_composite = True
    )
]

def build_chunks(case: EvaluationCase) -> list[DocumentChunk]:
    return [
        DocumentChunk(
            document_id = f"eval-doc-{index}",
            document_name = f"{case.name}.txt",
            source_type = SourceType.JSON,
            section = f"eval-chunk-{index}",
            text = text
        )
        for index, text in enumerate(case.chunks, start = 1)
    ]