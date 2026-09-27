"""Exercise both endpoints: python test_client.py --pdf /path/to/resume.pdf."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.schemas import EmbeddingResponse, ResumeSchema
from app.utils import cosine_similarity


async def run(base_url: str, pdf: Path, text: str) -> None:
    """Upload a sample resume, validate responses and demonstrate cosine scoring."""
    async with httpx.AsyncClient(
        base_url=base_url, timeout=httpx.Timeout(300, connect=10)
    ) as client:
        health = await client.get("/health/ready")
        health.raise_for_status()
        with pdf.open("rb") as stream:
            response = await client.post(
                "/ml/parse-resume",
                files={"file": (pdf.name, stream, "application/pdf")},
            )
        response.raise_for_status()
        resume = ResumeSchema.model_validate_json(response.content)
        print(json.dumps(resume.model_dump(), indent=2, ensure_ascii=False))
        response = await client.post("/ml/generate-embedding", json={"text": text})
        response.raise_for_status()
        vector = EmbeddingResponse.model_validate_json(response.content)
        print(f"dimensions={vector.dimensions}; first_5={vector.embedding[:5]}")
        print(f"self_similarity={cosine_similarity(vector.embedding, vector.embedding):.6f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--text", default="Python engineer with FastAPI, PyTorch and CUDA experience."
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args.base_url, args.pdf, args.text))
    except httpx.HTTPStatusError as exc:
        raise SystemExit(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc
    except (httpx.RequestError, OSError) as exc:
        raise SystemExit(f"Client failed: {exc}") from exc
