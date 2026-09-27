"""Contract, isolation and failure handling for the Interactions adapter."""

import json

import httpx
import pytest
from pydantic import ValidationError

from app.antigravity_extractor import AntigravityExtractor
from app.config import Settings
from app.errors import ServiceError


@pytest.mark.parametrize("status,payload,expected", [
    (200, {"status": "incomplete"}, 503),
    (200, {"status": "completed", "steps": []}, 500),
    (200, {"status": "completed", "steps": [{"type": "model_output", "content": [
        {"type": "text", "text": "PRIVATE invalid JSON"}]}]}, 500),
    (429, {"error": "PRIVATE"}, 503),
    (503, {"error": "PRIVATE"}, 503),
    (401, {"error": "PRIVATE"}, 500),
])
def test_failure_redaction(status, payload, expected):
    extractor = AntigravityExtractor(Settings(llm_provider="antigravity", gemini_api_key="test"))
    extractor.client.close()
    extractor.client = httpx.Client(base_url="https://example.invalid/", transport=httpx.MockTransport(
        lambda request: httpx.Response(status, json=payload)))
    try:
        with pytest.raises(ServiceError) as error:
            extractor.parse("PRIVATE resume")
        assert error.value.status == expected
        assert "PRIVATE" not in str(error.value)
    finally:
        extractor.close()


def test_selected_model_and_validated_response():
    config = Settings(llm_provider="antigravity", gemini_api_key="test")
    extractor = AntigravityExtractor(config)
    extractor.client.close()
    result = dict(candidate_name=None, email=None, skills=[], experience_years=0.0,
                  education=[], summary="")

    def respond(request):
        body = json.loads(request.content)
        assert body["agent"] == "antigravity-preview-09-2026"
        assert body["agent_config"]["model"] == "gemini-3.7-flash"
        assert body["store"] is True
        assert body["tools"] == []
        assert body["agent_config"]["max_total_tokens"] == 8192
        return httpx.Response(200, json={"status": "completed", "steps": [
            {"type": "model_output", "content": [{"type": "text", "text": json.dumps(result)}]}]})

    extractor.client = httpx.Client(base_url="https://example.invalid/", transport=httpx.MockTransport(respond))
    try:
        assert extractor.parse("Synthetic unknown candidate").model_dump() == result
    finally:
        extractor.close()


def test_antigravity_requires_nonblank_google_key():
    with pytest.raises(ValidationError):
        Settings(llm_provider="antigravity", gemini_api_key=" ")
