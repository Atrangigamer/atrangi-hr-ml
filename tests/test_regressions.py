"""Failure-injection and stress regressions discovered during iterative review."""

import asyncio
import threading
import time
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from test_service import FakeEmbedder, FakeExtractor, pdf_bytes

from app.config import Settings
from app.errors import ServiceError
from app.extractors import extract_pdf_text
from app.main import create_app
from app.runtime import BoundedRunner


@pytest.mark.asyncio
async def test_embedding_without_lifespan_is_503():
    app = create_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        result = await client.post("/ml/generate-embedding", json={"text": "Python"})
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "not_ready"


def test_documented_gpu_concurrency_environment(monkeypatch):
    monkeypatch.setenv("ML_GPU_CONCURRENCY", "1")
    assert Settings().gpu_concurrency == 1


def test_exact_pdf_character_limit_is_accepted():
    text = "x" * 100
    assert extract_pdf_text(pdf_bytes(text), Settings(max_resume_chars=100)) == text


def test_cleanup_failure_does_not_skip_other_model():
    before = FakeEmbedder.closed

    class BadClose(FakeExtractor):
        def close(self):
            raise RuntimeError("native close failed")

    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", BadClose),
    ):
        try:
            with TestClient(create_app()):
                pass
        except RuntimeError:
            pass
    assert FakeEmbedder.closed == before + 1


@pytest.mark.asyncio
async def test_cancelled_startup_closes_late_loaded_model():
    started, release = threading.Event(), threading.Event()
    closed = []

    class SlowLoad(FakeEmbedder):
        def __init__(self, _):
            started.set()
            release.wait(3)

        def close(self):
            closed.append(True)

    with (
        patch("app.main.Embedder", SlowLoad),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        app = create_app()

        async def start():
            async with app.router.lifespan_context(app):
                pass

        task = asyncio.create_task(start())
        assert await asyncio.to_thread(started.wait, 2)
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.05)
    assert closed == [True]


@pytest.mark.asyncio
async def test_runner_shutdown_rejects_new_work():
    runner = BoundedRunner(1, 0.5)
    await runner.aclose()
    with pytest.raises(ServiceError) as caught:
        await runner.run(lambda: 1)
    assert caught.value.status == 503


@pytest.mark.asyncio
async def test_mixed_parallel_api_work_is_serial_on_gpu():
    lock = threading.Lock()
    active = 0
    maximum = 0

    def work():
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        time.sleep(0.001)
        with lock:
            active -= 1

    class SlowEmbedder(FakeEmbedder):
        def embed(self, text):
            work()
            return super().embed(text)

    class SlowExtractor(FakeExtractor):
        def parse(self, text):
            work()
            return super().parse(text)

    with (
        patch("app.main.Embedder", SlowEmbedder),
        patch("app.main.ResumeExtractor", SlowExtractor),
    ):
        app = create_app(Settings(max_active_requests=128))
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                data = pdf_bytes()
                requests = [
                    client.post(
                        "/ml/parse-resume",
                        files={"file": ("resume.pdf", data, "application/pdf")},
                    )
                    if n % 2
                    else client.post("/ml/generate-embedding", json={"text": "Python"})
                    for n in range(100)
                ]
                results = await asyncio.gather(*requests)
                assert all(result.status_code == 200 for result in results)
                assert not app.state.gpu.pending
        assert maximum == 1


def test_malformed_multipart_has_consistent_error_envelope():
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        with TestClient(create_app()) as client:
            response = client.post(
                "/ml/parse-resume",
                content=b"invalid",
                headers={"Content-Type": "multipart/form-data"},
            )
    assert response.status_code == 400
    assert "error" in response.json()


def test_fallback_recovers_individual_empty_pages():
    import io
    from contextlib import nullcontext
    from types import SimpleNamespace

    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    for text in ("First page", "Second page"):
        pdf.drawString(60, 700, text)
        pdf.showPage()
    pdf.save()
    document = SimpleNamespace(
        pages=[
            SimpleNamespace(extract_text=lambda: "First page"),
            SimpleNamespace(extract_text=lambda: ""),
        ]
    )
    with patch("app.extractors.pdfplumber.open", return_value=nullcontext(document)):
        text = extract_pdf_text(output.getvalue(), Settings())
    assert "First page" in text and "Second page" in text


@pytest.mark.asyncio
async def test_shutdown_rejects_already_queued_work():
    runner = BoundedRunner(1, 2)
    started, release = threading.Event(), threading.Event()

    def block():
        started.set()
        release.wait(3)

    active = asyncio.create_task(runner.run(block))
    assert await asyncio.to_thread(started.wait, 2)
    called = []
    queued = asyncio.create_task(runner.run(lambda: called.append(True)))
    await asyncio.sleep(0)
    closing = asyncio.create_task(runner.aclose())
    await asyncio.sleep(0)
    release.set()
    await active
    await closing
    with pytest.raises(ServiceError):
        await queued
    assert not called


@pytest.mark.asyncio
async def test_cancelling_drain_does_not_cancel_native_task():
    runner = BoundedRunner(1, 2)
    started, release = threading.Event(), threading.Event()

    def block():
        started.set()
        release.wait(3)
        return 42

    active = asyncio.create_task(runner.run(block))
    assert await asyncio.to_thread(started.wait, 2)
    drain = asyncio.create_task(runner.drain())
    await asyncio.sleep(0)
    drain.cancel()
    await asyncio.sleep(0)
    drain.cancel()
    await asyncio.sleep(0)
    assert not drain.done()
    assert runner.pending
    release.set()
    assert await active == 42
    with pytest.raises(asyncio.CancelledError):
        await drain
    assert await runner.run(lambda: 7) == 7


def test_seeded_bad_input_corpus_never_returns_500():
    import random

    randomizer = random.Random(729)
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            for _ in range(100):
                # Invalid binary/PDF-like content with deterministic reproduction.
                data = b"%PDF-1.7\n" + randomizer.randbytes(randomizer.randrange(0, 300))
                response = client.post(
                    "/ml/parse-resume",
                    files={"file": ("fuzz.pdf", data, "application/pdf")},
                )
                assert response.status_code == 400
            for value in (
                None,
                0,
                False,
                [],
                {},
                "\x00",
                "\u200b",
                " " * 500,
                "x" * 12001,
            ):
                response = client.post("/ml/generate-embedding", json={"text": value})
                assert response.status_code == 422


@pytest.mark.asyncio
async def test_chunked_body_limit_counts_actual_bytes():
    from app.main import BodyLimitMiddleware

    called = []
    sent = []

    async def downstream(scope, receive, send):
        called.append(True)

    chunks = iter(
        [
            {"type": "http.request", "body": b"a" * 60, "more_body": True},
            {"type": "http.request", "body": b"b" * 60, "more_body": False},
        ]
    )

    async def receive():
        return next(chunks)

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "headers": [(b"content-length", b"1")]}
    await BodyLimitMiddleware(downstream, 100)(scope, receive, send)
    assert not called
    assert sent[0]["status"] == 413
