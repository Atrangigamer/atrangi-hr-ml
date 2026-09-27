"""FastAPI lifecycle, bounded request handling and the public ML endpoints."""

import asyncio
import gc
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from .antigravity_extractor import AntigravityExtractor
from .config import Settings
from .embeddings import Embedder
from .errors import InvalidPDF, ServiceError
from .extractors import ResumeExtractor, extract_pdf_text
from .openai_extractor import OpenAIExtractor
from .runtime import BoundedRunner, finish_before_cancelling
from .schemas import EmbeddingRequest, EmbeddingResponse, ErrorResponse, ResumeSchema

logger = logging.getLogger("ml_service")


class BodyLimitMiddleware:
    """Cap actual request bytes before multipart parsing, including chunked bodies.

    Buffers at most the configured limit plus one ASGI chunk; it does not trust
    Content-Length. Uvicorn also bounds concurrent connections in deployment.
    """

    def __init__(self, app: ASGIApp, limit: int) -> None:
        self.app, self.limit = app, limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.limit:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "request_too_large",
                            "message": "Request exceeds the configured body limit.",
                        }
                    },
                )
                await response(scope, receive, send)
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        chunks.clear()
        delivered = False

        async def replay() -> dict[str, Any]:
            nonlocal delivered, body
            if not delivered:
                delivered = True
                result = {"type": "http.request", "body": body, "more_body": False}
                body = b""
                return result
            return await receive()

        await self.app(scope, replay, send)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct an app; models are allocated only when its lifespan starts."""
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Load/warm both models once, fail startup on errors, drain on shutdown."""
        gpu = BoundedRunner(config.gpu_concurrency, config.gpu_queue_timeout)
        pdf = BoundedRunner(config.pdf_concurrency, config.gpu_queue_timeout)
        embedder = None
        extractor = None
        resources: list[Any] = []
        application.state.ready = False

        def load_models() -> tuple[Embedder, ResumeExtractor]:
            # Register each successful allocation inside its thread. Cancellation
            # between constructor completion and await return cannot lose it.
            embedding_model = Embedder(config.embedding_model)
            resources.append(embedding_model)
            extraction_model = (AntigravityExtractor(config) if config.llm_provider == "antigravity"
                                else OpenAIExtractor(config) if config.llm_provider in ("openai", "gemini")
                                else ResumeExtractor(config))
            resources.append(extraction_model)
            return embedding_model, extraction_model

        loading = asyncio.create_task(asyncio.to_thread(load_models))
        try:
            embedder, extractor = await asyncio.shield(loading)
            await gpu.run(embedder.embed, "Startup health check")
            await gpu.run(
                extractor.parse,
                "Synthetic startup check: no candidate facts are available.",
            )
            application.state.embedder = embedder
            application.state.extractor = extractor
            application.state.gpu = gpu
            application.state.pdf = pdf
            application.state.ready = True
            logger.info("Models warmed; extraction_provider=%s embedding_dimensions=384", config.llm_provider)
            yield
        finally:
            application.state.ready = False

            async def cleanup() -> None:
                await asyncio.gather(loading, return_exceptions=True)
                await pdf.aclose()
                await gpu.aclose()
                for model in reversed(resources):
                    try:
                        await asyncio.to_thread(model.close)
                    except Exception as exc:  # noqa: BLE001 - always close the remaining models
                        logger.error("Model cleanup failed type=%s", type(exc).__name__)
                resources.clear()
                application.state.embedder = None
                application.state.extractor = None
                gc.collect()

            await finish_before_cancelling(asyncio.create_task(cleanup()))

    application = FastAPI(title="atrangi HR ML Service", version="1.0.0", lifespan=lifespan)
    application.add_middleware(BodyLimitMiddleware, limit=config.max_pdf_bytes + 65536)

    @application.exception_handler(ServiceError)
    async def service_error(_: Request, exc: ServiceError) -> JSONResponse:
        headers = {"Retry-After": "5"} if exc.status == 503 else None
        return JSONResponse(
            status_code=exc.status,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers=headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError) -> JSONResponse:
        # Pydantic's default errors can include submitted input and resume PII.
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "invalid_request",
                    "message": "Request does not match the API schema; check /docs.",
                }
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
        # Multipart parser failures originate in Starlette, before route execution.
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": "http_request_rejected",
                    "message": "HTTP request rejected; check the URL, method and request encoding.",
                }
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled request failure type=%s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Unexpected service failure; check service health.",
                }
            },
        )

    @application.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    async def ready() -> dict[str, str]:
        if not getattr(application.state, "ready", False):
            raise ServiceError(503, "not_ready", "Models are not ready.")
        return {"status": "ready"}

    responses = {code: {"model": ErrorResponse} for code in (400, 413, 422, 500, 503)}

    async def inference(function: Any, argument: str, kind: str) -> Any:
        await ready()
        try:
            return await application.state.gpu.run(function, argument)
        except ServiceError:
            raise
        except Exception as exc:
            # Instructor exception strings can contain the full resume/model output.
            logger.error("%s inference failed type=%s", kind, type(exc).__name__)
            message = f"{kind} inference failed; verify model configuration, context budget and available memory."
            if "OutOfMemory" in type(exc).__name__:
                message = (
                    "Out of memory; reduce model/context size or free memory on the inference device."
                )
            raise ServiceError(500, "inference_failed", message) from exc

    @application.post("/ml/parse-resume", response_model=ResumeSchema, responses=responses)
    async def parse_resume(
        file: Annotated[UploadFile, File(description="Unencrypted text-bearing PDF")],
    ) -> ResumeSchema:
        """Accept multipart field `file` and return a validated ResumeSchema."""
        await ready()
        try:
            data = await file.read(config.max_pdf_bytes + 1)
        finally:
            await file.close()
        if len(data) > config.max_pdf_bytes:
            raise InvalidPDF("PDF exceeds the configured upload limit.")
        text = await application.state.pdf.run(extract_pdf_text, data, config)
        return await inference(application.state.extractor.parse, text, "Resume extraction")

    @application.post(
        "/ml/generate-embedding", response_model=EmbeddingResponse, responses=responses
    )
    async def generate_embedding(payload: EmbeddingRequest) -> EmbeddingResponse:
        """Return a normalized 384-dimensional vector for a short passage."""
        await ready()
        vector = await inference(application.state.embedder.embed, payload.text, "Embedding")
        return EmbeddingResponse(embedding=vector)

    return application


app = create_app()
