#!/bin/bash
# DarkLead — Digital Ocean deployment script
# Usage: ./deploy.sh [--fresh]
# Run as root on the droplet (Ubuntu 22.04 LTS recommended, 4GB+ RAM)
set -euo pipefail

DOMAIN="zero.darklead.org"
REPO="https://github.com/thw01f/TR-104-DarkLead.git"
APP_DIR="/opt/darklead"
EMAIL="gowthamangs.1cs@gmail.com"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 1. System dependencies ────────────────────────────────────────────────────
info "Installing system dependencies…"
apt-get update -qq
apt-get install -y -qq docker.io docker-compose-v2 git curl certbot nginx

systemctl enable --now docker
usermod -aG docker "$USER" || true

# ── 2. Clone or update repo ───────────────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
  info "Updating existing repo…"
  git -C "$APP_DIR" pull origin main
else
  info "Cloning repo…"
  git clone "$REPO" "$APP_DIR"
fi

cd "$APP_DIR"

# ── 3. .env.prod setup ────────────────────────────────────────────────────────
if [ ! -f ".env.prod" ]; then
  cp deploy/.env.prod.example .env.prod
  warn ".env.prod created from example — edit $APP_DIR/.env.prod with real API keys!"
  warn "Then re-run this script."
  exit 0
fi

# ── 4. SSL certificate (Let's Encrypt) ───────────────────────────────────────
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  info "Obtaining SSL certificate for $DOMAIN…"
  systemctl stop nginx 2>/dev/null || true
  certbot certonly --standalone \
    --non-interactive --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN"
fi

# ── 5. Build and start containers ────────────────────────────────────────────
info "Building Docker image (this takes ~3-5 min first time)…"
docker compose -f deploy/docker-compose.prod.yml build --no-cache

info "Starting services…"
docker compose -f deploy/docker-compose.prod.yml up -d

# ── 6. Health check ───────────────────────────────────────────────────────────
info "Waiting for health check…"
for i in $(seq 1 24); do
  sleep 5
  if curl -sf "http://localhost:7860/health" > /dev/null 2>&1; then
    info "✓ App is healthy"
    break
  fi
  echo -n "."
  if [ $i -eq 24 ]; then
    error "App did not become healthy after 2 min — check: docker compose -f deploy/docker-compose.prod.yml logs"
  fi
done

# ── 7. Firewall ───────────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
fi

info ""
info "✅  DarkLead deployed!"
info "    https://$DOMAIN"
info ""
info "Useful commands:"
info "  docker compose -f $APP_DIR/deploy/docker-compose.prod.yml logs -f"
info "  docker compose -f $APP_DIR/deploy/docker-compose.prod.yml restart darklead"
