# Universal HR platform: shared design

The implemented component is the stateless intelligence service. Its current
capabilities are resume extraction and multilingual semantic vectors across sectors.
It is not a payroll engine or a complete HR information system.

## Implemented for a universal hiring foundation

- UTF-8 inputs and original-script names/qualifications; no US-only name/degree rules.
- Multilingual 384-dimensional embeddings, local instruction-tuned extraction and
  industry-neutral schemas. No hardcoded software-engineering skill taxonomy.
- Shared API usable by separate employers, geographies and job families; persistent
  tenant data, access control and regional settings remain in the backend.
- Country-neutral null/empty handling. Unknown experience is 0.0 in the existing
  schema; treat it as unknown unless a reviewer verifies the source.
- No protected-characteristic inference or automated hiring decision endpoint.

The default embedding model card lists 50 languages, but supported input is not the
same as validated extraction quality. Maintain a tested language/industry matrix;
route unsupported or low-confidence cases to human review. Scanned PDFs need OCR
upstream. This service does not yet accept DOCX/images or long passages automatically.

## Broader platform modules for the team

| Module | Primary owner | Dependencies / suggested phase |
| --- | --- | --- |
| Tenant/company, user, role and region configuration | Hazma | Foundation; tenant authorization on every data lookup |
| Recruitment/ATS, jobs, applications, interviews | Hazma + Ele | Current MVP with atrangi and Analytics integrations |
| Employee directory, onboarding and documents | Hazma + Ele | Next phase after hiring handoff is stable |
| Leave, attendance and approvals | Hazma + Ele | Explicit policy, timezone and local calendar configuration |
| Performance and learning | Hazma + Analytics + Ele | Human-owned criteria; role-specific configuration |
| Payroll/benefits | Dedicated domain owner + Hazma | Region-specific rules and provider integrations; not LLM arithmetic |
| Metrics and search | Analytics | Tenant-scoped data, agreed definitions and versioned embeddings |

Keep currencies, timezones, languages and policy versions explicit in persistent
records. Employers define job requirements and policy; a universal platform should
not assume every employer shares one scoring threshold or legal workflow.

This table is a confirmed full-suite roadmap, not a claim that these modules exist in
the delivered Python service. The code delivered here implements the ML endpoints; FULL_HR_BLUEPRINT.md and BOB_MODULE_PROMPTS.md specify the confirmed remaining platform work.
