import pytest
from pydantic import ValidationError
from orion.models import Finding, RiskDimension, Severity, AssessmentStatus
from orion.scoring import score_findings, build_dimension_assessment, assess_submission, build_follow_up_questions

def test_score_findings_returns_confidence_weighted_mean():
    findings = [
        Finding(
            dimension = RiskDimension.OPERATIONAL_RESILIENCE,
            description = "Test finding",
            severity = Severity.HIGH,
            confidence = 0.5
        ),

        Finding(
            dimension = RiskDimension.OPERATIONAL_RESILIENCE,
            description = "Another finding",
            severity = Severity.MEDIUM,
            confidence = 1.0
        )
    ]

    score = score_findings(findings)

    assert score == 37.5 

def test_dimension_with_missing_information_is_not_scored():
    assessment = build_dimension_assessment(
        dimension = RiskDimension.CYBERSECURITY_DATA,
        findings = [],
        missing_information = ["Cybersecurity policy was not provided."]
    )

    assert assessment.status == AssessmentStatus.INSUFFICIENT_EVIDENCE
    assert assessment.score is None
    assert assessment.rating is None

def test_complete_submission_produces_composite_score():
    findings = [
        Finding(
            dimension = RiskDimension.OPERATIONAL_RESILIENCE,
            description = "No disaster recovery testing.",
            severity = Severity.HIGH,
            confidence = 0.95
        )
    ]

    result = assess_submission(
        submission_id = "test-001",
        findings = findings
    )

    assert result.composite_score == 13.3
    assert result.recommendation.value == "standard_review"

def test_missing_evidence_blocks_composite_score():
    result = assess_submission(
        submission_id = "test-002",
        findings = [],
        missing_information_by_dimension = {RiskDimension.CYBERSECURITY_DATA: ["Cybersecurity policy was not provided."]}
    )

    assert result.composite_score is None
    assert result.recommendation.value == "request_clarification"

def test_no_findings_returns_zero_score():
    assert score_findings([]) == 0.0

def test_critical_score_maps_to_critical_rating():
    assessment = build_dimension_assessment(
        dimension=RiskDimension.COMPLIANCE_INTEGRITY,
        findings=[
            Finding(
                dimension = RiskDimension.COMPLIANCE_INTEGRITY,
                description = "Critical compliance issue.",
                severity = Severity.CRITICAL,
                confidence = 1.0
            )
        ]
    )

    assert assessment.score == 100.0
    assert assessment.rating.value == "critical"

def test_finding_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        Finding(
            dimension = RiskDimension.CYBERSECURITY_DATA,
            description = "Invalid confidence test",
            severity = Severity.HIGH,
            confidence = 1.5
        )

def test_follow_up_questions_created_from_missing_information():
    missing = {RiskDimension.CYBERSECURITY_DATA: ["Latest penetration test report"]}

    questions = build_follow_up_questions(missing)

    assert len(questions) == 1
    assert questions[0].dimension == RiskDimension.CYBERSECURITY_DATA
    assert "Latest penetration test report" in questions[0].question