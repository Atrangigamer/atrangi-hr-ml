"""Bounded acceptance checks against real HTTP/model inference on synthetic data.

Run ``python -m scripts.verify_live`` with the service already running. Makes at
most five resume requests, stopping extraction checks on provider unavailability.
Never reads credentials. This is a smoke/load sample, not a quality benchmark.
"""

import asyncio
import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from textwrap import wrap

import httpx
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from app.schemas import EmbeddingResponse, ResumeSchema
from app.utils import cosine_similarity
from integrations.backend_client import MLClient
from scripts.evaluate_extraction import CASES


def synthetic_pdf(text: str) -> bytes:
    """Create a small text PDF, including Latin accents, entirely in memory."""
    buffer = io.BytesIO()
    canvas = Canvas(buffer)
    y = 790
    for line in wrap(text, 85):
        canvas.drawString(40, y, line)
        y -= 18
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


async def main() -> int:
    """Record assertions and timings without storing extracted candidate text."""
    rows = []
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Real localhost HTTP, Gemini PDFs, CUDA embeddings and reference client. "
                 "Synthetic diagnostic cases only; not a held-out accuracy benchmark.",
        "checks": rows,
    }
    target = Path("docs/live_acceptance_results.json")

    def record(name: str, passed: bool, **details: object) -> None:
        rows.append({"name": name, "passed": passed, **details})
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(name, "PASS" if passed else "FAIL", flush=True)

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=300,
                                 trust_env=False) as client:
        r = await client.get("/health/ready")
        record("readiness", r.status_code == 200)
        for name, payload in [("blank", {"text": "  "}), ("extra_field", {"text": "x", "x": 1}),
                              ("wrong_type", {"text": 42}), ("missing", {}),
                              ("token_limit", {"text": "word " * 500})]:
            r = await client.post("/ml/generate-embedding", json=payload)
            record(name, r.status_code == 422 and "error" in r.json(), status=r.status_code)
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        blank = io.BytesIO()
        writer.write(blank)
        writer.encrypt("synthetic-password")
        encrypted = io.BytesIO()
        writer.write(encrypted)
        for name, data in [("invalid_pdf", b"not a pdf"), ("empty_pdf", b""),
                           ("blank_pdf", blank.getvalue()), ("encrypted_pdf", encrypted.getvalue())]:
            r = await client.post("/ml/parse-resume", files={"file": ("test.pdf", data)})
            record(name, r.status_code == 400 and "error" in r.json(), status=r.status_code)
        r = await client.post("/ml/parse-resume", content=b"x" * (11 * 1024 * 1024))
        record("body_limit", r.status_code == 413, status=r.status_code)

        # Four concurrent requests, six waves: below the server connection limit.
        times = []
        async def embedding(index: int) -> bool:
            text = ["Customer service and Excel", "Contabilidad y servicio al cliente",
                    "Python engineering with FastAPI", "Inventory and logistics"][index % 4]
            started = time.monotonic()
            r = await client.post("/ml/generate-embedding", json={"text": text})
            times.append(time.monotonic() - started)
            r.raise_for_status()
            e = EmbeddingResponse.model_validate_json(r.content)
            return abs(math.hypot(*e.embedding) - 1) < 1e-5

        outcomes = []
        for wave in range(6):
            outcomes.extend(await asyncio.gather(*(embedding(wave * 4 + i) for i in range(4))))
        ordered = sorted(times)
        record("concurrent_real_embeddings", all(outcomes), requests=len(outcomes), concurrency=4,
               p50_seconds=round(ordered[len(ordered)//2], 4),
               p95_seconds=round(ordered[math.ceil(len(ordered)*.95)-1], 4))

        cases = [*CASES, {
            "id": "healthcare_education",
            "text": "Name: Robin Patel. Email: robin@example.com. Total professional experience: "
                    "4 years. Skills: patient care, documentation. Education: Bachelor of Nursing, "
                    "Example University, graduated 2020.",
            "expected": {"candidate_name": "Robin Patel", "email": "robin@example.com",
                         "experience_years": 4.0, "education": [{"degree": "Bachelor of Nursing",
                         "institution": "Example University", "graduation_year": 2020}]},
        }]
        for case in cases:
            started = time.monotonic()
            r = await client.post("/ml/parse-resume",
                                  files={"file": ("synthetic.pdf", synthetic_pdf(case["text"]),
                                                   "application/pdf")})
            checks = {}
            if r.status_code == 200:
                result = ResumeSchema.model_validate_json(r.content).model_dump()
                checks = {k: result[k] == v for k, v in case["expected"].items()}
            record(case["id"], r.status_code == 200 and all(checks.values()),
                   status=r.status_code, fields=checks, seconds=round(time.monotonic()-started, 3))
            if r.status_code in (429, 500, 502, 503, 504):
                report["extraction_stopped_early"] = True
                break

    async with MLClient("http://127.0.0.1:8000") as backend:
        a = EmbeddingResponse.model_validate(await backend.embed("Python FastAPI engineer"))
        b = EmbeddingResponse.model_validate(await backend.embed("Python FastAPI engineer"))
        record("backend_client_and_analytics", cosine_similarity(a.embedding, b.embedding) > .99999)
    report["all_passed"] = all(row["passed"] for row in rows) and not report.get("extraction_stopped_early")
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
