# Analytics integration

Use `app.utils.cosine_similarity(a, b)` for finite equal-length nonzero vectors.
The result lies in [-1, 1]. It is not a calibrated hiring probability.

Default vector model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2,
384 dimensions. The published default input limit is 128 wordpieces including
special tokens; the runtime reads the actual model limit and rejects excess input.
Use short professional passages, with the same splitting/aggregation policy for
candidate and job text. Strip contact/identity fields from content used for ranking.

IMPORTANT MIGRATION: old all-MiniLM-L6-v2 vectors also have 384 dimensions but are
not the same vector space. Do not compare them. Create a new space/version, re-embed
both resumes and jobs, and switch queries only after backfill. Store model repository,
commit SHA and preprocessing policy per vector space using models/model_manifest.json.

Missing experience uses 0.0 because the existing API requires a float; missingness
must be checked against source/review before rejecting a candidate. Null education
details are unknown, not failed requirements. Qualification equivalence is configured
by domain/country, not guessed by the LLM. Score only job-related qualifications.

Own: scoring explanations, explicit required/optional skills, search, and metrics.
Hazma owns DB and tenant authorization; Ele displays your API output through backend.
Validate cross-language retrieval with labeled pairs before claiming parity with
English. Source: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
