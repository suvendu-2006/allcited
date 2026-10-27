# Allcited API — Hugging Face Space (Docker)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/tmp/hf_cache \
    HF_HUB_ENABLE_HF_TRANSFER=0

# OCR runtime (eng + hin) + build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-hin curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

# CPU-only torch first (keeps the image ~1.5GB instead of ~4GB CUDA)
COPY requirements.txt /tmp/torch.txt
RUN grep -iE "^torch" /tmp/torch.txt || echo "torch>=2.2" > /tmp/torch.txt; \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
      $(grep -iE "^torch" /tmp/torch.txt || echo "torch>=2.2")

COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

# Pre-cache SentenceTransformer and CrossEncoder models during build
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY app /srv/app

RUN useradd -u 1000 -m -s /bin/bash appuser && \
    mkdir -p /srv/app /tmp/hf_cache && \
    chown -R appuser:appuser /srv /srv/app /home/appuser /tmp/hf_cache

USER appuser

# HF Docker Spaces route traffic to app_port (8000); bind 0.0.0.0
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s \
  CMD curl -sf http://127.0.0.1:8000/v1/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
