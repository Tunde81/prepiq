#!/bin/bash
# PrepIQ — Backup Script
# Backs up PostgreSQL, MongoDB, and media files to /var/backups/prepiq/
# Usage: bash scripts/backup.sh
# Cron: 0 2 * * * cd /path/to/prepiq && bash scripts/backup.sh >> /var/log/prepiq-backup.log 2>&1

set -euo pipefail

QUIET="${1:-}"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; RESET='\033[0m'
ok()   { [[ "$QUIET" == "--quiet" ]] || echo -e "${GREEN}✓${RESET} $*"; }
info() { [[ "$QUIET" == "--quiet" ]] || echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }

[[ -f "docker-compose.yml" ]] || { echo "Run from prepiq/ project root"; exit 1; }

# Load .env
set -a; source .env; set +a

BACKUP_DIR="/var/backups/prepiq"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/$TIMESTAMP"

sudo mkdir -p "$DEST"
sudo chown "$USER:$USER" "$DEST"

info "Starting backup → $DEST"

# ─── POSTGRESQL ───────────────────────────────────────────────────────────────
info "Backing up PostgreSQL..."
docker compose exec -T db pg_dump \
  -U "${POSTGRES_USER:-prepiq}" \
  -d "${POSTGRES_DB:-prepiq}" \
  --no-owner \
  --clean \
  | gzip > "$DEST/postgres_$TIMESTAMP.sql.gz"
ok "PostgreSQL dump: $(du -sh "$DEST/postgres_$TIMESTAMP.sql.gz" | cut -f1)"

# ─── MONGODB ──────────────────────────────────────────────────────────────────
info "Backing up MongoDB..."
docker compose exec -T mongo mongodump \
  --uri="${MONGO_URL:-mongodb://prepiq:changeme@localhost:27017/prepiq_events?authSource=admin}" \
  --archive \
  --gzip 2>/dev/null > "$DEST/mongo_$TIMESTAMP.archive.gz" || warn "MongoDB backup failed — skipping"

if [[ -s "$DEST/mongo_$TIMESTAMP.archive.gz" ]]; then
  ok "MongoDB dump: $(du -sh "$DEST/mongo_$TIMESTAMP.archive.gz" | cut -f1)"
fi

# ─── MEDIA FILES ──────────────────────────────────────────────────────────────
if [[ -d "backend/media" ]] && [[ -n "$(ls -A backend/media 2>/dev/null)" ]]; then
  info "Backing up media files..."
  tar -czf "$DEST/media_$TIMESTAMP.tar.gz" backend/media/ 2>/dev/null
  ok "Media: $(du -sh "$DEST/media_$TIMESTAMP.tar.gz" | cut -f1)"
fi

# ─── ENV FILE ─────────────────────────────────────────────────────────────────
cp .env "$DEST/env_$TIMESTAMP.bak"
ok ".env backed up"

# ─── PRUNE OLD BACKUPS (keep last 14 days) ────────────────────────────────────
info "Pruning backups older than 14 days..."
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +14 -exec rm -rf {} + 2>/dev/null || true
ok "Old backups pruned"

# ─── SUMMARY ──────────────────────────────────────────────────────────────────
TOTAL=$(du -sh "$DEST" | cut -f1)
echo ""
ok "Backup complete → $DEST ($TOTAL)"
echo "  Restore Postgres: bash scripts/restore.sh postgres $DEST/postgres_$TIMESTAMP.sql.gz"
echo "  Restore MongoDB:  bash scripts/restore.sh mongo $DEST/mongo_$TIMESTAMP.archive.gz"
echo ""
