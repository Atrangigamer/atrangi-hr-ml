# Universal HR suite: implementation blueprint for Bob and the team

Confirmed scope: hiring, onboarding, leave, payroll and performance. This repository
delivers a working ML-service implementation plus contracts and build instructions
for the rest of the platform. The modules below are specified, not implemented here.

## Architecture

Ele's web application -> Hazma's authenticated backend -> PostgreSQL/pgvector and
durable workers. Workers call atrangi's private ML service. Analytics consumes
authorized records and versioned vectors through tenant-scoped services.

Use a modular backend initially: identity/tenancy, recruitment, people/onboarding,
leave, payroll, performance and analytics. Keep one authoritative employee record.
Do not duplicate employee data per module or let UI components call databases/GPU.

## Foundation before module work

- Entities: Tenant, User, Membership, Role, Employee, Department, Location,
  EmploymentContract, Document, AuditEvent, ProcessingJob and PolicyVersion.
- Every employer-owned record carries tenant_id. Verify membership and object
  ownership on reads/writes/jobs; test cross-tenant identifiers explicitly.
- Roles: applicant, employee, manager, recruiter, HR administrator, payroll
  administrator and tenant administrator. Payroll access is separately granted.
- Store instants in UTC; preserve tenant/location timezone for calendars. Monetary
  fields use decimal/minor-unit amounts plus currency, never binary floating point.
- Audit business changes; avoid candidate/employee document contents in logs. Use
  per-object file authorization and retention settings. Migrations are versioned.
- Durable jobs have queued/running/succeeded/failed/review_required states, attempt
  counts and idempotency keys. An outbox links transactional changes to jobs/events.

## Hiring

Entities: Candidate, JobRequisition, JobRequirement, Application, Interview,
Offer, ResumeExtraction and CandidateEmbedding. Track extraction/model versions.
Flow: upload -> parse job -> human review -> authorized matching -> interview ->
offer -> accepted offer -> employee/onboarding handoff in one idempotent operation.
APIs: /api/resumes/upload, /api/jobs, /api/applications, /api/interviews, /api/offers.
Tests: duplicate upload, corrupt/scanned document, uncertain facts, job cancellation,
cross-tenant candidate access, repeated offer acceptance and language-specific labels.

## Onboarding and employee records

Entities: OnboardingTemplate, OnboardingCase, TaskAssignment, DocumentRequest,
Acknowledgement, EquipmentAssignment. Workflow: accepted offer or manual employee
creation -> assigned template -> tasks/documents -> HR review -> active employee.
APIs: /api/employees, /api/onboarding/cases, /api/onboarding/tasks, /api/documents.
Tests: duplicate conversion, task ownership, required versus optional tasks,
expired document access and template version changes mid-onboarding.
ML role: optional future document classification/extraction, behind a separately
versioned schema. The delivered resume endpoint does not implement these features.

## Leave and attendance

Entities: LeaveType, LeavePolicyVersion, HolidayCalendar, WorkSchedule, LeaveLedger,
LeaveRequest, Approval and AttendanceEntry. Workflow: submit -> policy validation ->
authorized approval/rejection -> atomic ledger update -> notification/outbox.
APIs: /api/leave/balances, /api/leave/requests, /api/leave/approvals, /api/attendance.
Tests: simultaneous requests, overlapping leave, insufficient balance, half days,
timezone/DST boundaries, holiday changes, cancellation reversal and idempotent approval.
Backend uses deterministic policy calculations. An LLM must not approve leave or
invent an employee's entitlement. Local policies are supplied and validated by HR.

## Payroll and benefits

Entities: PaySchedule, CompensationVersion, PayComponent, PayrollRun, PayrollItem,
Adjustment, Payslip and PaymentExport. Separate draft/calculated/reviewed/approved/
exported/paid/reversed states, with explicit authorized transitions.
APIs: /api/payroll/runs, /api/payroll/adjustments, /api/payroll/approvals,
/api/payroll/payslips, /api/payroll/exports.
Use deterministic decimal arithmetic and effective-dated configuration. Country
tax/deduction engines belong to validated domain integrations. No single global
formula is supplied here; do not manufacture statutory rules in Bob prompts.
Tests: rounding per currency, proration, retroactive changes, failed exports,
duplicate payment/export idempotency, immutable approved runs and reversals.
Payment initiation requires a separate approved provider integration. The ML
service never calculates authoritative salary, tax, deductions or transfers money.

## Performance and learning

Entities: ReviewCycle, Goal, GoalUpdate, CompetencyFrameworkVersion, ReviewAssignment,
Feedback, Review and DevelopmentPlan. Flow: define criteria -> collect authorized
feedback -> draft review -> manager/employee review -> acknowledgement -> close.
APIs: /api/performance/cycles, /api/performance/goals, /api/performance/reviews.
Tests: reviewer authorization, self versus manager access, locked-cycle edits,
versioned criteria, missing feedback and audit trails. Aggregate dashboards enforce
appropriate access and minimum group sizes configured by the employer.
ML summaries are a future draft-assistance feature requiring evidence references
and human approval; they are not autonomous promotion/termination scores.

## Ownership and integration acceptance

Hazma implements domain APIs, policies, persistence, auth and workers. Ele implements
screens and internationalized status/error handling. Analytics defines metrics and
reviewable matching. atrangi owns the supplied ML service and its model evaluation.

Release order: foundation -> hiring vertical slice -> onboarding -> leave -> payroll
integration -> performance -> cross-module analytics. Each module needs API/schema
tests, tenant isolation tests, one end-to-end UI flow and failure recovery before its
status changes from planned to implemented. See docs/BOB_MODULE_PROMPTS.md.
