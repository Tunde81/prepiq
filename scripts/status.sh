#!/bin/bash
# PrepIQ — Status & Health Check
# Usage: bash scripts/status.sh
# Shows live status of all services, disk, memory, and recent errors

set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

[[ -f "docker-compose.yml" ]] || { echo "Run from prepiq/ project root"; exit 1; }
set -a; source .env 2>/dev/null || true; set +a

echo ""
echo -e "${BOLD}PrepIQ — Platform Status${RESET}"
echo -e "$(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── CONTAINER STATUS ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Containers:${RESET}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | while IFS= read -r line; do
  if echo "$line" | grep -q "running"; then
    echo -e "  ${GREEN}$line${RESET}"
  elif echo "$line" | grep -q "Name"; then
    echo -e "  ${BOLD}$line${RESET}"
  else
    echo -e "  ${RED}$line${RESET}"
  fi
done

# ─── API HEALTH ───────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}API Health:${RESET}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health 2>/dev/null || echo "000")
RESPONSE=$(curl -s http://localhost/api/health 2>/dev/null || echo "{}")
if [[ "$HTTP_CODE" == "200" ]]; then
  echo -e "  ${GREEN}✓${RESET} HTTP $HTTP_CODE — $RESPONSE"
else
  echo -e "  ${RED}✗${RESET} HTTP $HTTP_CODE — API may be down"
fi

# ─── DATABASE CONNECTIVITY ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Database Connectivity:${RESET}"

# PostgreSQL
if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-prepiq}" -q 2>/dev/null; then
  USER_COUNT=$(docker compose exec -T db psql -U "${POSTGRES_USER:-prepiq}" -d "${POSTGRES_DB:-prepiq}" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' \n' || echo "?")
  ASSESS_COUNT=$(docker compose exec -T db psql -U "${POSTGRES_USER:-prepiq}" -d "${POSTGRES_DB:-prepiq}" -t -c "SELECT COUNT(*) FROM risk_assessments;" 2>/dev/null | tr -d ' \n' || echo "?")
  echo -e "  ${GREEN}✓${RESET} PostgreSQL — Users: $USER_COUNT | Assessments: $ASSESS_COUNT"
else
  echo -e "  ${RED}✗${RESET} PostgreSQL — not responding"
fi

# Redis
if docker compose exec -T redis redis-cli -a "${REDIS_PASSWORD:-changeme}" ping 2>/dev/null | grep -q PONG; then
  echo -e "  ${GREEN}✓${RESET} Redis — responding"
else
  echo -e "  ${RED}✗${RESET} Redis — not responding"
fi

# MongoDB
if docker compose exec -T mongo mongosh --eval "db.adminCommand('ping')" --quiet 2>/dev/null | grep -q "ok"; then
  EVENT_COUNT=$(docker compose exec -T mongo mongosh prepiq_events --quiet --eval "db.user_events.countDocuments()" 2>/dev/null | tail -1 || echo "?")
  echo -e "  ${GREEN}✓${RESET} MongoDB — Events logged: $EVENT_COUNT"
else
  echo -e "  ${YELLOW}⚠${RESET}  MongoDB — not responding (non-critical)"
fi

# ─── SYSTEM RESOURCES ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}System Resources:${RESET}"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')
MEM_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
MEM_USED=$(free -h | awk '/^Mem:/ {print $3}')
UPTIME=$(uptime -p 2>/dev/null || uptime | sed 's/.*up /up /' | cut -d, -f1-2)
echo "  Disk:    $DISK_USAGE"
echo "  Memory:  $MEM_USED / $MEM_TOTAL"
echo "  Uptime:  $UPTIME"

# ─── DOCKER RESOURCE USAGE ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Container Resource Usage:${RESET}"
docker stats --no-stream --format "  {{.Name}}\t CPU: {{.CPUPerc}}\t MEM: {{.MemUsage}}" 2>/dev/null \
  | grep prepiq || echo "  (run docker stats for live view)"

# ─── RECENT ERRORS ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Recent Backend Errors (last 20 lines):${RESET}"
docker compose logs --tail=20 backend 2>/dev/null | grep -i "error\|exception\|traceback" | tail -5 \
  | sed "s/^/  ${RED}/" | sed "s/$/${RESET}/" \
  || echo "  No recent errors found"

# ─── SSL EXPIRY ───────────────────────────────────────────────────────────────
if [[ -f "nginx/ssl/fullchain.pem" ]]; then
  echo ""
  echo -e "${BOLD}SSL Certificate:${RESET}"
  EXPIRY=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem 2>/dev/null | cut -d= -f2 || echo "unknown")
  DAYS_LEFT=$(openssl x509 -enddate -noout -in nginx/ssl/fullchain.pem 2>/dev/null \
    | cut -d= -f2 | xargs -I{} date -d "{}" +%s \
    | xargs -I{} bash -c 'echo $(( ($1 - $(date +%s)) / 86400 ))' _ {} 2>/dev/null || echo "?")
  if [[ "$DAYS_LEFT" =~ ^[0-9]+$ ]] && (( DAYS_LEFT < 14 )); then
    echo -e "  ${RED}⚠ Expires: $EXPIRY ($DAYS_LEFT days — RENEW SOON)${RESET}"
  else
    echo -e "  ${GREEN}✓${RESET} Expires: $EXPIRY ($DAYS_LEFT days remaining)"
  fi
fi

# ─── BACKUP STATUS ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Last Backup:${RESET}"
LATEST_BACKUP=$(ls -td /var/backups/prepiq/*/ 2>/dev/null | head -1 || echo "")
if [[ -n "$LATEST_BACKUP" ]]; then
  BACKUP_DATE=$(stat -c %y "$LATEST_BACKUP" 2>/dev/null | cut -d. -f1 || echo "unknown")
  BACKUP_SIZE=$(du -sh "$LATEST_BACKUP" 2>/dev/null | cut -f1 || echo "?")
  echo -e "  ${GREEN}✓${RESET} $LATEST_BACKUP ($BACKUP_SIZE) — $BACKUP_DATE"
else
  echo -e "  ${YELLOW}⚠${RESET}  No backups found — run: bash scripts/backup.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
