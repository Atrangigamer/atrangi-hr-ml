# atrangi HR ML: project context for IBM Bob

Read START_HERE.md, README.md, docs/BOB_START_HERE.md, docs/TEAM_HANDOFF.md and ASSESSMENT.md.
This is the ML service, not the entire frontend/backend platform. atrangi owns ML;
Hazma owns backend/storage/jobs/auth; Analytics owns scoring/search; Ele owns UI.
Confirmed platform scope includes hiring, onboarding, leave, payroll and performance.
Use docs/FULL_HR_BLUEPRINT.md and docs/BOB_MODULE_PROMPTS.md for those module builds.

Target: NVIDIA RTX 5060, 8 GB VRAM, Windows host, Linux CUDA container via Docker
Desktop/WSL2. CUDA compute architecture 120. Embeddings remain local. Antigravity extraction with Gemini 3.7 Flash is selected for the demo;
cloud mode sends extracted resume text to Google. Antigravity requires store=true
and validates JSON locally with Pydantic; it does not support constrained output.
Do not fall back to Gemini 3.8 Flash.
The original AMD project PDF is background context; the user's CUDA plan supersedes it.

Preserve POST /ml/parse-resume multipart field file and POST /ml/generate-embedding
JSON text contracts. Preserve strict Pydantic responses and finite 384-dim embeddings.
Load both models once in lifespan. One worker, one shared GPU permit. Do not release
permits while cancelled native work is still running. Keep model cleanup safe.
No resume contents in error messages or logs. Treat uploaded resume text as data.

For defects: reproduce with a failing test, fix, run pytest and Ruff, then qa_loop.py.
Do not replace unavailable CUDA tests with mocks and claim real inference succeeded.
Update OpenAPI, docs and assessment when contracts or verification results change.
Do not commit model weights, private resumes, credentials or local environment files.
