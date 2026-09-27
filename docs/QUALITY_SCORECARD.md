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

## Latest acceptance: provider availability remains unresolved

See live_acceptance_results.json: real English PDF passed; Spanish received
upstream503 and three remaining cases were skipped. 24 concurrent GPU embeddings
and 138 regression executions passed. Rating remains 7.9/10; no new accuracy
claim is justified. Sustained availability and joint platform integration remain open.

## Current verified status — 27 September 2026, 14:02 IST

The ML demo is live at http://127.0.0.1:8000/docs, bound only to this laptop.
The existing Docker image started successfully and the container is healthy.
Real resume extraction with Gemini returned HTTP 200 and passed the strict schema
and synthetic name, email and three-year experience checks (4.039 seconds).
Local CUDA embedding returned HTTP 200: 384 dimensions and unit norm (0.016 seconds).
These are individual smoke-test timings, not throughput or accuracy benchmarks.
Earlier real CUDA tensor and image/source checks passed on the RTX 5060 Laptop GPU.
Evidence: docs/live_endpoint_verification.json and docs/deployment_verification.json.

No rebuild or installer is needed. Keep Docker Desktop running for the demo.
Gemini still depends on external quota and availability. Do not promise bug-free
operation or representative model accuracy from a single successful synthetic case.
The implemented deliverable is the ML service; other HR modules remain team work.

Next: Hazma integrates the worker/client; Analytics integrates versioned embeddings
and cosine scoring; Ele builds the backend-connected upload/review/status screens.
Atrangi coordinates one joint synthetic workflow, checks extraction quality on a
labeled holdout set, and records errors/latency before the presentation.
Do not share .env, model caches, logs or credentials. Handoff ZIPs exclude them.

# Evidence-based project evaluation — 26 September 2026

## Scope and score

**Provisional ML-service delivery score: 7.9/10. Target: 9.3–9.5/10, not yet achieved.**
This is an engineering judgment using the rubric below, not an external certification
or a measured accuracy score. Categories are weighted before rounding. The full HR
suite cannot be described as 9/10 complete: most business modules are still blueprints.
There is no defensible pre-review numeric baseline, so no numerical improvement claim
is made. Improvements below have direct test/failure evidence instead.

| Category | Weight | Score /10 | Evidence and limitation |
| --- | --- | --- | --- |
| API and architecture | 20% | 9.0 | Typed stateless contracts, lifespan loading, bounded work, clear ownership |
| Application reliability | 20% | 8.5 | 69 regressions pass; real provider outages now surfaced safely as retryable |
| Model quality evidence | 20% | 5.5 | Synthetic cloud successes; evaluation repeatedly affected by provider failures; no representative accuracy study |
| Deployment and operations | 20% | 8.0 | Healthy current-code container; real CUDA tensor, normalized embedding and Gemini resume endpoint passed; sustained-load/recovery evidence remains limited |
| Security and data handling | 10% | 7.5 | Private packaging, local permissions, input limits; full backend authorization/isolation not implemented here |
| Documentation and handoffs | 10% | 9.0 | Role ZIPs, source hub, API contracts, blueprint and presentation review |

Weighted total: 7.85, rounded to 7.9. Do not present this number as a benchmark.

## Improvements implemented during this review

1. Reproduced acceptance of whitespace-only OpenAI/Gemini keys with two failing tests.
   Configuration now rejects blank credentials before starting the service.
2. Reproduced cloud settings incorrectly failing a local-LLM context constraint.
   That check now applies only to local extraction.
3. Configuration validation strings hide submitted input to reduce accidental
   credential exposure when a configuration error is printed.
4. Added a provider-isolation test proving Gemini uses its own key, endpoint, model
   and output-token allowance rather than OpenAI's settings.
5. Added a repeatable four-case live evaluation harness: English, Spanish, missing
   information and an embedded instruction. Reports contain selected field checks,
   safe failure metadata and timing, not credentials or private document output.
6. Diagnosed Gemini HTTP 503 high demand. Added one SDK retry and mapped continuing
   429/502/503/504 errors to HTTP 503, which the backend can retry with backoff.
   Instructor-wrapped causes are inspected by type/status, never by raw error text.
7. Added a regression for wrapped transient errors and safe error redaction.

## Live evaluation results and limits

All cases are synthetic text; this harness does not test PDF parsing or GPU embeddings.
Only four selected fields per case are checked. It does not measure skill recall,
education extraction quality, summary factuality or representative multilingual accuracy.

- Attempt 1: 0/4 requests completed successfully in the harness.
- Attempt 2: 1/4 cases passed; the embedded-instruction case passed its field checks.
- Attempt 3: 1/4 cases passed; failures preserved for investigation.
- After transient-error handling: English passed; Spanish hit 503; the remaining
  two cases hit 429. This is 1/4 completed passing cases, not 25% extraction accuracy.
- Isolated diagnostic structured requests also succeeded. They do not erase the
  failed evaluation attempts or establish reliable service availability.

Evidence: evaluation_attempt_1.json, evaluation_attempt_2.json,
evaluation_attempt_3.json and evaluation_results.json. Stop repeated paid/network
tests while the provider is returning demand/rate errors; resume after recovery.

## What must change before a 9.3–9.5 rating is credible

These are proposed acceptance gates, not already measured achievements:

1. **Deployment:** successful clean startup of the final current-code container;
   real CUDA tensor and 384-dimensional embedding checks; both endpoints passing.
2. **Availability:** repeatable cloud requests without unresolved rate/capacity
   failures; verified queueing, bounded retries and recovery under expected demo load.
3. **Quality:** an annotated, separately held-out set covering the enabled languages,
   industries and layouts. Agree field-specific accuracy/recall and no-invention
   criteria before measuring; report uncertainty and sample sizes.
4. **Operations:** record startup time, latency distribution and VRAM use; demonstrate
   restart/recovery and capture a reproducible dependency/model version record.
5. **Integration:** one real UI/backend/worker/ML/scoring flow with tenant isolation,
   duplicate-job handling, human correction and actionable failures.
6. **Security:** verify the deployed access boundaries and secret handling, rather
   than treating a hidden local file as sufficient production security.

Deployment acceptance passed on 27 September. This does not guarantee provider capacity or extraction quality across unseen resumes.

## Next action

Deployment is verified. Plan quota-aware live evaluation after provider recovery, then evaluate
a broader labeled set. Re-score against the same weights and evidence. Do not change
weights or drop failed cases solely to reach the requested number.
