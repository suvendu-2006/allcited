#!/usr/bin/env bash
# Push the api/ code + Space metadata to the Hugging Face Space.
# One-time setup:
#   pip install -U "huggingface_hub[cli]" && huggingface-cli login
#   export SPACE_URL=https://huggingface.co/spaces/<YOUR_USER>/allcited
# Then:  bash deploy.sh
set -euo pipefail
cd "$(dirname "$0")"

: "${SPACE_URL:?Set SPACE_URL=https://huggingface.co/spaces/<user>/allcited}"

STAMP=$(date -u +%F-%H%M)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Assemble the Space repo: api code + Space metadata at root
rsync -a --exclude '.venv' --exclude '__pycache__' --exclude '.pytest_cache' ../api/ "$TMP/"
cp README.md Dockerfile "$TMP/"

cd "$TMP"
git init -q
git add -A
git -c user.email=deploy@allcited.local -c user.name="allcited-deploy" commit -qm "deploy ${STAMP}"
git remote add space "$SPACE_URL" 2>/dev/null || git remote set-url space "$SPACE_URL"
git push -f space main
echo "✅ pushed ${STAMP} — Space builds at: ${SPACE_URL}"
