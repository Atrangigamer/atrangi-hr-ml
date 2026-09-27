"""Cloud provider selection, resource cleanup and safe error regression tests."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.errors import ServiceError
from app.openai_extractor import OpenAIExtractor
from app.schemas import ResumeSchema


def test_cloud_requires_key_and_redacts_settings():
    with pytest.raises(ValidationError):
        Settings(llm_provider="openai")
    config = Settings(llm_provider="openai", openai_api_key="synthetic-secret")
    assert "synthetic-secret" not in repr(config)


def test_cloud_contract_cleanup_and_failure_redaction():
    config = Settings(llm_provider="openai", openai_api_key="synthetic-secret")
    api = MagicMock()
    structured = MagicMock()
    structured.chat.completions.create.return_value = ResumeSchema(
        candidate_name=None, email=None, skills=[], experience_years=0.0,
        education=[], summary="",
    )
    with patch("app.openai_extractor.OpenAI", return_value=api), patch(
        "app.openai_extractor.instructor.from_openai", return_value=structured
    ):
        extractor = OpenAIExtractor(config)
        assert extractor.parse("synthetic resume").skills == []
        structured.chat.completions.create.side_effect = RuntimeError("secret resume content")
        with pytest.raises(ServiceError) as error:
            extractor.parse("synthetic resume")
        assert "secret resume content" not in str(error.value)
        assert error.value.code == "inference_failed"
        extractor.close()
        api.close.assert_called_once()


def test_cloud_constructor_failure_closes_client():
    with patch("app.openai_extractor.OpenAI") as api, patch(
        "app.openai_extractor.instructor.from_openai", side_effect=RuntimeError("setup")
    ):
        with pytest.raises(RuntimeError):
            OpenAIExtractor(Settings(llm_provider="openai", openai_api_key="synthetic"))
        api.return_value.close.assert_called_once()
