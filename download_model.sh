#!/bin/bash
# ⛓ GRAINLINK — Model Download Script
# Run this ONCE on the NAS before building the Docker image.
# Downloads all-MiniLM-L6-v2 into ./model_cache so it can be
# baked into the image without internet access at build time.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_CACHE="$SCRIPT_DIR/model_cache"

echo "⛓ GRAINLINK — Downloading embedding model..."
echo "Target: $MODEL_CACHE"
echo ""

# Fix entropy issue on Synology NAS
if [ -f /dev/urandom ]; then
    echo "→ Boosting entropy pool..."
    # Write to urandom to help fill entropy (safe on Linux)
    dd if=/dev/urandom of=/dev/null bs=1k count=100 2>/dev/null || true
fi

mkdir -p "$MODEL_CACHE"

# Download model using a temporary Docker container
# This avoids needing Python installed on the NAS directly
echo "→ Starting download container..."
docker run --rm \
    -v "$MODEL_CACHE:/cache" \
    -e HF_HOME=/cache \
    -e SENTENCE_TRANSFORMERS_HOME=/cache \
    -e TRANSFORMERS_CACHE=/cache \
    python:3.11-slim \
    bash -c "
        pip install -q sentence-transformers 2>&1 | tail -1
        python -c \"
from sentence_transformers import SentenceTransformer
print('Downloading all-MiniLM-L6-v2 (~90MB)...')
m = SentenceTransformer('all-MiniLM-L6-v2')
print('✅ Model downloaded successfully')
\"
    "

echo ""
echo "✅ Model saved to: $MODEL_CACHE"
echo "   $(du -sh $MODEL_CACHE | cut -f1) downloaded"
echo ""
echo "→ Now run: docker compose up -d --build"
