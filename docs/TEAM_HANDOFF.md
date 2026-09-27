# Who receives what

## Files to send now

| Person | Send this ZIP | First file to open |
| --- | --- | --- |
| Hazma | handoffs/Hazma_Backend.zip | START_HERE.md |
| Analytics Lead | handoffs/Analytics_Lead.zip | START_HERE.md |
| Ele | handoffs/Ele_Frontend.zip | START_HERE.md |
| atrangi (you) | Keep universal_hr_cuda_bob.zip, the complete source project | docs/BOB_START_HERE.md |

Every recipient ZIP includes the full HR blueprint, Bob prompts, integration
checklist and a dated release-status snapshot. They are integration subsets, not
standalone services. Hazma also gets minimal Python integration dependencies.
The weights, local environment and installation logs are deliberately excluded.
Regenerate these ZIPs with `python scripts/package_handoffs.py` after changing
contracts or after model_manifest.json becomes available. The manifest's metadata
is automatically included for Hazma and Analytics when present.

## Ownership from the source plan

Source: AMD_2.0_Hackathon_HR_Project_Plan.pdf, pages 1-3. The original file assigns
Antragi to ML, Hazma to backend, "You" to Analytics and Ele to frontend. The user
corrected the ML name to **atrangi** and changed hardware to **NVIDIA CUDA**.
The source PDF itself is unchanged. Its team boundaries still apply.

| Recipient | Send these files from this project | Their next work |
| --- | --- | --- |
| atrangi / you | Complete project, Bob rules, Dockerfile, compose.yaml, scripts, tests, assessment | Own model quality, CUDA deployment, extraction, embeddings and ML availability |
| Hazma, Backend Lead | docs/API_CONTRACT.md, docs/openapi.json, app/schemas.py, integrations/backend_client.py, docs/UNIVERSAL_HR_SCOPE.md | Add authenticated upload routes, durable worker jobs, per-tenant storage, pgvector, retries and audit events |
| Analytics Lead (called "You" in the PDF; confirm their actual name) | app/utils.py, docs/ANALYTICS_HANDOFF.md, docs/API_CONTRACT.md, model_manifest.json after download | Own candidate/job scoring, qualification rules, NL search and dashboards; version vector space and re-embed old records |
| Ele, Frontend Lead | docs/FRONTEND_HANDOFF.md, docs/API_CONTRACT.md, docs/UNIVERSAL_HR_SCOPE.md | Build upload/job-status/results screens, multilingual UI, ATS board and human review flows against Hazma's API |

`model_manifest.json` is created inside `models/` by the download script; send its
metadata to Hazma/Analytics, not the large weights. No messages have been sent.
Recipient ZIPs under the delivered handoffs folder contain the currently available
files. Share refreshed OpenAPI and model metadata after interface/model changes.

## Sequence for the team

1. atrangi: validate the service and supply its private URL, OpenAPI and model IDs.
2. Hazma: accept UI uploads, persist a job and enqueue processing. The worker calls
   ML, stores returned facts, splits professional content into short passages and
   requests embeddings. Map 400/413/422 to corrective action; bounded-backoff 503.
3. Analytics: apply the same passage policy to resumes and jobs, version each vector
   space, implement reviewable ranking and explicit job-specific filters.
4. Ele: display queued/processing/failed/review-required/complete states, editable
   extracted facts and explanations. Talk to Hazma's API, never directly to the GPU.
5. All: integrate one synthetic end-to-end case, then multilingual and multi-industry
   cases. Freeze the contract for the demo and record known limitations honestly.

The PDF asks Analytics to combine semantic similarity with qualifications. It does
not supply a scientifically calibrated fit-percentage formula. Do not present raw
cosine similarity as a probability of hiring success.
