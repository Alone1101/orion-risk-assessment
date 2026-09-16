import time
from orion.models import Severity, ReviewerResult, AssessmentStatus
from orion.llm import OllamaProvider
from orion.pipeline import run_assessment
from cases import EVALUATION_CASES, build_chunks

SEVERITY_ORDER = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3
}

def evaluate_result(case, result: ReviewerResult) -> list[str]:
    failures: list[str] = []

    assessments = {assessment.dimension: assessment for assessment in result.assessments}

    for expected in case.expected_findings:
        assessment = assessments[expected.dimension]

        matching_findings = [
            finding
            for finding in assessment.findings
            if SEVERITY_ORDER[finding.severity] >= SEVERITY_ORDER[expected.minimum_severity]
        ]

        if not matching_findings:
            failures.append(f"No {expected.dimension.value} finding with severity >= {expected.minimum_severity.value}")

    for dimension in case.expected_missing_dimensions:
        assessment = assessments[dimension]

        if assessment.status != AssessmentStatus.INSUFFICIENT_EVIDENCE:
            failures.append(f"{dimension.value} was not marked insufficient_evidence")

    if case.expected_composite and result.composite_score is None:
        failures.append("Expected a composite score but assessment was imcomplete")

    return failures

def main() -> None:
    provider = OllamaProvider()

    passed = 0
    latencies: list[float] = []

    for case in EVALUATION_CASES:
        print(f"\n=== {case.name} ===")

        chunks = build_chunks(case)

        start = time.perf_counter()

        result = run_assessment(
            submission_id = f"EVAL-{case.name}",
            provider = provider,
            chunks = chunks
        )

        elapsed = time.perf_counter() - start

        latencies.append(elapsed)

        failures = evaluate_result(case, result)
        
        if failures:
            print("Result: FAIL")
            for failure in failures:
                print(f" - {failure}")
        else:
            passed += 1
            print("Result: PASS")

        print(f"Latency: {elapsed:.2f}s")

    total = len(EVALUATION_CASES)
    total_latency = sum(latencies)
    mean_latency = total_latency / total

    print("\n=== Evaluation Summary ===")
    print(f"Cases passed: {passed}/{total}")
    print(f"Pass rate: {(passed / total) * 100:.1f}%")
    print(f"Total latency: {total_latency:.2f}s")
    print(f"Mean latency: {mean_latency:.2f}s")

if __name__ == "__main__":
    main()