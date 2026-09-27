# Team integration: start here

This delivery contains the ML service implementation and a blueprint for the full
HR suite. Onboarding, leave, payroll and performance are not implemented services
in this package. Use FULL_HR_BLUEPRINT.md and BOB_MODULE_PROMPTS.md in your own repo.

## Current deployment gate

At the latest check on 2026-09-26, Docker Desktop responds and the embedding weights
are downloaded. Both model weights are now downloaded; the CUDA base image is still pending. There is no
running ML container yet. CPU/application tests use model doubles; they do not prove
real GPU inference. See RELEASE_STATUS.md for the packaged test snapshot.

atrangi must supply a reachable private ML URL and successful real-model test results
before anyone marks the live integration complete. 127.0.0.1 on another teammate's
laptop does not reach atrangi's laptop. The default Compose port is loopback-only;
agree a private deployment/network arrangement with Hazma before integration.

## Shared contract decisions

- The two ML calls return results synchronously. Hazma provides durable background
  jobs and a separate job-status API for Ele. The ML OpenAPI is not the frontend API.
- Agree backend states: queued, running, succeeded, failed, review_required.
  UI labels can map running to Processing and succeeded to Complete. Define review
  transitions explicitly in Hazma's API; do not infer them from HTTP 200 alone.
- Validate results with the shared schemas. Unknown experience is 0.0 under this
  contract and is not verified absence of experience. Preserve source and corrections.
- Use 384-dimensional vectors from the same model revision and preprocessing policy
  for candidates and jobs. Model metadata is available in the recipient ZIPs after completed downloads.
  Do not use guessed revision IDs or mix vectors from older English-only models.
- Agree a short-passage splitting and aggregation policy before indexing records.
  The service rejects overlong embedding input; it does not silently truncate.

## First joint acceptance run

1. atrangi: pass CUDA tensor execution, readiness, PDF extraction and embedding on
   the actual GPU. Supply model_manifest.json and measured latency/VRAM use.
2. Hazma: upload a synthetic PDF through the authenticated backend; poll its job;
   validate and persist extraction and versioned vectors exactly once.
3. Analytics: score an approved candidate/job pair; verify cosine self-similarity
   near 1, equal dimensions and matching vector-space metadata. Show job-related
   explanations, not a probability of hiring success.
4. Ele: show upload, Processing, review and Complete states through Hazma's API;
   allow fact correction and actionable failure messages.
5. Together: try corrupt PDF, overlong embedding text, unavailable ML, duplicate
   job execution and cross-tenant access. Record expected versus observed results.

Then implement full HR modules in order: identity/employee records, hiring,
onboarding, leave, payroll, performance. Use the module acceptance cases in the
blueprint. Domain policy calculations and approvals belong to the backend.
