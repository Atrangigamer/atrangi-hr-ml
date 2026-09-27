# Active installation handoff



Quality review update: 69 regressions pass after blank-key/cloud-context fixes and

retryable provider-error handling. See docs/QUALITY_SCORECARD.md. Gemini live eval

now shows high-demand 503 and rate-limit 429 failures; avoid immediate repeated API

evaluation calls. Earlier isolated smoke successes do not establish reliability.

Current runtime build captured code before these fixes: rebuild current source layers

after the active download finishes, then run real GPU checks. Do not interrupt it.





## Latest deployment recovery: 2026-09-26 afternoon



Installer 11748 exhausted retries on incomplete Docker base-image downloads and

exited. No active build was interrupted. New installer PID 46728 uses

ML_DOCKERFILE=Dockerfile.cloud from private .env. This verified runtime-image tag

has a 4.43 GB compressed base versus the original 9.49 GB devel image. It omits

llama.cpp compilation because Gemini is selected, retaining local CUDA embeddings.

The original Dockerfile remains for fully local extraction. Compose config passed;

real build/GPU checks remain pending. Verify current status rather than assuming

the old installer PID is active. This new build includes current Gemini code.





Latest: Gemini credential accepted and real synthetic extraction through the service

adapter passed. ML_LLM_PROVIDER=gemini is now selected in private .env. User explicitly

wants to keep this key for the demo; do not block on rotation. Gemini model is

gemini-3.8-flash (2.5-flash returned unavailable-for-new-users). Local CUDA embeddings

and image build remain pending. Keep .env hidden and current-user-only; after atomic

.env edits reapply its Windows ACL/Hidden attribute. Never print secrets.





## Latest update: 2026-09-26 11:01 IST



Previous installer failed after Docker Hub connection refusal. Connectivity recovered;

installer restarted as PID 11748 and is BUILDING. Verify current status/process before

any restart. Both weights are complete; do not redownload them unnecessarily.



User requested OpenAI key integration. Optional OpenAIExtractor is implemented and

64 tests pass. Real authentication/model lookup passed, but real synthetic extraction

returned HTTP 429 credit_balance_exhausted (no API credits). Local .env contains the

private credential; never print it, include it in ZIPs or run verbose Compose config.

ML_LLM_PROVIDER is explicitly reset to local while quota is unavailable. Ask for no

new key merely to fix quota on the same account. User may choose a different provider.

See docs/OPENAI_PROVIDER.md. No real GPU endpoint tests have passed yet.



User authorized installation, Docker access, debugging and opening/running the

project in IBM Bob. Target is RTX 5060 Laptop, 8 GB VRAM, Windows/WSL2, CUDA SM120.

Full HR suite scope is specified; executable code here is the ML component.



## Confirmed



- Docker Desktop started successfully; Linux WSL2 engine responds.

- Local .venv created; 68 test/model-preparation packages installed.

- 61 tests passed in this local .venv. Earlier QA ran 10 clean rounds.

- IBM Bob 2.2.0 IDE is installed and the project was opened via bobide.cmd.

- Bob Python/Docker extensions already exist; workspace interpreter/tasks configured.



## In progress / blockers



- Both models downloaded successfully. resume.gguf is 1117320736 bytes; SHA256

  6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e

  matches the downloaded content identifier. models/model_manifest.json records

  exact revisions. Download process exited 0. CUDA base image is still downloading.

- CUDA Docker image downloads are slow and suffered an unexpected EOF. The initial

  build did not complete. Current Dockerfile uses PyTorch 2.10.0 CUDA12.8 devel.

- Installer installs/checks dependencies and builds while existing downloads run,

  then waits for downloads, downloads missing weights, tests CUDA, starts Compose and

  smoke-tests both endpoints. Inspect INSTALL_STATUS.json and installation.log.

- Do not start duplicate installers. Confirm the PID in INSTALL_STATUS.json still

  exists and check its stage before taking over. FAILED requires diagnosing the log.

- Actual GPU model inference has NOT yet passed. Never describe the service as live

  until readiness and both endpoint smoke tests succeed.



## Resume work



1. Read INSTALL_STATUS.json and tail installation.log. Inspect docker compose ps/logs.

2. Check models/model_manifest.json; only a complete download writes it.

3. If no installer is alive, run install_and_run.ps1 from this directory and capture

   output. Fix real build/runtime failures, preserving prior regression tests.

4. When healthy, run test_client.py on synthetic input and measure GPU use/latency.

5. Update ASSESSMENT.md, VALIDATION.md and the ZIP; exclude .venv, model weights,

   download caches, logs and synthetic temporary files.



Bob launcher: C:/Users/hp5cd/AppData/Local/Programs/IBM Bob/bin/bobide.cmd

Project: this folder. Documentation: docs/BOB_START_HERE.md and TEAM_HANDOFF.md.

Do not assume a stopped/completed process succeeded; verify its output artifacts.



Build-context note: active build mhsree6oowtd5g05tp74kjgcw captured app code before Gemini edits. After it completes, rebuild once from current files (cached base layers) before accepting live tests; the original installer may fail startup on gemini provider until this is done. Do not interrupt the active base-image download.


Latest recovery: runtime base image downloaded completely. Build failed due PEP668 then missing ensurepip. Both Dockerfiles now create --without-pip --system-site-packages venv, inheriting base pip/Torch. Manual compose build PID66928/session6046 is installing packages; do not duplicate. Original installer46728 exited. After build, run CUDA tensor test, Compose readiness and real endpoints; status is manually tracked until READY.

Continuation: PID55556 runs install_and_run.ps1 -WaitForBuildProcessId 66928. It waits for manual dependency build, then validates current image with cached build and performs CUDA/startup/endpoint checks. No parallel build is intended. Check status and these process identities before launching anything.

New build blocker found: base spin0.16 requires click<8.4; pip installed8.5.0. requirements.txt now pins click8.3.1. Existing installer55556/current build8924 still downloading; not interrupted. Helper PID28032 waits for installer55556 exit and restarts installer only if it failed and status still belongs to55556. Do not launch a duplicate. Helper source: work/resume_after_click_fix.ps1 in workspace.

Correction: click8.3.1 was below Instructor1.17 requirement>=8.3.3. Verified uv dry-run click8.3.3 satisfies Instructor; also fits base spin<8.4. Both requirements files now pin8.3.3. Previous installer28032 exited. New installer PID66164 started; verify status before acting.


## Latest hardware verification

Docker image build passed; real CUDA tensor execution and a real normalized
384-dimensional embedding passed on RTX 5060. Current cloud-adapter source hash
matches the image. Gemini returned HTTP 429 during startup twice, so the full HTTP
service is not live. See docs/deployment_verification.json. Avoid rapid API retries.

User confirmed Gemini quota exhausted and asked to retry after midnight. Automation rescheduled once for 2026-09-27 00:05 IST; no retries before then. Local-midnight quota reset is not guaranteed. Existing image and GPU tests passed, so retry startup without rebuilding unless code changed.


## Midnight follow-up — 27 September 2026, 00:06 IST

Existing container was paused; it was unpaused without rebuilding. Readiness returned
200. Real HTTP embedding returned200 with a normalized384-dimensional vector
(0.032 seconds for this one request, not a benchmark). Resume HTTP request returned
503 from a provider rate/quota failure. No further generation requests were made.
Service is running locally in degraded condition; full acceptance is NOT passed.
See docs/live_endpoint_verification.json. The midnight retry did not resolve quota.
