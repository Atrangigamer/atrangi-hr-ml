# Ele: frontend handoff

Call Hazma's authenticated API. Keep the local ML service private. The source plan
assigns you Next.js/React UI, the ATS board, upload flow and analytics views.

Build: PDF upload, queued/processing/review-required/complete/failed states; editable
candidate facts; job/application views; analytics explanations. Ask Hazma for the
durable job/status API contract; this microservice returns results synchronously.

Show actionable errors: scanned PDF needs OCR, corrupt/encrypted PDF needs replacement,
oversized resume needs shortening, temporary service capacity needs retry. A resume
upload can require several minutes; don't block the UI waiting on the GPU request.

Universal HR: Unicode names, translated UI strings, RTL layouts where enabled,
localized display dates and explicit timezone/currency labels for broader modules.
Don't translate legal names or invent equivalent degrees. Allow human correction.
Do not label 0.0 years as a verified zero, or display similarity as hiring probability.

API_CONTRACT.md describes the ML response for coordination; it is not permission
to call the ML service directly from the browser or expose its Docker port publicly.
