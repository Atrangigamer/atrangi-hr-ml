#!/usr/bin/env bash
# deploy_hf.sh — push this ML service to a Hugging Face Space (free CPU tier).
#
# PREREQUISITES (one-time):
#   pip install huggingface_hub
#   huggingface-cli login          # paste your HF write token
#
# USAGE:
#   bash deploy_hf.sh YOUR_HF_USERNAME YOUR_SPACE_NAME
#
# After this runs, go to:
#   https://huggingface.co/spaces/YOUR_HF_USERNAME/YOUR_SPACE_NAME/settings
# and add a Secret named ML_GEMINI_API_KEY with your Google API key value.
# The service will restart and be reachable at:
#   https://YOUR_HF_USERNAME-YOUR_SPACE_NAME.hf.space
#
# WHAT THIS DOES:
#   1. Creates (or reuses) an HF Space with SDK=docker and hardware=cpu-basic (free).
#   2. Copies app/, models/embedding, requirements.free.txt and Dockerfile.free.
#   3. Renames Dockerfile.free -> Dockerfile so HF picks it up automatically.
#   4. Pushes everything. HF builds the image and starts the container.
#
# LIMITATIONS:
#   - CPU embeddings: ~200-400 ms vs ~30 ms on your RTX 5060.
#   - HF Spaces free tier sleeps after 48h of inactivity; first request wakes it.
#   - model weights (models/embedding) must exist locally before running this.
#   - ML_GEMINI_API_KEY must be set as a Space Secret — never committed to the repo.
#   - No auth: anyone with the URL can call your endpoints. Add auth via Hazma's
#     backend before exposing candidate data.

set -euo pipefail

HF_USERNAME="${1:?Usage: bash deploy_hf.sh HF_USERNAME SPACE_NAME}"
SPACE_NAME="${2:?Usage: bash deploy_hf.sh HF_USERNAME SPACE_NAME}"
REPO_ID="${HF_USERNAME}/${SPACE_NAME}"

echo "==> Checking huggingface_hub CLI..."
python3 -c "import huggingface_hub; print('huggingface_hub', huggingface_hub.__version__)"

echo "==> Checking HF login..."
python3 -c "from huggingface_hub import whoami; u=whoami(); print('Logged in as:', u['name'])"

echo "==> Creating/reusing Space: ${REPO_ID}"
python3 - <<PYEOF
from huggingface_hub import HfApi
api = HfApi()
try:
    api.repo_info(repo_id="${REPO_ID}", repo_type="space")
    print("Space already exists — reusing.")
except Exception:
    api.create_repo(
        repo_id="${REPO_ID}",
        repo_type="space",
        space_sdk="docker",
        space_hardware="cpu-basic",  # free tier
        private=False,
    )
    print("Space created.")
PYEOF

# Build a temporary deploy directory with only what HF needs.
DEPLOY_DIR=$(mktemp -d)
trap 'rm -rf "$DEPLOY_DIR"' EXIT

echo "==> Preparing deploy directory: ${DEPLOY_DIR}"
cp -r app            "${DEPLOY_DIR}/app"
cp requirements.free.txt "${DEPLOY_DIR}/requirements.free.txt"
# HF Spaces always looks for a file named "Dockerfile" at the repo root.
cp Dockerfile.free   "${DEPLOY_DIR}/Dockerfile"

# Include the embedding model weights (required for startup).
if [ ! -d "models/embedding" ]; then
    echo "ERROR: models/embedding not found. Run scripts/download_models.py first."
    exit 1
fi
cp -r models/embedding "${DEPLOY_DIR}/models_embedding"

# HF Spaces Docker builds can't mount volumes, so we embed the model.
# Patch Dockerfile to COPY the model into /models/embedding at build time.
sed -i 's|^COPY --chown=mlservice:mlservice app ./app|COPY --chown=mlservice:mlservice app ./app\nCOPY --chown=mlservice:mlservice models_embedding /models/embedding|' \
    "${DEPLOY_DIR}/Dockerfile"

# README.md is required by HF Spaces — it holds the Space metadata header.
cat > "${DEPLOY_DIR}/README.md" <<MDEOF
---
title: atrangi HR ML Service
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# atrangi HR ML Service

FastAPI ML service: resume parsing (Gemini extraction) and 384-dim sentence embeddings.

**Endpoints:**
- \`POST /ml/parse-resume\` — multipart PDF upload, returns structured JSON
- \`POST /ml/generate-embedding\` — JSON text, returns 384-dim normalized vector
- \`GET /health/ready\` — readiness probe
- \`GET /docs\` — OpenAPI UI

**Setup:** Add \`ML_GEMINI_API_KEY\` in Space Settings → Secrets.
MDEOF

echo "==> Uploading to HF Space ${REPO_ID}..."
python3 - <<PYEOF
from huggingface_hub import HfApi
import os

api = HfApi()
deploy_dir = "${DEPLOY_DIR}"

for root, dirs, files in os.walk(deploy_dir):
    # Skip __pycache__
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fname in files:
        local_path = os.path.join(root, fname)
        path_in_repo = os.path.relpath(local_path, deploy_dir)
        api.upload_file(
            path_or_fileobj=local_path,
            path_in_repo=path_in_repo,
            repo_id="${REPO_ID}",
            repo_type="space",
        )
        print(f"  uploaded: {path_in_repo}")

print("Upload complete.")
PYEOF

echo ""
echo "=========================================="
echo "  DEPLOYED to Hugging Face Spaces"
echo "=========================================="
echo ""
echo "  Space:   https://huggingface.co/spaces/${REPO_ID}"
echo "  Service: https://${HF_USERNAME}-${SPACE_NAME}.hf.space"
echo "  API docs:https://${HF_USERNAME}-${SPACE_NAME}.hf.space/docs"
echo ""
echo "  NEXT STEP — add your API key as a Space Secret:"
echo "  https://huggingface.co/spaces/${REPO_ID}/settings"
echo "  Secret name:  ML_GEMINI_API_KEY"
echo "  Secret value: (your Google API key from .env)"
echo ""
echo "  The Space will rebuild (~3-5 min) and then be publicly reachable."
echo "  NOTE: free tier sleeps after 48h idle; first request after sleep takes ~30s."
