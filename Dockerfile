# ⛓ GRAINLINK — MCP Memory Server
# Every thought. Every agent. One link.
# Optimised for Synology DS716+ (Intel Celeron N3150, x86_64)
#
# ✅ Uses onnxruntime instead of PyTorch
#    Image: ~300MB instead of ~1.8GB
#    Start: ~1s instead of ~20s

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download ONNX model directly from HuggingFace at build time
# optimum/all-MiniLM-L6-v2 is the official ONNX export of the model
ENV HF_HOME=/app/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache

RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download( \
    repo_id='sentence-transformers/all-MiniLM-L6-v2', \
    local_dir='/app/model_cache/all-MiniLM-L6-v2', \
    allow_patterns=['tokenizer.json','tokenizer_config.json','onnx/model.onnx','onnx/model_quantized.onnx'] \
); \
print('ONNX model baked into image')"

COPY server.py .

VOLUME ["/data", "/logs"]

ENV DB_PATH=/data/memory.db \
    LOG_PATH=/logs/memory.log \
    EMBED_MODEL=all-MiniLM-L6-v2 \
    TOP_K=5 \
    HF_HOME=/app/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache \
    HF_HUB_OFFLINE=1

CMD ["python", "server.py"]
