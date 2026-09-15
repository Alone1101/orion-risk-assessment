from collections import defaultdict
from orion.models import Finding, RiskDimension, DimensionAssessment, ReviewerResult, AuditMetadata, AssessmentStatus, AuthorizationRecommendation, FollowUpQuestion
from orion.policy import SEVERITY_SCORES, risk_rating, DIMENSION_WEIGHTS, recommendation, POLICY_VERSION

DEFAULT_EVIDENCE_REQUESTS = {
    RiskDimension.GOVERNANCE_OWNERSHIP:
        "ownership, governance, and beneficial ownership information",

    RiskDimension.FINANCIAL_RESILIENCE:
        "financial position, liquidity, and capital information",

    RiskDimension.OPERATIONAL_RESILIENCE:
        "business continuity and operational resilience evidence",

    RiskDimension.CYBERSECURITY_DATA:
        "cybersecurity and data protection evidence",

    RiskDimension.COMPLIANCE_INTEGRITY:
        "regulatory compliance and integrity information"
}

# Converts a group of findings into one score
def score_findings(findings: list[Finding]) -> float:
    if not findings:
        return 0.0 

    scores = [SEVERITY_SCORES[finding.severity] * finding.confidence for finding in findings]

    return sum(scores) / len(scores)

def build_dimension_assessment(dimension: RiskDimension, findings: list[Finding], missing_information: list[str] | None = None) -> DimensionAssessment:
    missing_information = missing_information or []

    if missing_information:
        return DimensionAssessment(
            dimension = dimension,
            status = AssessmentStatus.INSUFFICIENT_EVIDENCE,
            findings = findings,
            missing_information = missing_information
        )
    
    score = score_findings(findings)

    return DimensionAssessment(
        dimension = dimension,
        status = AssessmentStatus.ASSESSED,
        score = round(score, 2),
        rating = risk_rating(score),
        findings = findings,
        missing_information = []
    )

def calculate_composite_score(assessments: list[DimensionAssessment]) -> float | None:
    if any(assessment.status == AssessmentStatus.INSUFFICIENT_EVIDENCE for assessment in assessments):
        return None

    return round(
        sum(
            assessment.score * DIMENSION_WEIGHTS[assessment.dimension]
            for assessment in assessments
            if assessment.score is not None
        ),
        2
    )

def assess_submission(
    submission_id: str, 
    findings: list[Finding], 
    missing_information_by_dimension: dict[RiskDimension, list[str]] | None = None, 
    llm_provider: str | None = None,
    llm_model: str | None = None
) -> ReviewerResult:
    
    missing_information_by_dimension = (missing_information_by_dimension or {})

    findings_by_dimension: dict[RiskDimension, list[Finding]] = defaultdict(list)

    for finding in findings:
        findings_by_dimension[finding.dimension].append(finding)

    assessments = [
        build_dimension_assessment(
            dimension = dimension,
            findings = findings_by_dimension[dimension],
            missing_information = missing_information_by_dimension.get(dimension, [])
        )
        for dimension in RiskDimension
    ]

    composite = calculate_composite_score(assessments)

    if composite is None:
        final_recommendation = (AuthorizationRecommendation.REQUEST_CLARIFICATION)
    else:
        final_recommendation = recommendation(composite)

    follow_up_questions = build_follow_up_questions(missing_information_by_dimension)

    return ReviewerResult(
        submission_id = submission_id,
        assessments = assessments,
        composite_score = composite,
        recommendation = final_recommendation,
        follow_up_questions = follow_up_questions,
        audit = AuditMetadata(
            pipeline_version = "0.1.0",
            policy_version = POLICY_VERSION,
            llm_provider = llm_provider,
            llm_model = llm_model
        )
    )

def build_follow_up_questions(missing_information_by_dimension: dict[RiskDimension, list[str]]) -> list[FollowUpQuestion]:
    questions: list[FollowUpQuestion] = []

    for dimension, missing_items in missing_information_by_dimension.items():
        for item in missing_items:
            questions.append(FollowUpQuestion(
                dimension = dimension,
                question = f"Please provide {item}.",
                reason = f"Required evidence is missing for {dimension.value}."
            ))

    return questions