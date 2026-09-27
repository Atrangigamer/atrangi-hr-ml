## Current provider update — 27 September 2026

Switched to Antigravity agent antigravity-preview-09-2026 using explicit
Gemini 3.7 Flash. No fallback to Gemini 3.8 Flash. New container is healthy.
Real synthetic resume endpoint passed HTTP 200 with expected fields (10.391s);
real normalized CUDA embedding and CUDA tensor checks passed. 77 regression tests
passed per round, two rounds (154 executions); Ruff passed; source matches image.
Evidence: docs/antigravity_verification.json and docs/qa_antigravity_results.json.

Antigravity requires stored interactions at Google. It does not support constrained
JSON output; the adapter validates responses strictly with Pydantic. See
ANTIGRAVITY_PROVIDER.md for differences. Synthetic smoke success does not establish
broad extraction accuracy or sustained provider availability. Assessment stays 7.9/10.
Earlier Gemini 3.8 outage records below are historical, not the active configuration.

# Universal HR — atrangi's project hub

Open this active folder in IBM Bob. The ML service runs at http://127.0.0.1:8000/docs.
CUDA embeddings pass; Gemini intermittently returns 503. See docs/RELEASE_STATUS.md
for the latest results and limitations. No installer or rebuild is currently needed.

- README.md: architecture, fresh setup and runtime commands.
- docs/RELEASE_STATUS.md: current acceptance evidence and team next steps.
- docs/ATRANGI_NEXT_STEPS.md: your ML lead responsibilities and quality workflow.
- docs/TEAM_HANDOFF.md and handoffs/: recipient instructions and ZIPs.
- docs/presentation/: presentation review and speaking script.
- docs/FULL_HR_BLUEPRINT.md: remaining full-suite implementation plan.
- docs/QUALITY_SCORECARD.md: provisional 7.9/10 assessment and remaining gates.
- scripts/verify_live.py: bounded real-service test using synthetic PDFs.

Keep Docker Desktop running. Preserve private .env; do not send it to teammates.
