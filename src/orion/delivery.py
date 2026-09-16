import logging, httpx
from orion.models import ReviewerResult

logger = logging.getLogger(__name__)

def deliver_result(result: ReviewerResult, url: str, timeout: float = 10.0, client: httpx.Client | None = None) -> None:
    logger.info(
        "Delivering reviewer result submission_id = %s",
        result.submission_id
    )

    if client is None:
        response = httpx.post(
            url,
            json = result.model_dump(mode = "json"),
            timeout = timeout
        )
    else:
        response = client.post(
            url,
            json = result.model_dump(mode = "json"),
            timeout = timeout
        )

    response.raise_for_status()

    logger.info(
        "Reviewer result delivered submission_id = %s status_code = %d",
        result.submission_id,
        response.status_code
    )