# HF Spaces root Dockerfile — build context is this directory (darklead/)
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python deps + scanner binaries
FROM python:3.11-slim AS py-builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget tar gzip build-essential libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Gitleaks
RUN wget -q https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz \
    && tar xzf gitleaks_8.18.4_linux_x64.tar.gz -C /usr/local/bin/ gitleaks \
    && rm gitleaks_8.18.4_linux_x64.tar.gz

# Install Trivy
RUN wget -q https://github.com/aquasecurity/trivy/releases/download/v0.55.0/trivy_0.55.0_Linux-64bit.tar.gz \
    && tar xzf trivy_0.55.0_Linux-64bit.tar.gz -C /usr/local/bin/ trivy \
    && rm trivy_0.55.0_Linux-64bit.tar.gz

# Install Hadolint
RUN wget -q https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 \
    -O /usr/local/bin/hadolint && chmod +x /usr/local/bin/hadolint

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Final runtime
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl supervisor redis-server \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=py-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=py-builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=py-builder /usr/local/bin/celery /usr/local/bin/celery
COPY --from=py-builder /usr/local/bin/gitleaks /usr/local/bin/gitleaks
COPY --from=py-builder /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=py-builder /usr/local/bin/hadolint /usr/local/bin/hadolint

COPY backend/ /app/backend/
COPY backend/supervisord.conf /etc/supervisor/conf.d/darklead.conf
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

RUN mkdir -p /data /tmp/darklead_clones

EXPOSE 7860

ENV DATABASE_URL=sqlite:////data/darklead.db
ENV REDIS_URL=redis://localhost:6379/0
ENV PYTHONPATH=/app/backend

# HF Spaces requires non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data /tmp/darklead_clones
USER appuser

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/darklead.conf"]
