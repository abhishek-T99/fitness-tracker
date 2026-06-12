FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps: curl for healthcheck, build-essential for any source builds.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first to maximize layer caching.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Then copy the source.
COPY . .

# Install entrypoint at /usr/local/bin so the docker-compose bind mount over /app
# can't shadow it. Strip CRLF first in case the file shipped from a Windows host.
RUN cp entrypoint.sh /usr/local/bin/entrypoint.sh \
 && sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
 && chmod +x /usr/local/bin/entrypoint.sh

# Non-root user is good hygiene; SQLite + media live under /app and we own it.
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command: web server. Compose overrides this for worker / beat.
CMD ["bash", "/usr/local/bin/entrypoint.sh", "web"]
