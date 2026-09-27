"""Cancellation-safe concurrency limits for native synchronous inference."""

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from .errors import ServiceError

T = TypeVar("T")


async def finish_before_cancelling(task: asyncio.Task[T]) -> T:
    """Defer caller cancellation until a cleanup task actually finishes.

    A second cancellation must not cancel native work or model cleanup either.
    The original cancellation is re-raised once the task is safely complete.
    """
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.cancelled():
                raise
            cancelled = True
    if cancelled:
        task.exception()
        raise asyncio.CancelledError
    return task.result()


class BoundedRunner:
    """Hold an asyncio semaphore until native work finishes, even on disconnect.

    asyncio.to_thread cannot forcibly stop a native GPU operation. Shielding the
    task and releasing the permit in its completion callback avoids accidentally
    allowing a second inference after a request has been cancelled.
    """

    def __init__(self, concurrency: int, queue_timeout: float) -> None:
        self.semaphore = asyncio.Semaphore(concurrency)
        self.queue_timeout = queue_timeout
        self.pending: set[asyncio.Task[Any]] = set()
        self.accepting = True

    async def run(self, function: Callable[..., T], *args: Any) -> T:
        """Wait a bounded time for admission, then execute in a worker thread."""
        if not self.accepting:
            raise ServiceError(503, "shutting_down", "Service is shutting down.")
        try:
            await asyncio.wait_for(self.semaphore.acquire(), self.queue_timeout)
        except TimeoutError as exc:
            raise ServiceError(
                503, "capacity_busy", "Inference queue is busy; retry with backoff."
            ) from exc
        if not self.accepting:
            self.semaphore.release()
            raise ServiceError(503, "shutting_down", "Service is shutting down.")
        task = asyncio.create_task(asyncio.to_thread(function, *args))
        self.pending.add(task)

        def finished(done: asyncio.Task[Any]) -> None:
            self.pending.discard(done)
            self.semaphore.release()
            if not done.cancelled():
                done.exception()  # Retrieve abandoned failures without logging PII.

        task.add_done_callback(finished)
        return await asyncio.shield(task)

    async def drain(self) -> None:
        """Finish native work before freeing model weights during shutdown."""
        if self.pending:

            async def wait_pending() -> None:
                await asyncio.gather(*self.pending, return_exceptions=True)

            await finish_before_cancelling(asyncio.create_task(wait_pending()))

    async def aclose(self) -> None:
        """Stop accepting work, reject queued callers, and drain active work."""
        self.accepting = False
        await self.drain()
