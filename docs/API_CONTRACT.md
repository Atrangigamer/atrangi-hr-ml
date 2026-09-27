# ML contract for Hazma and Analytics

Base URL: private deployment URL supplied by atrangi. Within the supplied Compose
network the service name is `ml`; for host tools use http://127.0.0.1:8000.
OpenAPI is provided as docs/openapi.json and live at /openapi.json.

| Method/path | Request | Response |
| --- | --- | --- |
| POST /ml/parse-resume | multipart field file containing raw PDF bytes | ResumeSchema |
| POST /ml/generate-embedding | JSON {"text":"short professional passage"} | {"embedding":[384 finite floats],"dimensions":384} |
| GET /health/live | none | {"status":"alive"} |
| GET /health/ready | none | 200 ready after model warmup, otherwise 503 |

ResumeSchema keys: candidate_name (nullable string), email (nullable string), skills
(string array), experience_years (float), education (array with degree, institution,
graduation_year, each nullable), summary (string). All keys required. Extra keys
rejected. A null/empty field means unknown/absent, not a failed qualification.
Missing experience maps to 0.0 under this original contract; verify with source.

Errors: {"error":{"code":"...","message":"..."}}. 400 invalid PDF/context,
413 body too large, 422 schema/embedding-token limit, 500 inference failure,
503 unavailable/busy. Queue capacity responses include Retry-After. Transport
limits or reverse proxies can still return non-JSON errors.

PDF limits: 10 MiB file, 20 pages, 24,000 extracted characters; a separate LLM token
budget may reject a shorter document. Scanned PDFs require upstream OCR. Embedding
token limit is read from the model; the default multilingual model uses 128 tokens.
Do not silently truncate or mix old English-model and new multilingual-model vectors.

The service is stateless and private. Backend authenticates, authorizes tenants,
assigns durable job IDs, handles bounded retries and persists results. Do not expose
GPU routes directly to employees, applicants or web browsers. Request cancellation
does not terminate native GPU work; avoid immediate duplicate retries after timeouts.

See integrations/backend_client.py for an async client. It intentionally does not
retry 500 or invalid-input failures automatically. Validate successful responses
against app/schemas.py or generated OpenAPI before persisting them.
