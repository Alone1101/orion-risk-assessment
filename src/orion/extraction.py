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
                    "confidence": 0.5,
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

        Confidence represents how strongly the supplied evidence supports the finding, not the likelihood that missing information exists.

        Use higher confidence when the finding is explicitly stated in the evidence.

        Use lower confidence when the finding requires interpretation or inference.

        Confidence measures how directly the supplied evidence supports the finding.

        Choose the value based on the evidence:
        - 0.90-1.00: explicitly and unambiguously stated
        - 0.70-0.89: strongly supported with minor interpretation
        - 0.50-0.69: moderately supported and requires inference
        - below 0.50: weak or ambiguous support

        Do not copy the example confidence value automatically.

        A finding and missing information are not mutually exclusive.

        If the evidence explicitly states that required information, documentation, testing, reports, or controls were not provided or cannot be established:
        1. Record the evidence-backed issue as a finding when it is risk-relevant.
        2. Also add the absent information to "missing_information".

        Example:
        Evidence: "The latest penetration test report was not provided."

        This may produce:
        - a finding that the penetration test report is unavailable; and 
        - missing_information containing "Latest penetration test report."

        If supplied sources contain materially contradictory or inconsistent information:
        1. Record the inconsistency as a finding when it is risk-relevant.
        2. Add the information requiring clarification to "missing_information".
        3. Cite evidence supporting the contradiction.

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