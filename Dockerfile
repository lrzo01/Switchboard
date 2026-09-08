FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY config.toml .
COPY schemas/ ./schemas/
COPY data/ ./data/
COPY src/ ./src/

RUN pip install --no-cache-dir .

CMD ["switchboard"]
