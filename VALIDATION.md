Latest Bob review: preserved the embedding API update, added unit-norm validation,
79 tests passed per run (full run plus two repeat rounds). Rebuilt container healthy;
real HTTP CUDA embedding passed. See docs/BOB_CHANGE_REVIEW.md and bob_review_live.json.

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

# Current release status — 27 September 2026

The service is running at http://127.0.0.1:8000/docs on this laptop only.
**Local GPU checks pass; cloud extraction availability remains a blocker.**
English resume extraction passed, then Gemini returned upstream HTTP 503 on the
Spanish case. The service safely returned 503. Further extraction requests stopped.
The missing-information, embedded-instruction and education cases were skipped.
Readiness means models initialized; it does not continuously probe Gemini availability.

## Verified in this run

- 69 regression tests passed in each of two rounds (138 test executions). Native
  inference is doubled in this suite; these are separate from the real tests below.
- Ruff passed. Container dependencies passed pip check. Stored OpenAPI matches the
  running service. Cloud-adapter SHA-256 matches the image.
- Real CUDA embeddings: 24 requests with concurrency four, all normalized 384-vectors.
  Sample p50 0.031s, p95 0.032s; a tiny warm sample, not a capacity guarantee.
- Real backend reference client and Analytics cosine helper passed together.
- Blank/invalid/extra/missing/overlong JSON rejected; corrupt, empty, blank and
  encrypted PDFs rejected; request-size cap returned 413.
- GPU total usage snapshot: 2720 of 8151 MiB, including other laptop workloads;
  this is not a measurement of service-only or peak VRAM.
- English PDF exact name/email/experience/absent-education checks passed in 17.875s.
  Spanish request failed after 6.688s due to provider availability, not a measured
  extraction-accuracy failure. Do not turn skipped cases into a quality percentage.

## Changes and remaining work

Added `python -m scripts.verify_live`, a repeatable synthetic real-service check
that stops extraction on upstream failure. Corrected outdated installation/offline
claims, guarded the fresh-install .env copy and changed Compose validation to quiet
mode so instructions do not print credentials. Older status notes live in docs/history.
No application defect was reproduced by this run; no inference code change or rebuild
was needed. Service restart testing is deferred because startup calls the unavailable
provider; restarting now could remove the still-working embedding endpoint.

The provisional ML delivery assessment remains 7.9/10, not the requested 9.3–9.5.
No sustained availability, representative multilingual accuracy, full HR integration
or production-security claim is established. The full HR modules remain team work.

## Next actions and ownership

1. atrangi: keep Docker Desktop running. Check status.ps1. After provider recovery,
   run the live acceptance script once; stop on provider errors. Label a separate
   representative holdout set before making accuracy claims. Coordinate a joint demo.
2. Hazma: receive handoffs/Hazma_Backend.zip. Implement authenticated durable jobs,
   tenant-scoped storage, bounded retries and reviewed result persistence.
3. Analytics Lead: receive handoffs/Analytics_Lead.zip. Use the model manifest and
   matching vector preprocessing; treat cosine as similarity, not hiring probability.
4. Ele: receive handoffs/Ele_Frontend.zip. Build upload/status/correction screens
   against Hazma's API, with clear temporary-failure states.
5. Team: verify upload -> worker -> parse -> human correction -> embedding -> storage
   -> scoring -> display. Onboarding, leave, payroll and performance need their own
   business logic and tests in the team repositories.

Do not share .env or credentials. localhost links work only on this laptop; remote
team access requires a separately configured private deployment. No public port was opened.
Evidence: docs/qa_release_results.json and docs/live_acceptance_results.json.
