import httpx, pytest
from orion.models import ReviewerResult, AuthorizationRecommendation, AuditMetadata
from orion.delivery import deliver_result

def test_deliver_result_posts_reviewer_payload():
    received_payload = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received_payload["body"] = request.content
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)

    result = ReviewerResult(
        submission_id = "ORION-TEST-001",
        assessments = [],
        composite_score = 20.0,
        recommendation = AuthorizationRecommendation.STANDARD_REVIEW,
        audit = AuditMetadata(
            pipeline_version = "0.1.0",
            policy_version = "demo-policy-v1"
        )
    )

    with httpx.Client(transport = transport) as client:
        deliver_result(
            result = result,
            url = "https://review.example.test/results",
            client = client
        )

    # Bytes appear in raw HTTP request body
    assert b"ORION-TEST-001" in received_payload["body"]
    assert b"standard_review" in received_payload["body"]

def test_deliver_result_raises_on_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request = request)

    transport = httpx.MockTransport(handler)

    result = ReviewerResult(
        submission_id = "ORION-TEST-002",
        assessments = [],
        composite_score = 20.0,
        recommendation = AuthorizationRecommendation.STANDARD_REVIEW,
        audit = AuditMetadata(
            pipeline_version = "0.1.0",
            policy_version = "demo-policy-v1"
        )
    )

    with httpx.Client(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            deliver_result(
                result = result,
                url = "https://review.example.test/results",
                client = client
            )