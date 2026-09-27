# atrangi: your next work as AI/ML lead

You own the quality and availability of the platform's ML component: resume
extraction, embeddings, GPU inference, model versions and its API contract.
Hazma owns backend data/jobs/authentication, Analytics owns ranking and metrics,
and Ele owns the frontend. The full HR blueprint is a team implementation plan.

## 1. Finish and verify deployment

Open the active project in IBM Bob. Installation is complete; no installer is
needed. Keep Docker Desktop running and check `./status.ps1`. To resume the
existing image, run `docker compose up -d --no-build --wait --wait-timeout 180`.

The installer must pass: CUDA tensor execution inside Docker, model startup,
GET /health/ready, a synthetic PDF extraction and a 384-dimensional embedding.
After READY, open http://127.0.0.1:8000/docs on this laptop.

For a manual endpoint check after startup:
```powershell
& .venv/Scripts/python.exe test_client.py --pdf synthetic-install-test.pdf --text "Customer service and inventory management"
docker compose logs --tail 100 ml
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv
```

Record the actual model revisions, VRAM before/after loading, cold-start time,
request latency and any errors. A valid JSON response proves the contract works;
it does not prove the extracted facts are correct. Read the response against the PDF.
After deployment, `./stop.ps1` stops the container and `./start.ps1` starts/builds it.
Keep this laptop awake for teammates' scheduled integration tests.

## 2. Establish an extraction quality baseline

Prepare an initial set of 20-30 synthetic or appropriately authorized resumes.
Include short/long documents, several industries, varied layouts, non-Latin text,
missing fields and overlapping jobs. Keep corrupt, encrypted and scanned PDFs as
separate error-handling cases; scanned documents currently need OCR elsewhere.
This initial set is a smoke evaluation, not proof of universal language support.

For every sample, manually record expected name, email, skills, education and
document-supported experience. Define how overlapping dates and missing dates
should be interpreted. Flag ambiguity instead of inventing a ground-truth value.

Compare extraction with the annotations: field accuracy, missing facts, invented
facts and schema failure rate. Review skills as sets; assess the summary sentence
by sentence against the document. Report results by language/layout as well as
overall. Set acceptance thresholds with the team before judging a new model.

Keep a separate holdout set. Save each failure as a regression case. Change one
prompt/model/setting at a time, rerun the same evaluation and compare the results.
Avoid logging personal document contents. Keep evaluation data outside shared ZIPs.

## 3. Make embeddings usable for Analytics

Agree a short-passage splitting policy with Analytics. The current multilingual
model produces 384 values and has a short token limit; full resumes will often
exceed it. Hazma's worker should split professional text before calling the endpoint.
Candidate and job passages must use the same preprocessing and aggregation policy.

Hand over the completed models/model_manifest.json. Every stored vector
space needs model revision and preprocessing metadata. Equal vector dimensions do
not mean two models are compatible. Re-embed candidates and jobs together after a
model change. Test relevant/irrelevant pairs and cross-language pairs with Analytics.
Cosine similarity is a similarity measure, not a hiring-success percentage.

## 4. Integrate with Hazma and Ele

Send the role-specific ZIPs listed in TEAM_HANDOFF.md. Publish any contract change
to Hazma and Analytics before updating the service. Keep API examples synthetic.

Agree with Hazma: private service address, connection timeout, job states, bounded
retries, idempotent persistence, error mapping and version metadata. localhost only
works on the host itself; agree a private network arrangement before remote access.
Ele calls Hazma's authenticated API and polls durable jobs, not this ML endpoint.

Run one joint flow: upload -> queued/running -> parse -> review/correct -> embed ->
store -> score -> display. Then test duplicate jobs, corrupt documents, unavailable
ML and capacity pressure. Hazma must verify tenant isolation and access controls.

## 5. Maintain reliability on the 8 GB GPU

Keep one server worker and GPU concurrency one until actual measurements justify
a change. Other laptop programs consume VRAM too. Measure simultaneous requests,
queue waits, latency and GPU memory; document supported demo load.
If OOM occurs, inspect logs and available VRAM before changing model/context sizes.
Rerun quality evaluation after any reduction. Re-run regression tests after code
changes and real-model smoke tests after dependency/model/container changes.

```powershell
& .venv/Scripts/python.exe qa_loop.py --rounds 10
& .venv/Scripts/ruff.exe check .
docker compose config --quiet
& .venv/Scripts/python.exe scripts/package_handoffs.py
```

## 6. Support the full HR suite without expanding ML prematurely

Help the team integrate hiring first. For onboarding, document classification or
extraction can be a future separately versioned endpoint with its own evaluation.
For leave/payroll, Hazma implements deterministic policy calculations and approvals.
Performance summaries, if added, need evidence-linked inputs and human review.
The existing resume endpoint does not implement these full-suite capabilities.

For each proposed ML feature, write: user need, input, output schema, authorized
data, evaluation cases, failure behavior and latency/VRAM budget. Implement only
after these are agreed. Do not silently add responsibilities to the resume schema.

## Your handoff is complete when

- The GPU service actually runs and both endpoints pass real-model smoke tests.
- Evaluation results and known limitations are documented, not just unit-test counts.
- Hazma has verified the live worker integration and Analytics has vector metadata.
- Ele's flow shows reviewable results and actionable failures through the backend.
- The team can restart the service, reproduce a synthetic demo and identify versions.

Your immediate order: finish deployment, evaluate a synthetic resume, share the
verified address/manifest, run the joint flow, then improve measured quality issues.
