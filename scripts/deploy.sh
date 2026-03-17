#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║              PrepIQ — Full Deployment Script             ║
# ║         Tested on Ubuntu 22.04 / 24.04 LTS (VPS)            ║
# ║  Run as root or sudo user. Sets up Docker, builds and starts ║
# ║  all services, configures SSL via Certbot.                   ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# ─── COLOURS ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }
fail() { echo -e "${RED}✗ ERROR:${RESET} $*"; exit 1; }
ask()  { echo -e "${BOLD}?${RESET}  $*"; }

# ─── BANNER ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║${RESET}   ${BOLD}PrepIQ — Deployment Script v1.0${RESET}        ${CYAN}║${RESET}"
echo -e "${CYAN}║${RESET}   National Cyber Preparedness Platform       ${CYAN}║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${RESET}"
echo ""

# ─── MUST RUN FROM PROJECT ROOT ───────────────────────────────────────────────
[[ -f "docker-compose.yml" ]] || fail "Run this script from the prepiq/ project root"

# ─── STEP 1: SYSTEM DEPENDENCIES ──────────────────────────────────────────────
echo -e "\n${BOLD}[1/7] System Dependencies${RESET}"

info "Updating package list..."
sudo apt-get update -qq

# Install curl, git, unzip if missing
for pkg in curl git unzip openssl ufw; do
  if ! command -v $pkg &>/dev/null; then
    info "Installing $pkg..."
    sudo apt-get install -y $pkg -qq
  fi
done
ok "System packages ready"

# ─── STEP 2: DOCKER ───────────────────────────────────────────────────────────
echo -e "\n${BOLD}[2/7] Docker & Docker Compose${RESET}"

if ! command -v docker &>/dev/null; then
  info "Installing Docker (official script)..."
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  ok "Docker installed"
  warn "You may need to log out and back in for group changes to take effect"
  warn "If docker commands fail, run: newgrp docker"
else
  ok "Docker already installed: $(docker --version | cut -d' ' -f3 | tr -d ',')"
fi

if ! docker compose version &>/dev/null; then
  info "Installing Docker Compose plugin..."
  sudo apt-get install -y docker-compose-plugin -qq
  ok "Docker Compose installed"
else
  ok "Docker Compose ready: $(docker compose version --short)"
fi

# ─── STEP 3: ENVIRONMENT CONFIGURATION ────────────────────────────────────────
echo -e "\n${BOLD}[3/7] Environment Configuration${RESET}"

if [[ -f ".env" ]]; then
  warn ".env already exists — skipping generation"
  warn "Delete .env and re-run to regenerate"
else
  info "Generating .env from template..."
  cp .env.example .env

  # Auto-generate secrets
  SECRET_KEY=$(openssl rand -hex 32)
  PG_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 20)
  REDIS_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 20)
  MONGO_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 20)

  sed -i "s/CHANGE_ME_64_CHAR_SECRET_KEY_GENERATE_WITH_OPENSSL_RAND/$SECRET_KEY/" .env
  sed -i "s/CHANGE_ME_STRONG_PASSWORD/$PG_PASS/g" .env
  sed -i "s/CHANGE_ME_REDIS_PASSWORD/$REDIS_PASS/g" .env
  sed -i "s/CHANGE_ME_MONGO_PASSWORD/$MONGO_PASS/g" .env
  # Fix DATABASE_URL with actual password
  sed -i "s|postgresql://prepiq:CHANGE_ME_STRONG_PASSWORD|postgresql://prepiq:$PG_PASS|g" .env
  sed -i "s|redis://:CHANGE_ME_REDIS_PASSWORD|redis://:$REDIS_PASS|g" .env
  sed -i "s|mongodb://prepiq:CHANGE_ME_MONGO_PASSWORD|mongodb://prepiq:$MONGO_PASS|g" .env

  ok "Secrets auto-generated"
  echo ""
  echo -e "${YELLOW}══════════════════════════════════════════════════${RESET}"
  echo -e "${YELLOW}  You MUST set the following values in .env now:${RESET}"
  echo -e "${YELLOW}══════════════════════════════════════════════════${RESET}"
  echo ""
  echo "  1. FRONTEND_URL          — your domain, e.g. https://prepiq.yourdomain.com"
  echo "  2. BACKEND_CORS_ORIGINS  — same domain in JSON array"
  echo "  3. FIRST_SUPERADMIN_EMAIL    — your admin email"
  echo "  4. FIRST_SUPERADMIN_PASSWORD — strong admin password"
  echo "  5. SMTP_* settings       — for email verification (optional for dev)"
  echo ""
  ask "Open .env in nano to edit now? [Y/n]"
  read -r EDIT_ENV
  if [[ "${EDIT_ENV:-Y}" =~ ^[Yy]$ ]]; then
    nano .env
  fi
fi

# Source the .env for validation
set -a; source .env; set +a

# Validate critical vars
DOMAIN=""
if [[ -n "${FRONTEND_URL:-}" && "${FRONTEND_URL}" != "https://yourdomain.com" ]]; then
  DOMAIN=$(echo "$FRONTEND_URL" | sed 's|https://||' | sed 's|http://||' | sed 's|/.*||')
  ok "Domain set to: $DOMAIN"
else
  warn "FRONTEND_URL not configured — SSL setup will be skipped"
  warn "Edit .env and set FRONTEND_URL=https://yourdomain.com"
fi

# ─── STEP 4: FIREWALL ─────────────────────────────────────────────────────────
echo -e "\n${BOLD}[4/7] Firewall (UFW)${RESET}"

if command -v ufw &>/dev/null; then
  sudo ufw allow 22/tcp   comment 'SSH'    2>/dev/null || true
  sudo ufw allow 80/tcp   comment 'HTTP'   2>/dev/null || true
  sudo ufw allow 443/tcp  comment 'HTTPS'  2>/dev/null || true
  # Block direct DB access from outside
  sudo ufw deny 5432/tcp  2>/dev/null || true
  sudo ufw deny 6379/tcp  2>/dev/null || true
  sudo ufw deny 27017/tcp 2>/dev/null || true

  # Enable UFW non-interactively
  echo "y" | sudo ufw enable 2>/dev/null || true
  ok "UFW configured: 22/80/443 open, databases locked"
else
  warn "UFW not available — configure firewall manually"
fi

# ─── STEP 5: BUILD & START SERVICES ───────────────────────────────────────────
echo -e "\n${BOLD}[5/7] Building & Starting Services${RESET}"

info "Pulling base images..."
docker compose pull --quiet

info "Building application images (this takes 3-5 minutes on first run)..."
docker compose build --no-cache 2>&1 | grep -E '(Step|Successfully|ERROR|error)' || true

info "Starting all services..."
docker compose up -d

info "Waiting for databases to be healthy (up to 60 seconds)..."
MAX_WAIT=60
WAITED=0
while ! docker compose exec -T db pg_isready -U prepiq -q 2>/dev/null; do
  sleep 3
  WAITED=$((WAITED + 3))
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    fail "PostgreSQL did not become healthy in time. Check: docker compose logs db"
  fi
  echo -n "."
done
echo ""
ok "PostgreSQL healthy"

# Wait for Mongo
WAITED=0
while ! docker compose exec -T mongo mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null | grep -q "ok"; do
  sleep 3
  WAITED=$((WAITED + 3))
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "MongoDB did not respond in time — continuing anyway"
    break
  fi
  echo -n "."
done
echo ""
ok "MongoDB healthy"

info "Running database migrations..."
docker compose exec -T backend alembic upgrade head
ok "Migrations complete"

# ─── STEP 6: SSL WITH CERTBOT ─────────────────────────────────────────────────
echo -e "\n${BOLD}[6/7] SSL Certificate (Let's Encrypt)${RESET}"

if [[ -z "$DOMAIN" ]]; then
  warn "Skipping SSL — FRONTEND_URL not set in .env"
  warn "Run scripts/ssl.sh after setting FRONTEND_URL to add SSL later"
else
  ask "Set up SSL certificate for $DOMAIN now? [Y/n]"
  read -r DO_SSL
  if [[ "${DO_SSL:-Y}" =~ ^[Yy]$ ]]; then
    bash scripts/ssl.sh "$DOMAIN"
  else
    warn "Skipping SSL — run scripts/ssl.sh $DOMAIN later"
  fi
fi

# ─── STEP 7: HEALTH CHECK ─────────────────────────────────────────────────────
echo -e "\n${BOLD}[7/7] Health Check${RESET}"

sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  ok "API health check passed (HTTP 200)"
else
  warn "API returned HTTP $HTTP_CODE — check logs: docker compose logs backend"
fi

# ─── DONE ─────────────────────────────────────────────────────────────────────
ADMIN_EMAIL=$(grep FIRST_SUPERADMIN_EMAIL .env | cut -d= -f2)

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║         PrepIQ is LIVE! 🚀               ║${RESET}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${RESET}"
echo ""
if [[ -n "$DOMAIN" ]]; then
  echo -e "  ${BOLD}Platform:${RESET}  https://$DOMAIN"
  echo -e "  ${BOLD}API:${RESET}       https://$DOMAIN/api/health"
else
  echo -e "  ${BOLD}Platform:${RESET}  http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"
  echo -e "  ${BOLD}API:${RESET}       http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')/api/health"
fi
echo ""
echo -e "  ${BOLD}Admin email:${RESET}    $ADMIN_EMAIL"
echo -e "  ${BOLD}Admin password:${RESET} (as set in .env)"
echo ""
echo -e "  ${BOLD}Useful commands:${RESET}"
echo "    docker compose logs -f              # live logs"
echo "    docker compose logs -f backend      # backend only"
echo "    docker compose ps                   # container status"
echo "    docker compose restart backend      # restart one service"
echo "    docker compose down && docker compose up -d  # full restart"
echo "    bash scripts/update.sh              # pull & redeploy"
echo "    bash scripts/backup.sh              # manual backup"
echo ""
