#!/bin/bash
# PrepIQ — Install Cron Jobs
# Usage: bash scripts/install-crons.sh
# Sets up: daily backup at 2am, SSL renewal check at 3am

set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }

[[ -f "docker-compose.yml" ]] || { echo "Run from prepiq/ project root"; exit 1; }

PROJECT_DIR=$(pwd)
DOMAIN=$(grep FRONTEND_URL .env 2>/dev/null | cut -d= -f2 | sed 's|https://||' | sed 's|http://||' | sed 's|/.*||' || echo "")

info "Installing PrepIQ cron jobs..."

# Remove any existing PrepIQ cron entries
(crontab -l 2>/dev/null | grep -v '# PrepIQ') | crontab - 2>/dev/null || true

# Build new crontab
CRON_ENTRIES=$(crontab -l 2>/dev/null || true)
CRON_ENTRIES+="
# PrepIQ — Daily backup at 2:00am
0 2 * * * cd $PROJECT_DIR && bash scripts/backup.sh --quiet >> /var/log/prepiq-backup.log 2>&1

# PrepIQ — Weekly status report (Mondays 8am)
0 8 * * 1 cd $PROJECT_DIR && bash scripts/status.sh >> /var/log/prepiq-status.log 2>&1
"

if [[ -n "$DOMAIN" ]]; then
  CRON_ENTRIES+="
# PrepIQ — SSL renewal check at 3:00am
0 3 * * * certbot renew --quiet --standalone --pre-hook \"cd $PROJECT_DIR && docker compose stop nginx\" --post-hook \"cd $PROJECT_DIR && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/ && docker compose start nginx\" >> /var/log/prepiq-ssl-renew.log 2>&1
"
fi

echo "$CRON_ENTRIES" | crontab -

ok "Cron jobs installed:"
echo "  02:00 daily  — Database backup → /var/backups/prepiq/"
echo "  08:00 Mon    — Status report   → /var/log/prepiq-status.log"
[[ -n "$DOMAIN" ]] && echo "  03:00 daily  — SSL renewal check"
echo ""
info "View cron log: tail -f /var/log/prepiq-backup.log"
echo ""
