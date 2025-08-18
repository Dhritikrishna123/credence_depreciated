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

# Copy source
COPY credence /app/credence

EXPOSE 8000

CMD ["uvicorn", "credence.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


