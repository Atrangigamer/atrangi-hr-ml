# Copy one task at a time into the responsible team's Bob workspace

These prompts are implementation tasks, not claims of completed platform modules.
Use the ML repository as a service dependency. Backend/frontend code belongs in
the team's repositories, not inside app/main.py here.

## Hazma: foundation

Read FULL_HR_BLUEPRINT.md. Build tenant identity, memberships, role checks, Employee,
Document, AuditEvent and durable ProcessingJob schemas with migrations. Add the
transactional outbox and cross-tenant authorization tests. Define and publish OpenAPI.
Use existing stack choices in our repository. Stop for a concrete design decision
only if the current repository and blueprint cannot determine it.

## Hazma + atrangi: hiring integration

Implement async resume upload/jobs using API_CONTRACT.md and backend_client.py.
Persist validated results, human corrections, model revisions and tenant IDs.
Implement bounded retries for transient failures without duplicate writes. Add job,
application, interview and offer flows, including idempotent offer-to-employee
conversion. Test a real ML service separately from mocked backend contract tests.

## Hazma + Ele: onboarding

Implement the onboarding entities, versioned templates, tasks, document requests,
review and completion states in FULL_HR_BLUEPRINT.md. Build the employee and HR
screens. Verify authorization, duplicate hire conversion and required task rules.

## Hazma + Ele: leave

Implement deterministic leave policies, work/holiday calendars, approval permissions
and an atomic leave ledger. Build employee requests and manager approvals. Test
overlaps, concurrent requests, half days, cancellations and timezone boundaries.
Ask HR for real policy inputs; do not infer entitlement from natural language.

## Hazma + domain owner: payroll

Implement payroll state transitions, decimal calculations, effective-dated inputs,
manual adjustments, immutable approval, payslip access and idempotent provider
exports. Start with explicit test policies. Keep statutory country logic behind a
validated adapter. Do not invent tax rules, submit payments, or call results compliant
without domain verification. Test rounding, reversals and duplicate exports.

## Hazma + Analytics + Ele: performance

Implement review cycles, configurable job-related criteria, goals, authorized
feedback and acknowledged reviews. Build reviewer/employee screens and audit trails.
Test permissions, closed cycles and missing data. Any future AI summary must be
evidence-linked draft text reviewed by a person, not an automated employment decision.

## Ele: universal interface

Implement screens against Hazma's OpenAPI for all confirmed modules, using translated
strings, Unicode names, RTL support where enabled and explicit timezone/currency
display. Include empty/loading/queued/review-required/error states and accessibility.
Never call the ML GPU container directly from the browser.

## atrangi: integration sign-off

Read the ML assessment, rerun CPU QA, start the CUDA container on RTX 5060/8 GB,
verify GPU offload and both live endpoints, measure VRAM and latency, and evaluate
labeled resumes across selected languages and industries. Reproduce each failure,
add a regression test, fix it and repeat. Record unresolved issues rather than
claiming a universally bug-free system.
