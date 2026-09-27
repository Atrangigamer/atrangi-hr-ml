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
