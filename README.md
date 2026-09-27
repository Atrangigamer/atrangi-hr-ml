Current extraction selection: Antigravity agent with explicit Gemini 3.7 Flash.
See docs/ANTIGRAVITY_PROVIDER.md for validation and provider-retention differences.

# Universal HR: atrangi ML service and IBM Bob implementation pack

Confirmed platform scope: hiring, onboarding, leave, payroll and performance.
**Implemented here:** stateless ML service, async backend integration example,
CUDA deployment configuration and regression tests. **Specified for Bob/team build:**
the wider HR modules, frontend, persistent backend and domain workflows. Those are
not represented as completed applications.

## Start here

1. Open this folder in IBM Bob. Read docs/BOB_START_HERE.md and paste its first prompt.
2. Read docs/FULL_HR_BLUEPRINT.md for the complete platform and docs/TEAM_HANDOFF.md
   for who receives which files. Use docs/BOB_MODULE_PROMPTS.md per team/module.
3. Run CPU verification, then the Windows CUDA setup below.

## Verified host and CUDA target

The authoring host reports NVIDIA GeForce RTX 5060 Laptop GPU, 8151 MiB VRAM,
compute capability 12.0, driver 617.14. CUDA architecture is **120**. The supplied
Dockerfile uses pytorch/pytorch:2.10.0-cuda12.8-cudnn9-devel and compiles llama.cpp
with GGML_CUDA=ON. It preserves the image's Torch wheel with a pip constraint.
The host has an NVIDIA driver; that alone does not prove the application works.
The current demo uses Dockerfile.cloud with the CUDA runtime base and Gemini
extraction. Real CUDA embeddings, tensor execution and both HTTP endpoints passed
on 27 September 2026. The optional local GGUF extraction route is not verified by
those cloud-mode tests. See docs/live_acceptance_results.json for the latest checks.

## Windows setup (PowerShell in this folder)

Use Docker Desktop with WSL2 and Linux containers. Start Docker Desktop first.
Check `docker info` and `nvidia-smi`. Then verify GPU container access:

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi
```

Prepare an isolated CPU/test environment. Use a standard Python 3.12 installation:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe qa_loop.py --rounds 10 --report qa_results.json
.\.venv\Scripts\ruff.exe check app tests integrations scripts test_client.py qa_loop.py
```

For a fresh installation only, download model weights once. Local embeddings do
not need network access at inference time; Gemini extraction requires internet and
provider quota. On this configured laptop, preserve the existing private .env and
use `docker compose up -d --no-build --wait --wait-timeout 180`.

Fresh installation commands (do not overwrite an existing .env):

```powershell
.\.venv\Scripts\python.exe -m pip install "huggingface-hub>=0.34,<2"
.\.venv\Scripts\python.exe scripts/download_models.py
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose config --quiet
docker compose build
docker compose up -d
docker compose logs -f ml
```

The download script records exact resolved commits in models/model_manifest.json.
For reproducible later downloads pass --embedding-revision and --llm-revision with
those commit SHAs. Model choices: Qwen2.5-1.5B-Instruct Q4_K_M and multilingual
MiniLM-L12-v2. This is a small starting configuration for 8 GB, not a quality or
VRAM guarantee. Measure first; replace with a larger model only if it fits and
improves labeled extraction results. Weights are not included in the archive.
Allow several GB of disk/network use for weights and substantially more for the
CUDA development image/build cache. Do not install the production requirements
straight into the CPU test venv: llama.cpp needs the CUDA toolchain.

Test the live GPU-backed application using a synthetic text-bearing resume:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ready
.\.venv\Scripts\python.exe test_client.py --pdf C:\path\synthetic-resume.pdf --text "Customer service and inventory management"
docker compose exec ml nvidia-smi
```

The Compose configuration exposes port 8000 only on host loopback and uses one GPU.
If Hazma's backend is also containerized, join the same private network and call
http://ml:8000. Configure network access deliberately for a backend on another host.

## Runtime behavior

- FastAPI async lifespan loads and warms both models once. No downloads per request.
- One shared asyncio semaphore, one worker, cancellation-safe inference and cleanup.
- In-memory PDF parsing with page-by-page fallback, strict Pydantic/Instructor JSON,
  bounded sizes and safe error messages. No OCR, DOCX/image intake or persistent DB.
- POST /ml/parse-resume accepts multipart field file; POST /ml/generate-embedding
  accepts JSON text and returns a normalized finite vector with 384 dimensions.
- The multilingual model's 128-wordpiece limit is checked before inference. Split
  long professional content upstream; no silent truncation. Language quality varies.
- Original-script names and credentials are preserved, with no US degree assumption.
  Unknown numeric experience remains 0.0 under the original schema and needs review.
- Cosine helper is app/utils.py. Old English-model vectors must be re-embedded;
  same dimensions do not imply the same vector space.

See docs/API_CONTRACT.md and docs/openapi.json for exact types/statuses. Health routes
are /health/live and /health/ready; docs UI is /docs. Resume data is not retained by
the service, though FastAPI may temporarily spool multipart uploads to disk.

## Main settings

ML_LLM_MODEL_PATH=/models/resume.gguf; ML_EMBEDDING_MODEL=/models/embedding;
ML_LLM_CONTEXT=4096; ML_LLM_MAX_TOKENS=1024; ML_GPU_CONCURRENCY=1;
ML_GPU_QUEUE_TIMEOUT=30; ML_LLM_ATTEMPTS=2; ML_PDF_CONCURRENCY=2;
ML_MAX_PDF_BYTES=10485760; ML_MAX_PDF_PAGES=20; ML_MAX_RESUME_CHARS=24000.
ML_LLM_CHAT_FORMAT is optional: normally use the GGUF template. Never use multiple
workers on one GPU without an explicit memory/allocation design. The LLM context
budget may reject PDFs below the character cap. Native work cannot be hard-killed
by cancelling its Python thread. Public hostile PDFs need isolated resource-limited
parsing. Backend auth, tenant checks, retries and human review are separate layers.

## Validation and boundaries

ASSESSMENT.md and VALIDATION.md describe actual test evidence. qa_results.json stores
repeated test output. Tests include real PDF parsing, Instructor validation and a
real localhost Uvicorn server, but native models are doubles. Separate real-model results are in docs/live_acceptance_results.json. Broad
multilingual factual quality and the full HR modules still require acceptance testing. Passing this suite does not prove a universally bug-free system.

## Official references

- IBM Bob workspace rules: https://bob.ibm.com/docs/ide/configuration/rules
- NVIDIA containers: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html
- CUDA llama.cpp build: https://github.com/abetlen/llama-cpp-python#installation
- Embedding model: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Local LLM: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
