#!/usr/bin/env bash
# =============================================================================
# BankOfCaptcha - Production / Staging Deployment Script
# =============================================================================
# Deploys the multi-tier containerized stack with healthchecks and rollback safety.
# Usage: ./scripts/deploy.sh [staging|production]
# =============================================================================

set -e

ENV_TARGET="${1:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=========================================================="
echo " Deploying BankOfCaptcha Stack to [$ENV_TARGET] Environment"
echo "=========================================================="

# Ensure environment file exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "[!] No .env file found. Copying .env.example..."
    cp .env.example .env
fi

# Build or pull latest images
echo "[1/4] Building container images..."
docker compose -f docker-compose.full.yml build

# Start or recreate services
echo "[2/4] Starting services in detached mode..."
docker compose -f docker-compose.full.yml up -d

# Health verification
echo "[3/4] Performing deployment health checks..."
MAX_ATTEMPTS=20
COUNT=0
HEALTHY=false

while [ $COUNT -lt $MAX_ATTEMPTS ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/branches || true)
    if [ "$HTTP_CODE" = "200" ]; then
        HEALTHY=true
        break
    fi
    COUNT=$((COUNT + 1))
    echo "  Waiting for backend API... ($COUNT/$MAX_ATTEMPTS)"
    sleep 3
done

if [ "$HEALTHY" = false ]; then
    echo "[-] Health check FAILED! Initiating rollback..."
    docker compose -f docker-compose.full.yml down
    exit 1
fi

echo "[4/4] Verifying frontend static distribution..."
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 || true)
if [ "$FRONTEND_CODE" != "200" ]; then
    echo "[-] Frontend health check FAILED! Code: $FRONTEND_CODE"
    exit 1
fi

echo "=========================================================="
echo " [SUCCESS] Deployment to [$ENV_TARGET] completed successfully!"
echo " Stack is up and running:"
echo "   - Frontend UI:  http://localhost:5173"
echo "   - Backend API:  http://localhost:8080"
echo "=========================================================="

