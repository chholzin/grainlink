# ⛓ GRAINLINK — MCP Memory Server
# Every thought. Every agent. One link.
# Optimised for Synology DS716+ (Intel Celeron N3150, x86_64)
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps – CPU-only torch
COPY requirements.txt .
RUN pip install --no-cache-dir \
    mcp>=1.0.0 \
    sentence-transformers>=2.7.0 \
    numpy>=1.26.0 \
    && pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# Copy pre-downloaded model from host into image
# → Run download script first (see SETUP.md)
COPY model_cache/ /app/model_cache/

COPY server.py .

VOLUME ["/data", "/logs"]

ENV DB_PATH=/data/memory.db \
    LOG_PATH=/logs/memory.log \
    EMBED_MODEL=all-MiniLM-L6-v2 \
    TOP_K=5 \
    TRANSFORMERS_CACHE=/app/model_cache \
    HF_HOME=/app/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

CMD ["python", "server.py"]
