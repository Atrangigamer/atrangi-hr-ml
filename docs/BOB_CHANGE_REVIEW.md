# Bob changes reviewed — 27 September 2026

Compared the active files with the previous delivery ZIP because this project has
no Git repository. Preserved the change from get_sentence_embedding_dimension()
to get_embedding_dimension() and the matching test double. The installed real
SentenceTransformer exposes the new method. Bob's change is compatible.

Found a separate defensive-validation gap: finite, nonzero vectors with norms 0.5
or 2.0 were accepted despite the documented unit-norm guarantee. Two new tests
reproduced the issue. The wrapper now rejects vectors outside a 1e-5 relative and
absolute tolerance around norm 1. It retains model-provided normalization and does
not silently alter outputs. This protects Analytics if native inference misbehaves.

Validation: 79 tests passed in the full run and both repeat rounds; Ruff passed.
Repeated results: docs/qa_bob_review_results.json. Native models are doubled in
these tests; real deployment evidence is recorded separately in bob_review_live.json.

Antigravity/Gemini 3.7 configuration and public endpoint schemas remain unchanged.
This focused review is not proof of universal model accuracy or zero possible bugs.
