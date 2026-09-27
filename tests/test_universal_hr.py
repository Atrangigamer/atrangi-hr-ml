"""Universal-language regressions and backend integration failure contracts."""

import httpx
import pytest

from app.schemas import EmbeddingRequest, ResumeSchema
from app.utils import normalize_text
from integrations.backend_client import MLClient, MLServiceError


@pytest.mark.parametrize("text", ["می\u200cخواهم", "क्\u200dष", "José García", "李明", "مريم أحمد"])
def test_names_and_script_joiners_preserved(text):
    assert normalize_text(text) == text


def test_joiners_alone_are_not_a_visible_passage():
    with pytest.raises(ValueError):
        EmbeddingRequest(text="\u200c\u200d")


def test_international_qualification_is_not_us_only():
    item = ResumeSchema(
        candidate_name="李明",
        email=None,
        skills=["客户服务"],
        experience_years=2.0,
        education=[{"degree": "职业资格证书", "institution": "示例学院", "graduation_year": 2020}],
        summary="客户服务经验。",
    )
    assert item.education[0].degree == "职业资格证书"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,retryable", [(400, False), (422, False), (500, False), (503, True), (302, False)]
)
async def test_backend_error_policy(status, retryable):
    def handler(request):
        return httpx.Response(status, json={"error": {"code": "capacity_busy"}})

    async with MLClient("http://test", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(MLServiceError) as caught:
            await client.embed("Python")
        assert caught.value.status == status
        assert caught.value.retryable is retryable


@pytest.mark.asyncio
async def test_backend_sends_file_and_json():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    async with MLClient("http://test", transport=httpx.MockTransport(handler)) as client:
        assert await client.parse_resume(b"%PDF-test") == {"ok": True}
        assert await client.embed("客户服务") == {"ok": True}
    assert b"%PDF-test" in requests[0].content
    assert "multipart/form-data" in requests[0].headers["content-type"]
    assert requests[1].headers["content-type"] == "application/json"
