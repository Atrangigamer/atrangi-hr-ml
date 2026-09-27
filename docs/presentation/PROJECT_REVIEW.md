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

> Latest quality review: 69 tests pass; live evaluation encountered 503/429 provider errors. GPU deployment is pending. Provisional ML-service rating: 6.9/10. See ../QUALITY_SCORECARD.md.

# Universal HR: project development review

**Presenter:** atrangi — AI/ML Lead  
**Review date:** 26 September 2026  
**Delivery:** ML intelligence service, integration contracts and full HR implementation blueprint

## 1. Executive overview

Universal HR is a proposed full-stack platform covering hiring, onboarding, leave,
payroll and performance. The implemented contribution in this repository is its
stateless ML microservice: structured resume extraction, semantic embeddings and
a reusable cosine-similarity helper. The remaining business modules are specified
for the backend, frontend and analytics teams to implement.

The project began with an AMD ROCm hackathon plan. It was adapted to the available
Windows laptop with an NVIDIA RTX 5060 Laptop GPU and approximately 8 GB VRAM.
The development workflow was prepared for IBM Bob, with Docker Desktop/WSL2 as
the intended runtime. The current demo configuration uses Gemini for extraction
and retains local CUDA embeddings. A local llama.cpp extraction option remains.

The latest completed regression suite has 64 passing tests. An earlier 61-test
suite passed ten independent rounds, totaling 610 executions. Real Gemini extraction
passed on synthetic input. Full Docker/GPU deployment and local embedding inference
remain unverified because large CUDA image downloads have repeatedly failed or
continued slowly. These are separate levels of evidence, not interchangeable claims.

## 2. Problem and intended value

Resumes arrive as documents rather than consistent database records. Their formats,
terminology and languages vary. Manual entry makes hiring workflows slow and
inconsistent, while keyword-only matching can miss related professional experience.
The broader HR lifecycle also needs continuity between candidate and employee data.

The ML service addresses two narrow problems: converting text-bearing resume PDFs
to validated structured facts, and converting short professional passages to vectors
that Analytics can use for semantic comparison. It supports human review; it does
not decide who gets hired or provide a calibrated probability of hiring success.

Expected benefits are reduced re-entry, consistent contracts and reusable semantic
representations. No measured reduction in hiring time, accuracy percentage or
business ROI has yet been established.

## 3. How the project evolved

| Stage | Decision and implementation | Reason |
| --- | --- | --- |
| Initial requirements | Two FastAPI ML endpoints, strict schemas, local inference, ROCm target | Follow the original hackathon brief |
| Hardware correction | Switch to NVIDIA CUDA for RTX 5060, 8 GB, Windows/WSL2 | Match the actual machine |
| Scope expansion | Define hiring, onboarding, leave, payroll and performance modules | Support the user's full HR vision |
| ML design | Keep the service stateless and place persistence/jobs in the backend | Separate inference from business workflows |
| Model handling | Load models once; serialize GPU inference; drain work during shutdown | Control memory and lifecycle behavior |
| Universal support | Choose multilingual embeddings and preserve script-sensitive Unicode | Avoid an English/technology-industry-only design |
| Development workflow | Prepare Bob rules, tasks, interpreter and module prompts | Make the work easier to continue in the team's IDE |
| Verification | Reproduce failures, fix them and repeat regression runs | Turn observed defects into permanent checks |
| Cloud option | Add OpenAI, then Gemini as explicit extraction providers | Support a cloud-assisted demo path |
| Delivery | Create role-specific ZIPs and a project hub | Make ownership and integration steps clear |

The OpenAI key authenticated, but generation failed because its account had no API
credits. Gemini accepted the supplied credential. A first Gemini model returned an
availability error; the provider-recommended model, gemini-3.8-flash, subsequently
passed synthetic structured extraction through the service adapter. Initial failures
mean this is a smoke-test result, not a reliability or accuracy benchmark.

IBM Bob was opened with the project and configured with tasks/rules. Implementation
and debugging in this recorded workflow were AI-assisted through Codex tools. Do
not claim that Bob independently wrote or verified all code. Bob is the IDE;
Docker hosts the service, and the selected cloud provider performs cloud extraction.

## 4. Architecture and data flow

```text
Ele's frontend                         [planned integration]
       |
       v
Hazma's authenticated backend          [planned integration]
       |                 |
       |                 +--> PostgreSQL / pgvector / job records
       v
Durable background worker              [planned integration]
       |
       v
FastAPI ML service                     [implemented]
       +--> PDF extraction --> validated ResumeSchema
       |                        ^
       |                        |
       |                 Gemini API (demo)
       |                 or local llama.cpp / OpenAI
       |
       +--> local CUDA SentenceTransformer --> 384-dimensional vector
                                                        |
                                                        v
                                          Analytics scoring and explanations
                                          [helper implemented; workflow planned]
```

The service accepts one request, performs inference and returns a result. It does
not own employee records, tenant authorization, job queues or long-term document
storage. Hazma's backend must supply those capabilities. The frontend talks to the
backend, not directly to the GPU service. A local loopback address is not a remote
team deployment address.

## 5. Implemented ML pipeline

### Resume extraction

`POST /ml/parse-resume` accepts a multipart `file` containing PDF bytes. It validates
size and document constraints, parses in memory, normalizes text and passes the
result to the selected extraction provider. pdfplumber is the primary parser;
pypdf supplies validation and fallback extraction, including recoverable pages.

Instructor connects model output to the Pydantic contract. All response keys are
required; nullable fields can explicitly represent unknown facts. Extra fields and
invalid values are rejected. The schema includes candidate_name, email, skills,
experience_years, education and summary. Education contains degree, institution
and graduation_year. Missing experience currently becomes 0.0 under the original
contract, so the UI must not treat it as a verified absence of experience.

Prompts tell the model to preserve names and qualifications, avoid inventing facts
and treat resume instructions as untrusted content. These controls reduce risk;
they do not prove immunity to prompt injection or hallucination. Human correction
and evaluation remain necessary.

Limits include a 10 MiB PDF, 20 pages and 24,000 extracted characters. Local LLM
context is checked separately. Scanned image-only PDFs need an OCR stage that is
not implemented here. Encrypted or unreadable PDFs produce actionable errors.

### Embeddings and scoring

`POST /ml/generate-embedding` accepts JSON containing text and returns 384 finite
floating-point values plus the dimension count. The chosen multilingual model is
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2. The loader requires
CUDA, loads local weights and rejects an unexpected vector dimension.

The model's token limit is read at runtime. Oversized passages are rejected rather
than silently truncated. Candidate and job text must be split consistently by the
integration layer. Vectors from different models must not be mixed merely because
both contain 384 values; model revisions and preprocessing identify the vector space.

The standalone helper computes cosine similarity:

`similarity(a, b) = dot(a, b) / (length(a) * length(b))`

Its range is [-1, 1]. It validates compatible, finite, nonzero vectors. Analytics
must add job-related qualification rules and explanations. Similarity is not an
objective assessment of a person's worth or a probability of hiring success.

## 6. Reliability and deployment engineering

FastAPI's async lifespan allocates expensive resources once. A single server worker
avoids duplicating models. An asyncio semaphore limits inference concurrency to one.
Blocking work runs outside the event loop, and cancellation handling retains permits
until native work actually finishes. Shutdown stops new/queued work and drains tasks
before closing resources.

The request middleware limits actual body bytes rather than trusting only the
Content-Length header. Health endpoints distinguish a live process from readiness
after warmup. Error responses use consistent codes; sensitive provider exception
details and document text are not returned in API failures.

Docker targets PyTorch with CUDA 12.8 and architecture 120. Model volumes are local;
the service port is bound to loopback. Docker Desktop uses the Linux WSL2 engine.
The installer is designed to build, check a real CUDA tensor operation, start the
container and smoke-test both endpoints. That full sequence has not yet passed.

API keys are private configuration, excluded from Git, Docker build context and
shared ZIPs. The local file is hidden and restricted by Windows permissions.
It is not encrypted storage and not a guarantee against administrator/process
access. Cloud mode sends extracted text to the selected provider; local mode does
not automatically fall back to the cloud. The demo uses the user-approved existing
Gemini credential; never display credentials in presentation screenshots.

## 7. Testing and bug-fix review

| Evidence | Result | What it establishes |
| --- | --- | --- |
| Earlier repeated regression suite | 61 tests × 10 rounds = 610 passes | Repeatability of covered application behavior |
| Latest suite after cloud adapter additions | 64 tests passed | Added configuration, cleanup and safe-error checks |
| Real localhost Uvicorn test | Mixed HTTP requests, failure/recovery and shutdown passed | Real HTTP handling with model doubles |
| Lint and Compose validation | Passed in recorded checks | Static consistency and valid Compose configuration |
| Downloaded weights | Both downloaded; revisions recorded; LLM checksum checked | Model artifacts present |
| Gemini service-adapter smoke test | Passed on synthetic data | One real structured cloud extraction path |
| Full CUDA/container endpoints | Pending | No verified GPU deployment or performance benchmark |

Recorded fixes include readiness error handling, configuration validation, PDF page
limits/recovery, cleanup after failures, startup cancellation allocation leaks,
queued work during shutdown and multipart error consistency. During the universal
HR migration, two test cases exposed Unicode joiner removal damaging Persian/Indic
text; the normalizer now retains script-significant joiners. Another defect accepted
redirects as successful backend responses; the client now rejects non-2xx responses.

One non-failing test-client deprecation warning remains. Ten repeated rounds do not
mean 610 distinct scenarios, and passing tests do not mean the software is bug-free.
The latest 64-test suite is not the suite represented by the earlier 610 count.

## 8. Team ownership and my contribution

| Owner | Responsibility | Handoff |
| --- | --- | --- |
| atrangi | ML service, provider configuration, model evaluation, deployment and contracts | Complete source, tests, model manifest and runbook |
| Hazma | Authentication, tenant authorization, workers, storage, domain APIs | Backend ZIP with reference client, schemas and OpenAPI |
| Analytics Lead | Job-related matching, vector policies, scoring explanations and metrics | Analytics ZIP with helper and vector-space guidance |
| Ele | Upload/review/status UI and full-suite screens through backend APIs | Frontend ZIP with contracts and workflow guidance |

Presentation wording for your role: “As ML lead, I defined the inference boundaries,
adapted the design to our available hardware, coordinated AI-assisted implementation,
and organized testing and integration handoffs. My next responsibility is validating
model quality and completing the real GPU integration with the team.”

The source PDF calls the ML lead Antragi; the user corrected the name to atrangi.
It labels Analytics as “You”; no confirmed personal name should be invented.

## 9. Full HR scope and remaining work

| Module | Current delivery | Work remaining |
| --- | --- | --- |
| Hiring | Resume ML code, schemas, embeddings code, scoring helper | Durable backend workflow, UI, live integration and quality evaluation |
| Onboarding | Entities, workflow and acceptance blueprint | Templates, tasks, document handling and employee conversion |
| Leave | Policy/ledger/workflow blueprint | Deterministic calculations, approvals and concurrency tests |
| Payroll | Versioned calculation/approval blueprint | Validated policy integrations, rounding, payslips and audit controls |
| Performance | Review-cycle and permissions blueprint | Goals, feedback, review UI and access controls |

Universal means an extensible multi-industry, multilingual design—not validated
support for every language, jurisdiction or HR policy. Payroll calculations and
leave entitlements must use validated deterministic rules, not LLM guesses.

## 10. Next milestones and acceptance criteria

1. Complete the CUDA image and verify its current code includes the Gemini adapter.
2. Pass real CUDA tensor execution, readiness, PDF extraction and local embeddings.
3. Record GPU memory, startup time and request latency; do not invent results.
4. Evaluate 20–30 initial synthetic/authorized resumes with manual annotations and
   a separate holdout set. Track missing facts, invented facts and field accuracy.
5. Agree passage splitting/model metadata with Analytics and retry/job rules with Hazma.
6. Run one synthetic end-to-end flow through Ele's UI and Hazma's backend.
7. Expand modules in order: foundation, hiring, onboarding, leave, payroll, performance.

## 11. Evidence map for reviewers

- app/main.py: endpoints, lifecycle, readiness and error handling.
- app/extractors.py and app/openai_extractor.py: PDF/local/cloud extraction.
- app/schemas.py: request and response contracts.
- app/embeddings.py and app/utils.py: vectors, validation and cosine helper.
- tests/: repeatable regressions; qa_results.json: earlier ten-round evidence.
- Dockerfile, compose.yaml and install_and_run.ps1: intended CUDA deployment.
- models/model_manifest.json: exact downloaded revisions.
- docs/FULL_HR_BLUEPRINT.md: planned full-suite architecture.
- docs/TEAM_HANDOFF.md and handoffs/: recipient responsibilities and deliverables.

This review summarizes repository evidence and the recorded development workflow.
It is not a certification of production readiness. Refresh deployment status and
measured results immediately before presenting.
