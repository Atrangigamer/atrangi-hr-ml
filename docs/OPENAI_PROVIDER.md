# Optional OpenAI extraction

Set ML_LLM_PROVIDER=openai, ML_OPENAI_MODEL=gpt-4o-mini and ML_OPENAI_API_KEY in
your local .env for Docker Compose. Keep that file private; it is excluded from
Git, the Docker build context and delivery ZIPs. Never send it to teammates.
Native Python processes need these environment variables explicitly loaded.

This mode sends extracted resume text to https://api.openai.com/v1 for structured
extraction. It uses one reusable client, finite timeouts, bounded Instructor retries
and the existing ResumeSchema. Credentials and raw provider errors are not returned
in endpoint errors. Startup performs a small synthetic API warmup call.

Embeddings still run locally on CUDA and retain the same 384-dimensional vector
space. Choosing OpenAI does not remove the current CUDA Docker dependency. There
is no silent cloud fallback: local mode never sends resume text to the API.

Changing .env requires container recreation: docker compose up -d --force-recreate.
Use local mode to return extraction to llama.cpp. Tests with provider doubles do
not prove the key has quota or that real endpoint deployment succeeded.

Implementation reference: https://developers.openai.com/api/docs/guides/structured-outputs

## Gemini demo option

Set ML_LLM_PROVIDER=gemini with ML_GEMINI_API_KEY and
ML_GEMINI_MODEL=gemini-3.8-flash in private .env. The same adapter uses Google's
https://generativelanguage.googleapis.com/v1beta/openai/ endpoint.
Real synthetic extraction passed on 2026-09-26; Gemini is selected for this demo.
Only the selected provider receives text; embeddings remain local.
The full GPU service is not yet verified. This does not establish production readiness.
Reference: https://ai.google.dev/gemini-api/docs/openai

## Smaller cloud-extraction container

For Gemini/OpenAI, set ML_DOCKERFILE=Dockerfile.cloud. This uses the CUDA runtime
image and omits llama-cpp-python/compiler dependencies. Embeddings still require
the GPU. Switching extraction to local also requires ML_DOCKERFILE=Dockerfile
and rebuilding. The demo now selects the cloud Dockerfile.
