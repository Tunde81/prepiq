#!/bin/bash
# PrepIQ — Restore Script
# Usage:
#   bash scripts/restore.sh postgres /var/backups/prepiq/20250101_020000/postgres_20250101_020000.sql.gz
#   bash scripts/restore.sh mongo    /var/backups/prepiq/20250101_020000/mongo_20250101_020000.archive.gz

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
fail() { echo -e "${RED}✗ ERROR:${RESET} $*"; exit 1; }

TYPE="${1:-}"
FILE="${2:-}"

[[ -z "$TYPE" || -z "$FILE" ]] && fail "Usage: bash scripts/restore.sh [postgres|mongo] /path/to/backup"
[[ -f "$FILE" ]] || fail "Backup file not found: $FILE"
[[ -f "docker-compose.yml" ]] || fail "Run from prepiq/ project root"

set -a; source .env; set +a

echo ""
echo -e "${YELLOW}⚠  WARNING: This will overwrite current data. Continue? [y/N]${RESET}"
read -r CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

case "$TYPE" in
  postgres)
    info "Restoring PostgreSQL from $FILE..."
    zcat "$FILE" | docker compose exec -T db psql \
      -U "${POSTGRES_USER:-prepiq}" \
      -d "${POSTGRES_DB:-prepiq}" \
      --quiet 2>/dev/null
    ok "PostgreSQL restored"
    ;;

  mongo)
    info "Restoring MongoDB from $FILE..."
    cat "$FILE" | docker compose exec -T mongo mongorestore \
      --uri="${MONGO_URL}" \
      --archive \
      --gzip \
      --drop 2>/dev/null
    ok "MongoDB restored"
    ;;

  *)
    fail "Unknown type '$TYPE'. Use: postgres or mongo"
    ;;
esac

echo ""
ok "Restore complete — restart services if needed: docker compose restart"
echo ""
