from pathlib import Path
from orion.ingestion import parse_document
from orion.chunking import split_chunks
from orion.models import RiskDimension
from orion.retrieval import retrieve_chunks

FIXTURE_PATH = Path("evals/fixtures/large_regulatory_application.docx")

EXPECTED_EVIDENCE = {
    RiskDimension.GOVERNANCE_OWNERSHIP: ["beneficial owners"],

    RiskDimension.FINANCIAL_RESILIENCE: ["liquidity", "capital reserves"],

    RiskDimension.OPERATIONAL_RESILIENCE: ["disaster recovery testing report was not provided"],

    RiskDimension.CYBERSECURITY_DATA: ["privileged accounts did not consistently enforce"],
    
    RiskDimension.COMPLIANCE_INTEGRITY: ["anti-money laundering"]
}

def main() -> None:
    ingested_chunks = parse_document(
        path = FIXTURE_PATH,
        document_id = "eval-large-application"
    )

    chunks = split_chunks(ingested_chunks)

    total_characters = sum(len(chunk.text) for chunk in chunks)

    print("=== Preprocessing Efficiency ===")
    print(f"Ingested chunks: {len(ingested_chunks)}")
    print(f"Chunks after splitting: {len(chunks)}")
    print(f"Total characters: {total_characters:,}")
    print()

    for dimension in RiskDimension:
        print(dimension.value)
        
        retrieved = retrieve_chunks(chunks, dimension, limit = 10)

        retrieved_characters = sum(len(chunk.text) for chunk in retrieved)
        
        reduction = ((total_characters - retrieved_characters) / total_characters * 100)

        retrieved_text = " ".join(chunk.text.lower() for chunk in retrieved)

        expected_terms = EXPECTED_EVIDENCE[dimension]

        evidence_found = all(term.lower() in retrieved_text for term in expected_terms)

        print(f"  Retrieved chunks: {len(retrieved)}")
        print(f"  Characters sent to LLM: {retrieved_characters:,}")
        print(f"  Text reduction: {reduction:.1f}%")
        print(f"  Expected evidence retained: {'PASS' if evidence_found else 'FAIL'}")

if __name__ == "__main__":
    main()