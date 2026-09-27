"""CPU contract tests; native CUDA/model integration is tested on deployment."""

import asyncio
import io
import threading
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from app.config import Settings
from app.errors import InvalidPDF, ServiceError
from app.extractors import extract_pdf_text
from app.main import create_app
from app.runtime import BoundedRunner
from app.schemas import ResumeSchema
from app.utils import cosine_similarity, normalize_text


def pdf_bytes(text: str = "atrangi - Python Engineer") -> bytes:
    """Create a tiny, text-bearing PDF entirely in memory."""
    output = io.BytesIO()
    document = canvas.Canvas(output)
    document.drawString(60, 700, text)
    document.showPage()
    document.save()
    return output.getvalue()


def resume() -> ResumeSchema:
    return ResumeSchema(
        candidate_name="atrangi",
        email=None,
        skills=["Python"],
        experience_years=0.0,
        education=[],
        summary="Python engineer",
    )


class FakeEmbedder:
    loads = 0
    closed = 0

    def __init__(self, _: str) -> None:
        type(self).loads += 1

    def embed(self, text: str) -> list[float]:
        if text == "fail":
            raise RuntimeError("PRIVATE RESUME CONTENT")
        return [1.0] + [0.0] * 383

    def close(self) -> None:
        type(self).closed += 1


class FakeExtractor:
    loads = 0
    closed = 0

    def __init__(self, _: Settings) -> None:
        type(self).loads += 1

    def parse(self, text: str) -> ResumeSchema:
        if "trigger_failure" in text:
            raise RuntimeError("PRIVATE RESUME CONTENT")
        return resume()

    def close(self) -> None:
        type(self).closed += 1


@pytest.fixture
def client():
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        with TestClient(create_app(), raise_server_exceptions=False) as test:
            yield test


def test_both_endpoints_and_single_load():
    loads = FakeEmbedder.loads, FakeExtractor.loads
    closes = FakeEmbedder.closed, FakeExtractor.closed
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        with TestClient(create_app()) as client:
            for _ in range(2):
                parsed = client.post(
                    "/ml/parse-resume",
                    files={"file": ("resume.pdf", pdf_bytes(), "application/pdf")},
                )
                assert parsed.status_code == 200
                assert ResumeSchema.model_validate(parsed.json()) == resume()
                vector = client.post("/ml/generate-embedding", json={"text": "Python"})
                assert vector.status_code == 200
                assert len(vector.json()["embedding"]) == vector.json()["dimensions"] == 384
            assert client.get("/health/ready").status_code == 200
            assert (FakeEmbedder.loads, FakeExtractor.loads) == (
                loads[0] + 1,
                loads[1] + 1,
            )
    assert (FakeEmbedder.closed, FakeExtractor.closed) == (closes[0] + 1, closes[1] + 1)


@pytest.mark.parametrize("body", [{"text": "   "}, {"text": 12}, {"text": "x", "extra": True}, {}])
def test_invalid_json(client, body):
    assert client.post("/ml/generate-embedding", json=body).status_code == 422


@pytest.mark.parametrize("data", [b"", b"bad", b"%PDF-1.7\nbroken", pdf_bytes("")])
def test_invalid_pdf(client, data):
    response = client.post("/ml/parse-resume", files={"file": ("bad.pdf", data, "application/pdf")})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_pdf"


def test_inference_failure_is_safe(client):
    response = client.post("/ml/generate-embedding", json={"text": "fail"})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "inference_failed"
    assert "PRIVATE" not in response.text
    response = client.post(
        "/ml/parse-resume",
        files={"file": ("resume.pdf", pdf_bytes("trigger_failure"), "application/pdf")},
    )
    assert response.status_code == 500
    assert "PRIVATE" not in response.text


def test_fallback_and_encrypted_pdf():
    data = pdf_bytes()
    with patch("app.extractors.pdfplumber.open", side_effect=RuntimeError("parser failure")):
        assert "atrangi" in extract_pdf_text(data, Settings())
    writer = PdfWriter()
    writer.append(PdfReader(io.BytesIO(data)))
    writer.encrypt("secret")
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(InvalidPDF, match="Encrypted"):
        extract_pdf_text(stream.getvalue(), Settings())


def test_pdf_size_and_page_limits():
    with pytest.raises(InvalidPDF, match="upload limit"):
        extract_pdf_text(pdf_bytes(), Settings(max_pdf_bytes=1024))
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(InvalidPDF, match="pages"):
        extract_pdf_text(output.getvalue(), Settings(max_pdf_pages=1))


def test_request_body_limit():
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        with TestClient(create_app(Settings(max_pdf_bytes=1024))) as client:
            response = client.post("/ml/parse-resume", content=b"x" * 70000)
            assert response.status_code == 413


def test_schema_rejects_hallucinated_shape():
    values = resume().model_dump()
    for replacement in (
        {"experience_years": -1.0},
        {"experience_years": float("nan")},
        {"skills": "Python"},
        {"unexpected": "key"},
    ):
        with pytest.raises(ValidationError):
            ResumeSchema.model_validate(values | replacement)


def test_text_and_cosine():
    assert normalize_text("\x00  Python\t engineer\r\n\u200b Resume  ") == "Python engineer\nResume"
    assert cosine_similarity([1, 0], [0, 1]) == 0
    assert cosine_similarity([1e300, 1e300], [1e300, 1e300]) == pytest.approx(1)
    assert cosine_similarity([1, 0], [-1, 0]) == -1


@pytest.mark.parametrize(
    "a,b",
    [([], []), ([1], [1, 2]), ([0], [1]), ([float("inf")], [1]), ([float("nan")], [1])],
)
def test_invalid_cosine(a, b):
    with pytest.raises(ValueError):
        cosine_similarity(a, b)


@pytest.mark.asyncio
async def test_cancellation_does_not_release_gpu_early():
    gate = BoundedRunner(1, 0.05)
    started, release = threading.Event(), threading.Event()

    def native_operation():
        started.set()
        release.wait(5)
        return 42

    task = asyncio.create_task(gate.run(native_operation))
    await asyncio.to_thread(started.wait, 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    try:
        with pytest.raises(ServiceError) as caught:
            await gate.run(lambda: 0)
        assert caught.value.status == 503
    finally:
        release.set()
        await gate.drain()
    assert await gate.run(lambda: 7) == 7


def test_startup_failure_closes_embedding():
    before = FakeEmbedder.closed
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", side_effect=RuntimeError("load failed")),
    ):
        with pytest.raises(RuntimeError, match="load failed"):
            with TestClient(create_app()):
                pass
    assert FakeEmbedder.closed == before + 1


def test_real_instructor_adapter_and_retry(tmp_path):
    """Exercise actual Instructor with fake native completions, no GPU required."""
    import sys
    from types import SimpleNamespace

    from openai.types.chat import ChatCompletion

    from app.extractors import ResumeExtractor

    calls = []

    class NativeLlama:
        def __init__(self, **kwargs):
            assert kwargs["n_gpu_layers"] in (-1, 0)
            assert "main_gpu" not in kwargs
            assert "split_mode" not in kwargs

        def tokenize(self, _: bytes):
            return [1] * 50

        def create_chat_completion_openai_v1(self, **kwargs):
            calls.append(kwargs)
            assert kwargs["response_format"]["type"] == "json_object"
            assert "candidate_name" in kwargs["response_format"]["schema"]["properties"]
            # First response violates a semantic schema constraint; retry succeeds.
            value = resume().model_dump()
            if len(calls) == 1:
                value["experience_years"] = -1.0
            import json

            return ChatCompletion(
                id="test",
                created=0,
                model="local",
                object="chat.completion",
                choices=[
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(value)},
                    }
                ],
            )

        def close(self):
            pass

    model_path = tmp_path / "test.gguf"
    model_path.touch()
    for gpu_available in (True, False):
        calls.clear()
        module = SimpleNamespace(
            Llama=NativeLlama,
            llama_supports_gpu_offload=lambda ga=gpu_available: ga,
        )
        with patch.dict(sys.modules, {"llama_cpp": module}):
            extractor = ResumeExtractor(Settings(llm_model_path=model_path))
            assert extractor.parse("Example resume") == resume()
            assert len(calls) == 2
            extractor.close()
