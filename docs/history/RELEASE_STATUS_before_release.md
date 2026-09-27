# Handoff snapshot — 2026-09-26, 03:11 IST

## Latest update — 2026-09-26, 11:01 IST

Optional OpenAI extraction added; the application suite now has 64 passing tests.
Live OpenAI authentication/model lookup succeeded. Live synthetic extraction failed
with HTTP 429 credit_balance_exhausted. Local extraction remains selected. The prior
Docker build failed because Docker Hub was unreachable; after connectivity recovered,
the installer restarted. Real GPU deployment remains unverified.
The sections below preserve earlier test/download snapshots.

## Latest update — 2026-09-26, 03:45 IST

Both model downloads completed. The LLM file is 1117320736 bytes and its SHA-256
matches the downloaded content identifier. Exact revisions are in the model
manifest, now included in Hazma and Analytics handoff ZIPs. The installer remains
BUILDING while the CUDA image downloads; real GPU tests are still pending.
The earlier snapshot below describes the previous check.

## Checks actually completed

- New repeat run: 10 rounds, 61 passing tests each, 610 passing test executions.
- Includes real localhost Uvicorn HTTP runs with 40 mixed requests per round,
  malformed multipart input, inference-failure handling, recovery and shutdown.
- PDF parsing, strict schemas, Unicode, concurrency and lifecycle regressions pass.
- These tests replace native model inference with test doubles.
- Docker Compose configuration validates. Docker Desktop's Linux engine responds.
- Host identifies RTX 5060 Laptop GPU, 8151 MiB VRAM; approximately 2 GB was in use.
- One non-failing Starlette/httpx test-client deprecation warning remains.

## Pending deployment checks

The installer remains at BUILDING. Docker is downloading the CUDA base image;
no ML container exists yet. Embedding model weights downloaded. The LLM download
has a partial file and is not complete. Real CUDA tensor execution, model offload,
VRAM fit and both real-model endpoint smoke tests have not passed yet.

The running installer is configured to attempt those checks after download/build.
Read INSTALL_STATUS.json in atrangi's local working folder for subsequent progress;
this document is a snapshot and does not update itself.

## Safe work to start now

Use the schemas, ML OpenAPI, backend client, cosine helper and shared blueprint to
build integrations with explicit mocks. Get the verified private ML URL and model
revision metadata from atrangi before a live integration test.

The executable code delivered is the ML component. Full-suite backend/frontend,
onboarding, leave, payroll and performance are specified in the blueprint and still
need implementation in the team repositories. Passing these tests does not certify
that the full platform is complete or that the software has no possible bugs.


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
