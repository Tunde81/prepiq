#!/bin/bash
# PrepIQ SSL Setup
# Usage: bash scripts/ssl.sh yourdomain.com
# Installs certbot, obtains certificate, rewrites nginx config for HTTPS

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
info() { echo -e "${CYAN}→${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET}  $*"; }
fail() { echo -e "${RED}✗ ERROR:${RESET} $*"; exit 1; }

DOMAIN="${1:-}"
[[ -z "$DOMAIN" ]] && fail "Usage: bash scripts/ssl.sh yourdomain.com"

echo ""
echo -e "${BOLD}PrepIQ SSL Setup — $DOMAIN${RESET}"
echo ""

# ─── CHECK DNS ────────────────────────────────────────────────────────────────
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "")
DNS_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -1 || nslookup "$DOMAIN" 2>/dev/null | awk '/Address: /{print $2}' | tail -1 || echo "")

if [[ -n "$SERVER_IP" && -n "$DNS_IP" && "$SERVER_IP" != "$DNS_IP" ]]; then
  warn "DNS mismatch detected:"
  warn "  Server IP:  $SERVER_IP"
  warn "  $DOMAIN resolves to: $DNS_IP"
  warn "  SSL will fail if DNS doesn't point to this server"
  echo ""
  read -p "Continue anyway? [y/N] " -r
  [[ "$REPLY" =~ ^[Yy]$ ]] || exit 0
else
  ok "DNS looks correct ($DOMAIN → $SERVER_IP)"
fi

# ─── INSTALL CERTBOT ──────────────────────────────────────────────────────────
info "Installing Certbot..."
if ! command -v certbot &>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y certbot -qq
  ok "Certbot installed"
else
  ok "Certbot already installed"
fi

# ─── TEMPORARILY STOP NGINX TO FREE PORT 80 ───────────────────────────────────
info "Temporarily stopping Nginx to free port 80 for certificate issuance..."
docker compose stop nginx 2>/dev/null || true
sleep 2

# ─── OBTAIN CERTIFICATE ───────────────────────────────────────────────────────
info "Obtaining Let's Encrypt certificate for $DOMAIN..."
EMAIL=$(grep FIRST_SUPERADMIN_EMAIL .env 2>/dev/null | cut -d= -f2 || echo "admin@$DOMAIN")

sudo certbot certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  --domains "$DOMAIN" \
  --keep-until-expiring

ok "Certificate obtained: /etc/letsencrypt/live/$DOMAIN/"

# ─── COPY CERTS INTO PROJECT ──────────────────────────────────────────────────
info "Copying certificates into nginx/ssl/..."
mkdir -p nginx/ssl
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" nginx/ssl/
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" nginx/ssl/
sudo chown "$USER:$USER" nginx/ssl/*.pem
chmod 600 nginx/ssl/privkey.pem
ok "Certificates copied to nginx/ssl/"

# ─── WRITE HTTPS NGINX CONFIG ─────────────────────────────────────────────────
info "Writing HTTPS Nginx configuration..."
cat > nginx/nginx.conf << NGINXEOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    limit_req_zone \$binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone \$binary_remote_addr zone=auth:10m rate=10r/m;

    upstream backend  { server backend:8000; }
    upstream frontend { server frontend:80; }

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name $DOMAIN;
        return 301 https://\$host\$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl;
        server_name $DOMAIN;
        client_max_body_size 20M;

        ssl_certificate     /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 1d;
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

        # API
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 60s;
        }

        # Auth — tighter rate limit
        location /api/auth/ {
            limit_req zone=auth burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Media files
        location /media/ {
            proxy_pass http://backend;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # Frontend SPA
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    }
}
NGINXEOF

ok "nginx.conf updated for HTTPS"

# ─── RESTART NGINX ────────────────────────────────────────────────────────────
info "Starting Nginx with SSL..."
docker compose up -d nginx
sleep 3

HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/health" 2>/dev/null || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
  ok "HTTPS health check passed!"
else
  warn "HTTPS returned HTTP $HTTP_CODE — check: docker compose logs nginx"
fi

# ─── AUTO-RENEWAL CRON ────────────────────────────────────────────────────────
info "Setting up automatic certificate renewal..."
# Remove existing prepiq renewal cron if present
(crontab -l 2>/dev/null | grep -v 'prepiq-ssl-renew') | crontab -

# Add renewal cron: runs daily at 3am, copies new certs and reloads nginx
(crontab -l 2>/dev/null; cat << CRONEOF
# PrepIQ SSL auto-renewal — runs daily at 3:00am
0 3 * * * certbot renew --quiet --standalone --pre-hook "cd $(pwd) && docker compose stop nginx" --post-hook "cd $(pwd) && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/ && docker compose start nginx" >> /var/log/prepiq-ssl-renew.log 2>&1
CRONEOF
) | crontab -

ok "Auto-renewal cron installed (daily at 3am)"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║       SSL Setup Complete! 🔒                  ║${RESET}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Platform:${RESET} https://$DOMAIN"
echo -e "  ${BOLD}Cert:${RESET}     /etc/letsencrypt/live/$DOMAIN/"
echo -e "  ${BOLD}Renews:${RESET}   Automatically via cron (daily 3am)"
echo ""
echo "  Test renewal dry-run:"
echo "    sudo certbot renew --dry-run"
echo ""
