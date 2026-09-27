"""Build recipient-specific ZIPs and the complete source archive, without weights."""

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
COMMON = [
    "docs/ANTIGRAVITY_PROVIDER.md",
    "docs/TEAM_HANDOFF.md",
    "docs/INTEGRATION_CHECKLIST.md",
    "docs/FULL_HR_BLUEPRINT.md",
    "docs/BOB_MODULE_PROMPTS.md",
    "docs/UNIVERSAL_HR_SCOPE.md",
    "docs/API_CONTRACT.md",
    "docs/RELEASE_STATUS.md",
]
PACKS = {
    "Hazma_Backend": {
        "files": [
            "docs/openapi.json",
            "integrations/__init__.py",
            "integrations/backend_client.py",
            "app/__init__.py",
            "app/schemas.py",
            "app/utils.py",
        ],
        "start": """# Hazma — backend integration

Read docs/INTEGRATION_CHECKLIST.md, then docs/API_CONTRACT.md.
This is an integration subset, not a runnable ML server or completed HR backend.

1. Merge integrations/backend_client.py and shared app schemas/utils into your
   backend's package layout; preserve relative imports when relocating them.
2. Add dependencies from requirements-integration.txt to your existing dependency
   manager. Resolve them with your backend's versions before installing.
3. Create authenticated upload + durable job/status APIs. Workers call MLClient,
   validate returned objects with ResumeSchema/EmbeddingResponse and persist them.
4. Own tenant authorization, DB/pgvector, idempotency, retry limits and audit events.
5. Publish your backend OpenAPI to Ele; agree vector metadata/passage rules with
   Analytics. Request private service URL + model manifest from atrangi when ready.

Use Bob's Hazma prompts in docs/BOB_MODULE_PROMPTS.md. Then build employee records,
onboarding, leave, payroll and performance per the shared blueprint.
""",
        "requirements": "httpx==0.28.1\npydantic==2.13.5\n",
    },
    "Analytics_Lead": {
        "files": ["docs/ANALYTICS_HANDOFF.md", "app/__init__.py", "app/utils.py"],
        "start": """# Analytics Lead — scoring and reporting

Read docs/ANALYTICS_HANDOFF.md and docs/INTEGRATION_CHECKLIST.md.
app/utils.py contains the standalone cosine_similarity helper (standard library
only). This package does not include a GPU model, database or analytics API.

1. Use cosine_similarity on finite, nonzero vectors from the SAME model revision.
2. Agree short-passage splitting/aggregation and vector metadata with Hazma/atrangi.
3. Implement reviewable, job-related matching and explicit qualification filters;
   evaluate labeled multilingual pairs before claiming retrieval quality.
4. Provide score explanations and dashboard contracts to Hazma and Ele.
5. Request the completed model_manifest.json before indexing live vectors.

For full HR, define authorized onboarding/leave/payroll/performance metrics with
the module owners. These dashboards are planned, not implemented in this subset.
Use the Analytics prompts in docs/BOB_MODULE_PROMPTS.md.
""",
    },
    "Ele_Frontend": {
        "files": ["docs/FRONTEND_HANDOFF.md", "docs/openapi.json"],
        "start": """# Ele — frontend integration

Read docs/FRONTEND_HANDOFF.md and docs/INTEGRATION_CHECKLIST.md.
This is a contracts/design handoff, not a completed frontend application.

1. Get Hazma's authenticated backend OpenAPI and durable job-status contract.
   Included openapi.json describes ML only; never call its routes from the browser.
2. Build upload -> job status -> review/correction -> result screens and ATS views.
3. Map agreed backend states to clear UI labels. Handle scanned/corrupt PDFs,
   temporary failures and unknown facts without presenting them as verified values.
4. Build onboarding, leave, payroll and performance UI against Hazma's APIs using
   the shared blueprint. Mock pending APIs explicitly during development.
5. Run the joint synthetic case after atrangi verifies the real GPU deployment.

Use the Ele/shared prompts in docs/BOB_MODULE_PROMPTS.md in your frontend repo.
""",
    },
}


def main() -> None:
    """Package only explicit handoff files; check archive integrity and record hashes."""
    handoffs = ROOT / "handoffs"
    handoffs.mkdir(exist_ok=True)
    inventory = {}
    for name, spec in PACKS.items():
        path = handoffs / f"{name}.zip"
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            for relative in COMMON + spec["files"]:
                archive.write(ROOT / relative, relative)
            archive.writestr("START_HERE.md", spec["start"])
            if "requirements" in spec:
                archive.writestr("requirements-integration.txt", spec["requirements"])
            manifest = ROOT / "models/model_manifest.json"
            if name != "Ele_Frontend" and manifest.is_file():
                archive.write(manifest, "models/model_manifest.json")
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            inventory[path.name] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "files": archive.namelist(),
            }
    (handoffs / "MANIFEST.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    excluded = {
        "models",
        ".venv",
        ".model-download-cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".git",
    }
    target = ROOT.parent / "universal_hr_cuda_bob.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            if not path.is_file() or any(part in excluded for part in rel.parts):
                continue
            if path.suffix in {".log", ".pyc"} or path.name in {
                ".env",
                "INSTALL_STATUS.json",
                "synthetic-install-test.pdf",
            }:
                continue
            archive.write(path, Path(ROOT.name) / rel)
    with ZipFile(target) as archive:
        assert archive.testzip() is None
    print("Verified 3 recipient ZIPs, SHA-256 inventory and complete source ZIP.")


if __name__ == "__main__":
    main()
