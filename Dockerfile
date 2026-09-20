FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini .
COPY csvfiles ./csvfiles
COPY sih_bis.d[b] ./

# Ingest and validate if database is not present
RUN if [ ! -f sih_bis.db ]; then \
      alembic upgrade head && \
      python -m scripts.ingest --data-dir csvfiles && \
      python scripts/validate_ingestion.py; \
    fi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; p = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health', timeout=3)" || exit 1

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

