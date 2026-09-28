"""Admission bounds bodies while allowing health checks and idle connections."""

import asyncio

import pytest

from app.main import RequestAdmissionMiddleware


@pytest.mark.asyncio
async def test_admission_rejects_without_reading_body_and_recovers():
    entered = asyncio.Event()
    finish = asyncio.Event()
    messages = []

    async def app(scope, receive, send):
        if scope["method"] == "POST":
            entered.set()
            await finish.wait()

    async def receive():
        raise AssertionError("Overload must not read uploaded bytes")

    async def send(message):
        messages.append(message)

    gate = RequestAdmissionMiddleware(app, limit=1)
    task = asyncio.create_task(gate({"type": "http", "method": "POST"}, receive, send))
    await entered.wait()
    await gate({"type": "http", "method": "GET"}, receive, send)
    await gate({"type": "http", "method": "POST"}, receive, send)
    assert messages[0]["status"] == 503
    assert (b"retry-after", b"5") in messages[0]["headers"]
    assert b"capacity_busy" in messages[1]["body"]
    finish.set()
    await task
    assert gate.active == 0
    await gate({"type": "http", "method": "POST"}, receive, send)
    assert gate.active == 0


@pytest.mark.asyncio
async def test_admission_releases_after_cancellation():
    started = asyncio.Event()

    async def app(scope, receive, send):
        started.set()
        await asyncio.Event().wait()

    gate = RequestAdmissionMiddleware(app, limit=1)
    task = asyncio.create_task(gate({"type": "http", "method": "POST"}, None, None))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert gate.active == 0
