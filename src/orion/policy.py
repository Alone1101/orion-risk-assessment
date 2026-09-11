from orion.models import AuthorizationRecommendation, RiskDimension, RiskRating, Severity

POLICY_VERSION = "demo-policy-v1"

DIMENSION_WEIGHTS: dict[RiskDimension, float] = {
    RiskDimension.GOVERNANCE_OWNERSHIP: 0.15,
    RiskDimension.FINANCIAL_RESILIENCE: 0.20,
    RiskDimension.OPERATIONAL_RESILIENCE: 0.20,
    RiskDimension.CYBERSECURITY_DATA: 0.20,
    RiskDimension.COMPLIANCE_INTEGRITY: 0.25,
}

SEVERITY_SCORES: dict[Severity, float] = {
    Severity.LOW: 15.0,
    Severity.MEDIUM: 40.0,
    Severity.HIGH: 70.0,
    Severity.CRITICAL: 100.0,
}

def risk_rating(score: float) -> RiskRating:
    if score < 25:
        return RiskRating.LOW
    if score < 50:
        return RiskRating.MEDIUM
    if score < 75:
        return RiskRating.HIGH
    return RiskRating.CRITICAL

def recommendation(composite_score: float) -> AuthorizationRecommendation:
    if composite_score < 25:
        return AuthorizationRecommendation.STANDARD_REVIEW
    if composite_score < 50:
        return AuthorizationRecommendation.ENHANCED_REVIEW
    if composite_score < 75:
        return AuthorizationRecommendation.CONDITIONAL_AUTHORIZATION
    return AuthorizationRecommendation.ESCALATE_FOR_REJECTION_REVIEW