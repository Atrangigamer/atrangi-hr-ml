"""Explicit cloud extraction option via OpenAI-compatible providers."""

import json
import logging

import instructor
from openai import OpenAI

from .config import Settings
from .errors import ServiceError
from .extractors import EXTRACTION_PROMPT
from .schemas import ResumeSchema


class OpenAIExtractor:
    """Reuse one bounded-timeout API client throughout the application lifespan."""

    def __init__(self, settings: Settings) -> None:
        # Instructor's retry logger includes raw provider errors and validation input.
        # Our service boundary emits sanitized failures instead.
        logging.getLogger("instructor.v2.retry").disabled = True
        self.settings = settings
        is_gemini = settings.llm_provider == "gemini"
        key = settings.gemini_api_key if is_gemini else settings.openai_api_key
        self.model = settings.gemini_model if is_gemini else settings.openai_model
        self.max_tokens = settings.gemini_max_tokens if is_gemini else settings.llm_max_tokens
        if key is None:
            raise ValueError("Selected cloud provider requires an API key")
        self.client = OpenAI(
            api_key=key.get_secret_value(),
            base_url=("https://generativelanguage.googleapis.com/v1beta/openai/"
                      if is_gemini else "https://api.openai.com/v1"),
            timeout=settings.openai_timeout,
            max_retries=1,
        )
        try:
            self.structured = instructor.from_openai(self.client, mode=instructor.Mode.JSON_SCHEMA)
        except Exception:
            self.client.close()
            raise

    def parse(self, text: str) -> ResumeSchema:
        """Send extracted text to OpenAI and validate the complete response contract."""
        if len(text) > self.settings.max_resume_chars:
            raise ServiceError(400, "resume_context_exceeded", "Resume text is too long.")
        try:
            result = self.structured.chat.completions.create(
                model=self.model,
                response_model=ResumeSchema,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": json.dumps({"resume_text": text})},
                ],
                max_retries=self.settings.llm_attempts,
                max_tokens=self.max_tokens,
                temperature=0,
            )
            return ResumeSchema.model_validate(result.model_dump(), strict=True)
        except Exception as exc:  # noqa: BLE001 - redact provider exceptions at this boundary
            # SDK/Instructor errors may contain credentials or resume content.
            attempts = getattr(exc, "failed_attempts", None) or []
            cause = attempts[-1].exception if attempts else exc
            # Instructor wraps SDK errors; walk its explicit cause chain without
            # inspecting potentially sensitive exception strings.
            for _ in range(5):
                nested = getattr(cause, "__cause__", None)
                if nested is None:
                    break
                cause = nested
            status = getattr(cause, "status_code", None)
            logging.getLogger("ml_service").error(
                "Cloud extraction failed provider=%s error_type=%s http_status=%s",
                self.settings.llm_provider, type(cause).__name__,
                status if isinstance(status, int) else None,
            )
            if status in (429, 502, 503, 504):
                raise ServiceError(
                    503, "inference_failed",
                    "Cloud provider is temporarily unavailable or rate limited; retry later.",
                ) from None
            raise ServiceError(
                500, "inference_failed",
                "Cloud extraction failed; check credentials, model access, quota and network.",
            ) from None

    def close(self) -> None:
        """Close network connections after outstanding inference drains."""
        self.client.close()
