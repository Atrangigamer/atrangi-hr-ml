"""Regression tests for provider isolation and cloud configuration."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.errors import ServiceError
from app.openai_extractor import OpenAIExtractor


@pytest.mark.parametrize("provider", ["openai", "gemini"])
def test_blank_cloud_keys_rejected(provider):
    with pytest.raises(ValidationError):
        Settings(llm_provider=provider, **{f"{provider}_api_key": "   "})


def test_cloud_configuration_does_not_require_local_context():
    config = Settings(llm_provider="gemini", gemini_api_key="synthetic", llm_context=2048)
    assert config.llm_provider == "gemini"


def test_gemini_uses_only_its_own_credential_and_endpoint():
    settings = Settings(llm_provider="gemini", gemini_api_key="gemini-test",
                        openai_api_key="openai-test")
    with patch("app.openai_extractor.OpenAI") as client, patch(
        "app.openai_extractor.instructor.from_openai"
    ):
        extractor = OpenAIExtractor(settings)
        assert client.call_args.kwargs["api_key"] == "gemini-test"
        assert client.call_args.kwargs["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
        assert extractor.model == settings.gemini_model
        assert extractor.max_tokens == settings.gemini_max_tokens
        extractor.close()


def test_wrapped_provider_outage_is_retryable_and_redacted():
    class ProviderFailure(Exception):
        status_code = 503

    cause = ProviderFailure("private upstream contents")
    wrapper = RuntimeError("private wrapper contents")
    wrapper.__cause__ = cause
    with patch("app.openai_extractor.OpenAI"), patch(
        "app.openai_extractor.instructor.from_openai"
    ) as adapter:
        adapter.return_value.chat.completions.create.side_effect = wrapper
        extractor = OpenAIExtractor(Settings(llm_provider="gemini", gemini_api_key="test"))
        with pytest.raises(ServiceError) as error:
            extractor.parse("synthetic")
        assert error.value.status == 503
        assert "private" not in str(error.value)
        extractor.close()
