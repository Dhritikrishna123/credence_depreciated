FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install project deps
COPY pyproject.toml README.md /app/
RUN pip install --upgrade pip && pip install .

# Copy source and runtime assets (alembic, config example, entrypoint)
COPY credence /app/credence
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY config/config.example.yaml /app/config/config.yaml
COPY docker/entrypoint.py /app/entrypoint.py

EXPOSE 8000

# Default to API; compose can override to "worker"
CMD ["python", "/app/entrypoint.py", "api"]


