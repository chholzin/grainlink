# ⛓ GRAINLINK — MCP Memory Server
# Every thought. Every agent. One link.
# Optimised for Synology DS716+ (Intel Celeron N3150, x86_64)
FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps – CPU-only torch keeps image size manageable (~1.5GB)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    mcp>=1.0.0 \
    sentence-transformers>=2.7.0 \
    numpy>=1.26.0 \
    && pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

# Pre-download the embedding model into the image
# so first start doesn't need internet access
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY server.py .

# Volumes for persistent data & logs
VOLUME ["/data", "/logs"]

ENV DB_PATH=/data/memory.db \
    LOG_PATH=/logs/memory.log \
    EMBED_MODEL=all-MiniLM-L6-v2 \
    TOP_K=5

# MCP servers communicate over stdio – no exposed port needed
CMD ["python", "server.py"]
