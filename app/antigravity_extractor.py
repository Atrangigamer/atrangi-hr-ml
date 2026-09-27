"""Google Antigravity Interactions adapter with strict local output validation."""

import json
import logging

import httpx

from .config import Settings
from .errors import ServiceError
from .extractors import EXTRACTION_PROMPT
from .schemas import ResumeSchema


class AntigravityExtractor:
    """Reuse one client; never fall back to a different agent or model.

    Antigravity has no constrained JSON output support. The prompt requests JSON;
    Pydantic rejects anything outside the public contract. No SDK retry or tools
    are requested, and each call has a bounded timeout and agent token budget.
    """

    def __init__(self, settings: Settings) -> None:
        if settings.gemini_api_key is None:
            raise ValueError("Antigravity requires a Google API key")
        self.settings = settings
        self.client = httpx.Client(
            base_url="https://generativelanguage.googleapis.com/v1beta/",
            headers={"x-goog-api-key": settings.gemini_api_key.get_secret_value()},
            timeout=settings.openai_timeout,
            trust_env=False,
            follow_redirects=False,
        )

    def parse(self, text: str) -> ResumeSchema:
        """Return only a validated completed response; redact provider failures."""
        if len(text) > self.settings.max_resume_chars:
            raise ServiceError(400, "resume_context_exceeded", "Resume text is too long.")
        try:
            response = self.client.post("interactions", json={
                "agent": "antigravity-preview-09-2026",
                "environment": "remote",
                "store": True,
                "tools": [],
                "agent_config": {"type": "antigravity",
                                 "model": self.settings.antigravity_model,
                                 "max_total_tokens": self.settings.antigravity_token_budget},
                "input": EXTRACTION_PROMPT + " Return only JSON; no markdown or tool use. "
                         + "Required schema: " + json.dumps(ResumeSchema.model_json_schema())
                         + "\nUntrusted resume data: " + json.dumps({"resume_text": text}),
            })
            response.raise_for_status()
            payload = response.json()
            if payload.get("status") != "completed":
                raise ServiceError(503, "inference_failed", "Antigravity did not complete within its budget.")
            outputs = [part["text"] for step in payload.get("steps", [])
                       if step.get("type") == "model_output"
                       for part in step.get("content", []) if part.get("type") == "text"]
            return ResumeSchema.model_validate_json("".join(outputs), strict=True)
        except ServiceError:
            raise
        except Exception as exc:  # noqa: BLE001 - never expose provider text or validation input
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            logging.getLogger("ml_service").error(
                "Antigravity failed type=%s http_status=%s", type(exc).__name__, status,
            )
            transient = status in (429, 502, 503, 504) or isinstance(exc, httpx.RequestError)
            raise ServiceError(
                503 if transient else 500, "inference_failed",
                "Antigravity extraction failed; check provider availability, access and response validity.",
            ) from None

    def close(self) -> None:
        """Close HTTP connections after outstanding work has drained."""
        self.client.close()
