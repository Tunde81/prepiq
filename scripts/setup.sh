#!/bin/bash
# PrepIQ VPS Setup Script
# Run as: chmod +x scripts/setup.sh && ./scripts/setup.sh

set -e

echo "╔═══════════════════════════════════════╗"
echo "║        PrepIQ VPS Setup           ║"
echo "╚═══════════════════════════════════════╝"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "→ Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✓ Docker installed"
fi

# Check for Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "→ Installing Docker Compose plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "✓ Docker Compose installed"
fi

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    # Generate a random SECRET_KEY
    SECRET=$(openssl rand -hex 32)
    sed -i "s/CHANGE_ME_64_CHAR_SECRET_KEY_GENERATE_WITH_OPENSSL_RAND/$SECRET/" .env
    echo "✓ .env created — EDIT IT BEFORE CONTINUING"
    echo ""
    echo "⚠️  Please update .env with your values:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - REDIS_PASSWORD"  
    echo "   - FIRST_SUPERADMIN_EMAIL"
    echo "   - FIRST_SUPERADMIN_PASSWORD"
    echo "   - FRONTEND_URL (your domain)"
    echo "   - SMTP settings (for email)"
    echo ""
    read -p "Press ENTER after editing .env to continue..."
fi

echo "→ Building and starting PrepIQ..."
docker compose pull
docker compose build --no-cache
docker compose up -d

echo "→ Waiting for services to be healthy..."
sleep 15

echo "→ Running database migrations..."
docker compose exec backend alembic upgrade head

echo ""
echo "╔═══════════════════════════════════════╗"
echo "║         PrepIQ is LIVE!           ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "  Frontend:  http://localhost"
echo "  API Docs:  http://localhost/api/docs"
echo "  Health:    http://localhost/api/health"
echo ""
echo "  Admin login:"
echo "  Email:    $(grep FIRST_SUPERADMIN_EMAIL .env | cut -d= -f2)"
echo "  Password: (as set in .env)"
echo ""
echo "To view logs:  docker compose logs -f"
echo "To stop:       docker compose down"
echo "To update:     git pull && docker compose up -d --build"
