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
COPY app-requirements.txt /tmp/torch.txt
RUN grep -iE "^torch" /tmp/torch.txt || echo "torch>=2.2" > /tmp/torch.txt; \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
      $(grep -iE "^torch" /tmp/torch.txt || echo "torch>=2.2")

COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

COPY app /srv/app

# HF Docker Spaces route traffic to app_port (8000); bind 0.0.0.0
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s \
  CMD curl -sf http://127.0.0.1:8000/v1/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
