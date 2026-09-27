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

## Latest acceptance update — use this in the presentation

English real PDF extraction and CUDA embeddings passed. A later Spanish request
received upstream Gemini 503, so broader extraction evaluation is incomplete.
Report 69 regression tests per round, 24 successful real concurrent embeddings,
and a provisional 7.9/10 assessment. Do not claim universal accuracy or bug-free
operation. See docs/RELEASE_STATUS.md for full current evidence.

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

---

## Earlier record (historical; current status above supersedes deployment claims)

# Presentation script and questions

Suggested duration: 8–10 minutes plus questions. This is a speaking outline,
not a generated slide deck. Use PROJECT_REVIEW.md for the supporting detail.

## Slide 1 — Universal HR and my role (30 seconds)

On screen: Universal HR · atrangi · AI/ML Lead.

Say: “Our vision is an HR platform covering hiring, onboarding, leave, payroll and
performance. My contribution is the intelligence service that turns resume documents
into structured facts and prepares semantic vectors for matching. Today I will show
how we designed it, what we tested and what still needs integration.”

## Slide 2 — The problem (40 seconds)

On screen: varied PDFs → manual entry → inconsistent data; keyword limitations.

Say: “A resume is easy for a person to read, but difficult for a workflow to process
consistently. Different layouts and languages make this harder. We separated document
understanding from the rest of HR so the same validated results can support hiring
and later employee workflows. Our aim is to assist review, not automate hiring decisions.”

## Slide 3 — From the brief to our machine (45 seconds)

On screen: AMD/ROCm brief → RTX 5060/CUDA adaptation → Gemini-assisted demo.

Say: “The initial brief targeted AMD ROCm. Our actual machine has an NVIDIA RTX 5060
Laptop GPU with 8 GB VRAM, so we changed the deployment target to CUDA. We prepared
the project for IBM Bob and Docker Desktop with WSL2. Later we added an explicit
cloud extraction option. The current demo uses Gemini; embeddings remain local.”

## Slide 4 — Architecture and ownership (60 seconds)

On screen: frontend → backend/worker → ML → backend storage/analytics.

Say: “Ele owns the UI. Hazma owns authentication, persistent records and background
jobs. My service owns inference and returns typed results. Analytics owns matching
logic and explanations. The browser does not directly call the GPU. The ML service
is stateless, so it can be changed without taking ownership of the entire HR database.”

Label backend/frontend boxes “integration planned” unless the team has separately
implemented and verified them by presentation day.

## Slide 5 — Resume extraction (60 seconds)

On screen: PDF bytes → text extraction → normalization → LLM → Pydantic JSON.

Say: “We parse PDF bytes in memory with pdfplumber and a pypdf fallback. We normalize
text while preserving characters important to different writing systems. Instructor
and Pydantic enforce the response contract: name, email, skills, experience, education
and summary. Missing values have explicit handling. A schema-valid answer can still
contain a factual mistake, which is why source review and labeled evaluations matter.”

Show a synthetic example only. Do not describe image-only PDFs as supported OCR.

## Slide 6 — Semantic embeddings (45 seconds)

On screen: short professional text → 384 numbers → cosine similarity.

Say: “The multilingual embedding model represents short passages as 384-dimensional
vectors. Analytics can compare candidate and job passages using cosine similarity.
We reject overlong input instead of silently cutting off its end. We also record model
revisions because two models can have the same vector size but incompatible meanings.”

## Slide 7 — Reliability decisions (60 seconds)

On screen: load once · one GPU permit · bounded input · safe shutdown.

Say: “Loading a model for every request would waste time and memory. We load resources
once during startup. The GPU semaphore admits one inference operation at a time.
We also handle cancellation carefully: a cancelled HTTP request does not necessarily
stop native GPU work. Shutdown drains active work before freeing models. Input limits
and consistent error codes help the backend recover predictably.”

## Slide 8 — How I built and improved it (50 seconds)

On screen: requirements → implementation → reproduce failure → fix → regression.

Say: “I coordinated an AI-assisted development workflow, adapted requirements to our
hardware and organized the work for Bob. We used observed test failures to guide
fixes. For example, Unicode cleanup originally removed characters needed by some
languages, and the backend client originally accepted redirects as success. Those
failures now have regression coverage.”

Be transparent: Codex tools assisted implementation/testing; Bob was configured
as the intended team IDE. Do not claim every line was manually written or Bob-tested.

## Slide 9 — What the tests show (60 seconds)

On screen: 61 × 10 = 610 earlier executions; latest 64 passes; real Gemini smoke pass.

Say: “The earlier 61-test suite passed ten rounds. After adding cloud-provider checks,
the suite reached 64 passing tests. Real localhost HTTP tests cover mixed requests,
errors and shutdown, but they use model doubles. Separately, Gemini completed a real
synthetic extraction. We have not yet verified the complete local GPU deployment.”

Do not label these results “100% accuracy” or “bug-free.” There are no measured
production throughput or extraction-accuracy numbers to show yet.

## Slide 10 — Current blocker and demo (60 seconds)

On screen: models downloaded; cloud extraction verified; Docker/GPU verification pending.

Say: “Both model artifacts are present. Large CUDA container downloads have been
slow and have failed with network/incomplete-file errors. Our installer retries and
is designed to check CUDA, readiness and both endpoints. We will mark the service
ready only after those checks actually pass.”

If deployment is ready by presentation time: show readiness, one synthetic PDF
result and a 384-dimensional embedding. If not: show the code flow, real cloud
smoke-test evidence and test report, clearly labeled. Never present fixtures as
live GPU output. Refresh this slide before presenting.

## Slide 11 — Team handoff and full HR roadmap (50 seconds)

On screen: three teammate ZIPs; hiring → onboarding → leave → payroll → performance.

Say: “We packaged contracts, code examples and next steps for each teammate. Hazma
gets the asynchronous client and schemas, Analytics gets vector guidance and the
cosine helper, and Ele gets UI workflow contracts. The remaining HR modules are
blueprinted, not completed here. Leave and payroll require deterministic rules;
we are not asking an LLM to invent entitlements or calculate authoritative pay.”

## Slide 12 — My next milestone (30 seconds)

Say: “My next milestone is a verified GPU service and a complete synthetic flow with
the team. After that, I will evaluate resumes across layouts and languages, record
quality and latency, and improve measured failures. The contribution so far is a
tested ML foundation with clear integration boundaries and honest deployment gates.”

## Likely questions and defensible answers

**Did you train a model?** No. We integrated pretrained models and engineered the
extraction, validation, inference lifecycle and API boundaries. Fine-tuning has not
been performed.

**Why an API key?** Cloud extraction requires provider authentication and usage
accounting. Fully local inference does not require an AI provider key. A key is
not part of the trained model or the CUDA driver.

**Why Gemini?** The OpenAI generation test hit an account-credit limit. Gemini
passed a real synthetic extraction test. This establishes a working demo option,
not that Gemini is universally more accurate or cheaper.

**Is it AMD accelerated?** The original plan was. The implemented deployment target
was changed to NVIDIA CUDA to match the actual laptop. Do not claim AMD execution
or original hackathon hardware compliance without separate validation.

**Why Docker if the LLM is in the cloud?** The intended service still runs local
GPU embeddings. Docker packages that runtime and the API. Cloud extraction alone
does not eliminate the current CUDA dependency.

**What does universal mean?** Extensible HR modules, multilingual text handling and
multi-industry input support. It does not mean every language or country's rules
have been evaluated or implemented.

**How accurate is it?** No representative accuracy benchmark is available yet.
Schema and regression tests pass, and synthetic cloud extraction works. Annotated
resume evaluation is the next quality gate.

**Is it secure or production-ready?** It has bounded input, typed errors and private
credential packaging. Full deployment, authorization integration, isolation, model
quality and operational testing are still required before production claims.

**Where is data stored?** This service does not persist resumes. Backend storage is
Hazma's responsibility. In Gemini mode, extracted text is sent to Google's API.
Do not describe the entire pipeline as offline or entirely local.

**What did you personally contribute?** Requirements and architecture decisions,
hardware adaptation, AI-assisted implementation coordination, test/fix review,
provider integration and team handoffs. Explain which work was tool-assisted.

## Presentation-day checklist

- Check the actual readiness and latest test evidence; update status slides.
- Use synthetic resumes and prepared examples, with live/recorded/mock labels.
- Hide terminals or files containing credentials; do not open .env on screen.
- Separate implemented code, verified behavior and planned modules on every slide.
- Do not claim completed team work without checking with its owner.
- Keep an honest walkthrough available if the GPU demo is unavailable.
