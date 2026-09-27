> Latest review: 69 application tests pass. Live Gemini evaluation encountered

> provider 503/429 failures; GPU deployment is still pending. Provisional ML-service

> score is 6.9/10; target 9.3-9.5 is not achieved. See docs/QUALITY_SCORECARD.md

> (QUALITY_SCORECARD.md in the docs folder). Earlier results below remain historical.



# CUDA / Universal HR assessment



## Current result



61 regression tests pass, including actual localhost HTTP, PDF parsing and Instructor

validation. Native inference is doubled in this test suite. The final repeated run

is recorded in qa_results.json; it must contain ten zero-exit rounds before packaging.

Ruff, Python compilation and `docker compose config --quiet` pass.



## Test-and-fix evidence



The previous ML service's eight lifecycle, input and PDF defects remain covered.

During CUDA/universal-HR migration, a new 61-test suite initially produced 58 passes

and three failed cases. Two cases reproduced one Unicode bug: removing ZWJ/ZWNJ

changed Persian/Indic text. The normalizer now retains script-significant joiners,

while rejecting passages containing only invisible joiners. The other failure found

redirect responses incorrectly accepted by the new backend client. Non-2xx responses

now raise a safe typed error. All 61 tests passed after these fixes.



CUDA checks now reject both CPU-only and ROCm PyTorch builds. The existing model

wrapper tests still reject missing GPUs, wrong dimensions, non-finite/zero vectors

and overlong token sequences. Names and qualifications accept non-Latin scripts.



## Actual host evidence



nvidia-smi: NVIDIA GeForce RTX 5060 Laptop GPU; 8151 MiB VRAM; compute capability

12.0; driver 617.14. Build architecture: 120. Docker CLI and Compose are available,

and Compose configuration validates. Docker Desktop was started and its Linux WSL2

engine responds. The local Python environment is installed and its 61 tests pass.

IBM Bob opened this workspace, with interpreter and run tasks configured.

Both model weights downloaded and exact revisions were recorded. The CUDA image build is pending.

Inspect INSTALL_STATUS.json for current installation progress. Native Windows

nvcc/MSVC commands were not available. GPU tensor execution, model offload, actual

multilingual inference and VRAM fit have not yet been verified.



## Scope boundaries



Implemented: the ML service, backend reference client, CUDA packaging, model-preparation

script, Bob instructions and tests. The full HR scope is confirmed, but onboarding,

leave, payroll, performance, database/auth and frontend are build specifications in

FULL_HR_BLUEPRINT.md and BOB_MODULE_PROMPTS.md, not completed code in this repository.



The model choice is a starting point for an 8 GB GPU. Its 50-language embedding model

card is not evidence of equal quality for every language or industry. Evaluate labeled

resumes before enabling each language. Old English-model vectors must be regenerated.

Unknown experience stays 0.0 under the existing contract and needs source review.



Native calls cannot be forcibly terminated safely in Python threads. Public hostile

PDFs need process/container resource isolation beyond byte/page/text caps. The service

belongs behind Hazma's authenticated, tenant-authorized backend. Payroll and leave

use deterministic versioned domain rules, not LLM decisions.



One non-failing TestClient/httpx deprecation warning remains. No tested failures remain;

no claim is made that all possible bugs, hardware configurations or HR workflows are

covered. Next gate: real CUDA deployment and full-platform module acceptance tests.



## Latest hardware verification

Docker image build passed; real CUDA tensor execution and a real normalized
384-dimensional embedding passed on RTX 5060. Current cloud-adapter source hash
matches the image. Gemini returned HTTP 429 during startup twice, so the full HTTP
service is not live. See docs/deployment_verification.json. Avoid rapid API retries.


## Midnight follow-up — 27 September 2026, 00:06 IST

Existing container was paused; it was unpaused without rebuilding. Readiness returned
200. Real HTTP embedding returned200 with a normalized384-dimensional vector
(0.032 seconds for this one request, not a benchmark). Resume HTTP request returned
503 from a provider rate/quota failure. No further generation requests were made.
Service is running locally in degraded condition; full acceptance is NOT passed.
See docs/live_endpoint_verification.json. The midnight retry did not resolve quota.
