"""Hazma's reusable asynchronous ML client; backend owns jobs and retry policy."""

from typing import Any

import httpx


class MLServiceError(Exception):
    """Safe upstream failure without exposing document contents."""

    def __init__(self, status: int, code: str, retryable: bool) -> None:
        super().__init__(f"ML request failed: status={status}, code={code}")
        self.status, self.code, self.retryable = status, code, retryable


class MLClient:
    """Reuse one client per async worker/event loop and close it on shutdown.

    Supply the private service URL explicitly. Do not create one client across
    multiple event loops in synchronous Celery tasks; wrap a complete async call
    and its context manager in each such task instead.
    """

    def __init__(self, base_url: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.client = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout=httpx.Timeout(300, connect=10),
            trust_env=False,
        )

    async def __aenter__(self) -> "MLClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.client.aclose()

    async def _post(self, route: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = await self.client.post(route, **kwargs)
        except httpx.RequestError as exc:
            # Timeouts are indeterminate; GPU work may still be executing.
            raise MLServiceError(0, "transport_failure", True) from exc
        if not response.is_success:
            # Avoid returning arbitrary upstream text or candidate PII.
            code = "upstream_failure"
            try:
                known = response.json().get("error", {}).get("code")
                if known in {
                    "invalid_pdf",
                    "invalid_request",
                    "request_too_large",
                    "resume_context_exceeded",
                    "embedding_text_too_long",
                    "capacity_busy",
                    "not_ready",
                    "shutting_down",
                    "inference_failed",
                }:
                    code = known
            except (ValueError, AttributeError, TypeError):
                pass
            raise MLServiceError(
                response.status_code, code, response.status_code in (429, 502, 503, 504)
            )
        try:
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError("Expected an object")
            return result
        except ValueError as exc:
            raise MLServiceError(502, "invalid_upstream_json", False) from exc

    async def parse_resume(self, pdf: bytes) -> dict[str, Any]:
        """Send multipart bytes; persist results once under a backend job ID."""
        return await self._post(
            "/ml/parse-resume", files={"file": ("resume.pdf", pdf, "application/pdf")}
        )

    async def embed(self, text: str) -> dict[str, Any]:
        """Embed a short passage; validate against the shared response schema."""
        return await self._post("/ml/generate-embedding", json={"text": text})
