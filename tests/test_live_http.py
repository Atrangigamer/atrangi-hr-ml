"""Real TCP/Uvicorn integration; model doubles isolate hardware dependencies."""

import asyncio
import socket
import threading
import time
from unittest.mock import patch

import httpx
import uvicorn
from test_service import FakeEmbedder, FakeExtractor, pdf_bytes

from app.main import create_app


def test_live_server_mixed_requests_and_shutdown():
    """Exercise actual HTTP multipart/JSON parsing, load and graceful shutdown."""
    with (
        patch("app.main.Embedder", FakeEmbedder),
        patch("app.main.ResumeExtractor", FakeExtractor),
    ):
        app = create_app()
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        address = f"http://127.0.0.1:{listener.getsockname()[1]}"
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                log_level="critical",
                access_log=False,
                lifespan="on",
                loop="asyncio",
                timeout_graceful_shutdown=5,
            )
        )
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 5
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert server.started

            async def exercise():
                async with httpx.AsyncClient(
                    base_url=address, timeout=10, trust_env=False
                ) as client:
                    assert (await client.get("/health/ready")).status_code == 200
                    sample = pdf_bytes()
                    results = await asyncio.gather(
                        *[
                            client.post(
                                "/ml/parse-resume",
                                files={"file": ("resume.pdf", sample, "application/pdf")},
                            )
                            if n % 2
                            else client.post("/ml/generate-embedding", json={"text": "Python"})
                            for n in range(40)
                        ]
                    )
                    assert all(r.status_code == 200 for r in results)
                    bad = await client.post(
                        "/ml/parse-resume",
                        content=b"bad",
                        headers={"Content-Type": "multipart/form-data"},
                    )
                    assert bad.status_code == 400 and "error" in bad.json()
                    failure = await client.post("/ml/generate-embedding", json={"text": "fail"})
                    assert failure.status_code == 500
                    recovery = await client.post(
                        "/ml/generate-embedding", json={"text": "recovery"}
                    )
                    assert recovery.status_code == 200

            asyncio.run(exercise())
        finally:
            server.should_exit = True
            thread.join(10)
            listener.close()
        assert not thread.is_alive()
        assert not app.state.ready
        assert app.state.embedder is None and app.state.extractor is None
