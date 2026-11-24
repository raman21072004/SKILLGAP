FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 DATA_DIR=/app/data
WORKDIR /app/backend

# CPU-only PyTorch keeps the image ~2 GB smaller than the CUDA build
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install -r requirements.txt -r requirements-ml.txt

COPY data /app/data
COPY backend /app/backend

# Bake NLTK data and the sentence-transformer into the image (needs internet at build time).
ARG DOWNLOAD_MODELS=true
RUN if [ "$DOWNLOAD_MODELS" = "true" ]; then python scripts/download_models.py --skip-spacy; fi

RUN useradd --create-home appuser && mkdir -p /app/backend/var && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 30"]
