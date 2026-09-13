from orion.models import RiskDimension, DocumentChunk

DIMENSION_KEYWORDS: dict[RiskDimension, set[str]] = {
    RiskDimension.GOVERNANCE_OWNERSHIP: {
        "ownership",
        "shareholder",
        "director",
        "board",
        "governance",
        "beneficial owner",
        "management"
    },

    RiskDimension.FINANCIAL_RESILIENCE: {
        "revenue",
        "capital",
        "liquidity",
        "cash",
        "debt",
        "financial",
        "profit",
        "loss"
    },

    RiskDimension.OPERATIONAL_RESILIENCE: {
        "business continuity",
        "disaster recovery",
        "backup",
        "recovery",
        "outage",
        "incident",
        "availability",
        "resilience"
    },

    RiskDimension.CYBERSECURITY_DATA: {
        "cybersecurity",
        "security",
        "encryption",
        "access control",
        "data protection",
        "breach",
        "vulnerability",
        "penetration test"
    },

    RiskDimension.COMPLIANCE_INTEGRITY: {
        "compliance",
        "regulatory",
        "audit",
        "sanction",
        "aml",
        "anti-money laundering",
        "fraud",
        "policy"
    }
}

def keyword_score(chunk: DocumentChunk, dimension: RiskDimension) -> int:
    text = chunk.text.lower()

    return sum(1 for keyword in DIMENSION_KEYWORDS[dimension] if keyword in text)

def retrieve_chunks(chunks: list[DocumentChunk], dimension: RiskDimension, limit: int = 10) -> list[DocumentChunk]:
    scored_chunks = [(keyword_score(chunk, dimension), chunk) for chunk in chunks] 

    relevant_chunks = [(score, chunk) for score, chunk in scored_chunks if score > 0]

    relevant_chunks.sort(key = lambda item: item[0], reverse = True) # Only compare scores

    return [chunk for _, chunk in relevant_chunks[:limit]]