import json
from pydantic import ValidationError, BaseModel
from orion.models import RiskDimension, DocumentChunk, ExtractionResult, Severity, Probability, Finding, EvidenceReference
from orion.llm import LLMProvider

class RawEvidenceReference(BaseModel):
    source_id: str
    excerpt: str

class RawFinding(BaseModel):
    description: str
    severity: Severity
    confidence: Probability
    evidence: list[RawEvidenceReference]

class RawExtractionResult(BaseModel):
    findings: list[RawFinding]
    missing_information: list[str]

def build_extraction_prompt(dimension: RiskDimension, chunks: list[DocumentChunk]) -> str:
    evidence_text = "\n\n".join(
        f"[SOURCE S{index}]\n"
        f"Document: {chunk.document_name}\n"
        f"Page: {chunk.page}\n"
        f"Section: {chunk.section}\n"
        f"Text: {chunk.text}"
        for index, chunk in enumerate(chunks, start=1)
    )

    return f"""
        You are extracting evidence for the ORION risk assessment pipeline.

        Risk dimension:{dimension.value}

        Use only the supplied evidence.

        Return valid JSON with this shape:

        {{
            "findings": [
                {{
                    "description": "short factual finding",
                    "severity": "low | medium | high | critical",
                    "confidence": 0.0,
                    "evidence": [
                        {{
                            "source_id": "S1",
                            "excerpt": "exact supporting excerpt"
                        }}
                    ]
                }}
            ],
            "missing_information": []
        }}

        Only use source IDs that are provided below.

        The excerpt must come directly from the corresponding source.

        Do not invent evidence.

        Evidence:{evidence_text}
        """.strip()

def extract_dimension(provider: LLMProvider, dimension: RiskDimension, chunks: list[DocumentChunk]) -> ExtractionResult:
    prompt = build_extraction_prompt(dimension, chunks)

    raw_response = provider.generate(prompt)

    try:
        data = json.loads(raw_response)
        raw_result = RawExtractionResult.model_validate(data)

    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("LLM returned invalid extraction output") from exc

    source_map = {f"S{index}": chunk for index, chunk in enumerate(chunks, start = 1)}

    findings: list[Finding] = []

    for raw_finding in raw_result.findings:
        evidence: list[EvidenceReference] = []

        for raw_evidence in raw_finding.evidence:
            chunk = source_map.get(raw_evidence.source_id)

            if chunk is None:
                raise ValueError(f"LLM referenced unknown source: {raw_evidence.source_id}")

            if raw_evidence.excerpt not in chunk.text:
                raise ValueError(f"LLM returned unsupportted excerpt for {raw_evidence.source_id}")

            evidence.append(
                EvidenceReference(
                    document_id = chunk.document_id,
                    document_name = chunk.document_name,
                    page = chunk.page,
                    section = chunk.section,
                    excerpt = raw_evidence.excerpt
                )
            )

        findings.append(
            Finding(
                dimension = dimension,
                description = raw_finding.description,
                severity = raw_finding.severity,
                confidence = raw_finding.confidence,
                evidence = evidence
            )
        )

    return ExtractionResult(
        findings = findings,
        missing_information = raw_result.missing_information
    )