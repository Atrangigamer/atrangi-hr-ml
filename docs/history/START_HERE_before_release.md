# Universal HR — one starting point

Owner: atrangi. Active workspace: this folder. Open this folder in IBM Bob.
Do not develop from extracted ZIP copies; they are handoff snapshots.

## What is ready

ML source, tests, backend client, API contracts, team packages and full HR blueprint.
Gemini extraction passed a real synthetic test; 64 regression tests passed.
CUDA deployment and real local embeddings are not yet verified. Read
INSTALL_STATUS.json and run ./status.ps1 for current state. Never start a second
installer while the existing one is active.

## Where things belong

| Folder/file | Purpose |
| --- | --- |
| app/ | FastAPI, extraction, embeddings and schemas |
| tests/ | Regression and HTTP tests |
| integrations/ | Hazma's async reference client |
| docs/ | Architecture, contracts, Bob prompts and your role guide |
| handoffs/ | ZIPs to send to teammates |
| models/ | Local model weights and revision manifest; do not share weights |
| scripts/ | Model preparation and safe packaging |
| .bob/ and .vscode/ | Bob rules, interpreter and tasks |
| .env | Private credentials; hidden, do not share |
| installation.log and INSTALL_STATUS.json | Local setup diagnostics |

## What you do next

1. Send Hazma_Backend.zip to Hazma, Analytics_Lead.zip to Analytics and
   Ele_Frontend.zip to Ele. Everyone opens START_HERE.md inside their ZIP.
2. Keep Docker running and finish the verified deployment. Gemini alone does not
   make the embedding endpoint operational. Check status.ps1 before trying requests.
3. After readiness, test a synthetic PDF via test_client.py and inspect its facts.
4. Give Hazma a reachable private service address and Analytics the model manifest.
5. Test upload -> extraction -> human review -> embeddings -> scoring -> display.
6. Evaluate more resumes and record accuracy, latency, GPU memory and limitations.

Read docs/ATRANGI_NEXT_STEPS.md for detailed steps. Full HR onboarding, leave,
payroll and performance are planned in docs/FULL_HR_BLUEPRINT.md, not completed
applications in this project. Hazma/Ele build those modules in their repositories.

## Useful commands in Bob's PowerShell terminal

```powershell
./status.ps1
# After the service is ready:
& .venv/Scripts/python.exe test_client.py --pdf synthetic-install-test.pdf
# After changing code:
& .venv/Scripts/python.exe -m pytest -q
& .venv/Scripts/ruff.exe check .
# Refresh source and teammate archives:
& .venv/Scripts/python.exe scripts/package_handoffs.py
```

The sibling Universal_HR_Hub folder contains shortcuts to these same live files.
It has no duplicate source or credentials. Older output folders are previous
snapshots; use this active workspace as the source of truth.
