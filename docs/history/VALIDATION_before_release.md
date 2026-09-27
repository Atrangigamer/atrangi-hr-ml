> Latest review: 69 application tests pass. Live Gemini evaluation encountered

> provider 503/429 failures; GPU deployment is still pending. Provisional ML-service

> score is 6.9/10; target 9.3-9.5 is not achieved. See docs/QUALITY_SCORECARD.md

> (QUALITY_SCORECARD.md in the docs folder). Earlier results below remain historical.



# Validation



- CPU/application regression suite: 61 passed after migration fixes.

- Repetition: consult qa_results.json for ten completed passing rounds (610 test executions).

- Real localhost Uvicorn, mixed API load, PDF fuzzing and recovery: included.

- Ruff, compileall and Docker Compose configuration validation: passed.

- Native NVIDIA driver/GPU identification: passed via nvidia-smi.

- Real model inference, CUDA image build, VRAM and extraction quality: not executed.



See ASSESSMENT.md for fixes, scope and blockers. Tests with native-model doubles are

not evidence of CUDA inference or factual resume-extraction quality.



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
