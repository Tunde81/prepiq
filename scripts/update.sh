#!/bin/bash
# PrepIQ — Update & Redeploy Script
# Usage: bash scripts/update.sh
# Rebuilds changed images, runs migrations, restarts services with zero-downtime approach

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }

[[ -f "docker-compose.yml" ]] || { echo "Run from prepiq/ project root"; exit 1; }

echo ""
echo -e "${BOLD}PrepIQ — Update${RESET}"
echo -e "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Backup before update
info "Running pre-update backup..."
bash scripts/backup.sh --quiet 2>/dev/null || warn "Backup skipped (run scripts/backup.sh manually)"

# Pull latest code if inside a git repo
if [[ -d ".git" ]]; then
  info "Pulling latest code..."
  git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || warn "git pull failed — continuing with local files"
  ok "Code updated"
fi

# Rebuild only changed images
info "Rebuilding application images..."
docker compose build backend frontend

# Apply any new migrations before restarting
info "Applying database migrations..."
docker compose run --rm backend alembic upgrade head
ok "Migrations applied"

# Restart services gracefully (keep DB/Redis/Mongo running)
info "Restarting application services..."
docker compose up -d --no-deps backend frontend nginx
ok "Services restarted"

sleep 5

# Health check
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
  ok "Health check passed (HTTP 200)"
else
  warn "Health check returned HTTP $HTTP_CODE"
  warn "Check logs: docker compose logs backend"
fi

echo ""
ok "Update complete — $(date '+%H:%M:%S')"
echo ""
