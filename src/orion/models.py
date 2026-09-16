from enum import StrEnum
from typing import Annotated
from pydantic import BaseModel, Field

Probability = Annotated[float, Field(ge = 0.0, le = 1.0)]
RiskScore = Annotated[float, Field(ge = 0.0, le = 100.0)]

class RiskDimension(StrEnum):
    GOVERNANCE_OWNERSHIP = "governance_ownership"
    FINANCIAL_RESILIENCE = "financial_resilience"
    OPERATIONAL_RESILIENCE = "operational_resilience"
    CYBERSECURITY_DATA = "cybersecurity_data"
    COMPLIANCE_INTEGRITY = "compliance_integrity"

class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskRating(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuthorizationRecommendation(StrEnum):
    STANDARD_REVIEW = "standard_review"
    ENHANCED_REVIEW = "enhanced_review"
    CONDITIONAL_AUTHORIZATION = "conditional_authorization"
    ESCALATE_FOR_REJECTION_REVIEW = "escalate_for_rejection_review"
    REQUEST_CLARIFICATION = "request_clarification"

class AssessmentStatus(StrEnum):
    ASSESSED = "assessed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

class EvidenceReference(BaseModel):
    document_id: str
    document_name: str
    page: int | None = None
    section: str | None = None
    excerpt: str

class Finding(BaseModel):
    dimension: RiskDimension
    description: str
    severity: Severity
    confidence: Probability
    evidence: list[EvidenceReference] = Field(default_factory=list)

class DimensionAssessment(BaseModel):
    dimension: RiskDimension
    status: AssessmentStatus
    score: RiskScore | None = None
    rating: RiskRating | None = None
    findings: list[Finding] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list) # Indicate not enough information to assess something properly

class FollowUpQuestion(BaseModel):
    dimension: RiskDimension
    question: str
    reason: str

class AuditMetadata(BaseModel):
    pipeline_version: str
    policy_version: str
    llm_provider: str | None = None
    llm_model: str | None = None

class ReviewerResult(BaseModel):
    submission_id: str
    assessments: list[DimensionAssessment]
    composite_score: RiskScore | None
    recommendation: AuthorizationRecommendation
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)
    audit: AuditMetadata

class SourceType(StrEnum):
    JSON = "json"
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"

class DocumentChunk(BaseModel):
    document_id: str
    document_name: str
    source_type: SourceType
    text: str
    page: int | None = None
    section: str | None = None

class ExtractionResult(BaseModel):
    findings: list[Finding] = Field(default_factory = list)
    missing_information: list[str] = Field(default_factory = list)

class DocumentReference(BaseModel):
    document_id: str
    path: str

class ApplicationSubmission(BaseModel):
    submission_id: str
    applicant_name: str
    activities: list[str] = Field(default_factory = list)
    documents: list[DocumentReference] = Field(default_factory = list)