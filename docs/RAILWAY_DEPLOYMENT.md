# Railway ONNX deployment

The free image uses raw onnxruntime, tokenizers and NumPy. It does not install
PyTorch, SentenceTransformers, Transformers or Optimum. The Docker weights stage
fetches only the published quantized ONNX artifact and tokenizer from pinned
revision e8f8c211226b894fcb81acc59f3b34ba3efd5f42; no model export is needed.

Dockerfile.free defaults to Antigravity with Gemini 3.7 Flash, ONNX CPU embeddings,
and port 8000. Set ML_GEMINI_API_KEY privately in Railway. Networking must target
port 8000. railway.toml selects the free Dockerfile for deployments from this repo.
The GitHub workflow builds the same Dockerfile and publishes GHCR images. A Railway
service using a registry image may require a manual redeploy to pull a new tag.

Local acceptance uses compose.free.yaml on localhost port 8001 with a 512 MiB limit,
leaving the existing CUDA demo on port 8000. No model bind mount is needed.
Do not assume a memory estimate means a verified fit; see deployment evidence.

Quantization changes numerical vectors. Store the shipped model_manifest.json
vector_space ID with records; re-embed candidates and jobs together for this backend.
Do not mix old PyTorch and quantized vectors without a retrieval-quality evaluation.
Antigravity calls require internet/quota and Google-stored interactions.

Railway profile limits: 2 MiB PDF, 10 pages, one PDF parser, four HTTP connections.
The CUDA profile keeps its existing defaults. Initial full ONNX container started
under 512 MiB; final smoke-test results are recorded separately.

## Verified build and current blocker

Commit dd4896bd33420f93c35993e29c3e7f5da6e3e4db passed GitHub Actions, including
real ONNX inference under a 512 MiB memory/swap limit. The corresponding GHCR image
is published. Final local full service passed readiness, real embedding, synthetic
resume fields, malformed-PDF rejection and upload-size rejection under 512 MiB.
81 regression tests and Ruff passed.

Public URL https://charming-insight-production-3c8b.up.railway.app still returns502.
User target service: 099738b6-9ed6-427a-8541-03c59a060f55.
GitHub deployment failure points instead to service 04df63ea-187a-4cf0-8d59-701dc2992610.
Inspect the target service logs/source. If registry-based, redeploy the immutable
image ghcr.io/atrangigamer/atrangi-hr-ml:dd4896bd33420f93c35993e29c3e7f5da6e3e4db.
Keep target port8000 and private ML_GEMINI_API_KEY, with Antigravity/Gemini3.7.
Do not declare production live until public readiness and both endpoints pass.

## Connection-limit fix — 28 September

Uvicorn previously limited all open connections to four, counting keep-alive
connections as well as work. The free image now allows 64 transport connections
and keeps idle connections for only one second. Before reading any POST body,
the application admits at most two active requests. Others receive JSON
capacity_busy, HTTP503 and Retry-After:5. Health GETs bypass this body-work gate.
Inference still uses one semaphore permit and its existing queue timeout.
This separates idle connection pressure from memory-consuming uploads.

83 tests pass, including admission overload, health bypass and cancellation cleanup.
The larger synthetic load tests explicitly raise admission to isolate GPU serialization;
they are not claims that Railway supports 100 simultaneous real inferences.
No Google credential change is part of this fix.
