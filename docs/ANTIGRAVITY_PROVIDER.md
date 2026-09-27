# Antigravity extraction adapter

Requested by atrangi on 27 September 2026. Uses the existing private Google API key.

- Provider: antigravity
- Agent: antigravity-preview-09-2026
- Explicit underlying model: gemini-3.7-flash (no fallback to 3.8 Flash)
- Endpoint: https://generativelanguage.googleapis.com/v1beta/interactions
- Agent token budget: 8192, bounded HTTP timeout, no automatic request retries.
- Local CUDA embeddings remain unchanged.

Antigravity is a managed agent, not a Chat Completions model. Its API does not
support schema-constrained JSON. We request plain JSON and strictly validate it
with ResumeSchema; incomplete or invalid responses are rejected with safe errors.
This adapter does not use Instructor's Chat Completions schema mode. Optional
OpenAI/Gemini adapters retain Instructor. Public endpoint schemas are unchanged.

The live API rejected store=false: this agent requires stored interactions on
Google's infrastructure. Each request uses a fresh remote environment; no prior
interaction or environment is reused by our service. Tools=[] and the extraction
prompt request no tool use, but the remote environment is Google-managed.
Do not describe this path as offline or as having no provider-side retention.
Only synthetic inputs were used for verification.

Settings: ML_LLM_PROVIDER=antigravity, ML_ANTIGRAVITY_MODEL=gemini-3.7-flash,
ML_ANTIGRAVITY_TOKEN_BUDGET=8192. Key remains in private .env and is excluded from ZIPs.

Official docs: https://ai.google.dev/gemini-api/docs/antigravity-agent
