# Open this project in IBM Bob

On this laptop, open the active project folder. Recipients can extract the archive.
Open the folder containing `AGENTS.md`, `app/`
and `Dockerfile` as the Bob workspace. Keep `.bob/rules/` visible. Bob supports
workspace rules there and root AGENTS.md project instructions; this package uses
both documented mechanisms. It does not require a special Bob runtime SDK.

Official reference: https://bob.ibm.com/docs/ide/configuration/rules

## First message to paste into Bob

```text
I am atrangi, AI/ML Lead for a universal HR platform. Read AGENTS.md, README.md,
docs/TEAM_HANDOFF.md, docs/UNIVERSAL_HR_SCOPE.md and ASSESSMENT.md first.
Our confirmed platform covers hiring, onboarding, leave, payroll and performance.
Read FULL_HR_BLUEPRINT.md and BOB_MODULE_PROMPTS.md for the wider implementation.
This ML project targets my RTX 5060 Laptop GPU (8 GB VRAM, compute capability 12.0)
on Windows using Docker Desktop with its WSL2 Linux backend. Preserve the existing
API contracts and cancellation-safe single-GPU scheduling. Run the CPU tests and
lint; reproduce and fix any failures. Check Docker/WSL2 and CUDA availability.
Read docs/RELEASE_STATUS.md first: the current cloud-mode image and models are
already installed. Preserve private .env, use the existing image, and avoid duplicate
downloads/builds. Verify actual GPU offload and both endpoints with synthetic resumes. Do not call mocked tests real GPU inference. Record commands, versions,
failures and remaining blockers. Review labels before enabling any language in
production. Keep backend, Analytics and frontend ownership from TEAM_HANDOFF.md.
```

## Work in these stages

1. **Review:** ask Bob to explain the current architecture and read the assessment.
2. **Verify CPU behavior:** create a test venv, install requirements-dev.txt, run
   `python qa_loop.py --rounds 10`, then Ruff. Fix reproduced defects first.
3. **Verify Windows GPU route:** Docker Desktop must be running Linux containers
   with WSL2 support. `nvidia-smi` must work on the host and in a GPU container.
4. **Prepare weights and build:** follow README.md. Use architecture 120 for this
   device. Start with the provided 1.5B Q4 model and 4096-token context, then measure.
5. **Evaluate:** parse representative multilingual/industry resumes and compare to
   human labels. Test both short passages and rejected overlong inputs. Run the
   live client after each model/configuration change.
6. **Handoff:** give each lead their documented subset and the generated OpenAPI.

Bob is the development assistant. Your application still runs as a normal FastAPI
service. Never put private candidate records, tokens or model weights into prompts
or source control just to make a test pass.
