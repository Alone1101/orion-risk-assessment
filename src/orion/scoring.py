from collections import defaultdict
from orion.models import Finding, RiskDimension, DimensionAssessment, ReviewerResult, AuditMetadata
from orion.policy import SEVERITY_SCORES, risk_rating, DIMENSION_WEIGHTS, recommendation, POLICY_VERSION

# Converts a group of findings into one score
def score_findings(findings: list[Finding]) -> float:
    if not findings:
        return 0.0 

    scores = [SEVERITY_SCORES[finding.severity] * finding.confidence for finding in findings]

    return sum(scores) / len(scores)

def build_dimension_assessment(dimension: RiskDimension, findings: list[Finding], missing_information: list[str] | None = None) -> DimensionAssessment:
    score = score_findings(findings)

    return DimensionAssessment(
        dimension = dimension,
        score = round(score, 2),
        rating = risk_rating(score),
        findings = findings,
        missing_information = missing_information or []
    )

def calculate_composite_score(assessments: list[DimensionAssessment]) -> float:
    by_dimension = {assessment.dimension: assessment for assessment in assessments}

    composite = 0.0

    for dimension, weight in DIMENSION_WEIGHTS.items():
        assessment = by_dimension.get(dimension)

        if assessment is not None:
            composite += assessment.score * weight

    return round(composite, 2)

def assess_submission(submission_id: str, findings: list[Finding]) -> ReviewerResult:
    findings_by_dimension: dict[RiskDimension, list[Finding]] = defaultdict(list)

    for finding in findings:
        findings_by_dimension[finding.dimension].append(finding)

    assessments = [
        build_dimension_assessment(
            dimension = dimension,
            findings = findings_by_dimension[dimension]
        )
        for dimension in RiskDimension
    ]

    composite = calculate_composite_score(assessments)

    return ReviewerResult(
        submission_id = submission_id,
        assessments = assessments,
        composite_score = composite,
        recommendation = recommendation(composite),
        audit = AuditMetadata(
            pipeline_version = "0.1.0",
            policy_version = POLICY_VERSION
        )
    )