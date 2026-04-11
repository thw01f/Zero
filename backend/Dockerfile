# Build context: darklead/ (repo root)
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python deps + binaries
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
