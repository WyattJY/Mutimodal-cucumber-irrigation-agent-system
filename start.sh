#!/bin/bash
# ============================================
# AGRI-COPILOT Startup Script
# Cucumber Irrigation Intelligent Agent System
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Server ports
BACKEND_PORT=8000
FRONTEND_PORT=3003

# Log files
BACKEND_LOG="$PROJECT_ROOT/logs/backend.log"
FRONTEND_LOG="$PROJECT_ROOT/logs/frontend.log"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}"
echo "============================================"
echo "   AGRI-COPILOT - Startup Script"
echo "   Cucumber Irrigation Agent System"
echo "============================================"
echo -e "${NC}"

# Step 1: Stop existing services
echo -e "${YELLOW}[1/4] Stopping existing services...${NC}"
pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

# Step 2: Start Backend
echo -e "${GREEN}[2/4] Starting Backend (port $BACKEND_PORT)...${NC}"
cd "$PROJECT_ROOT/backend"
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/backend"

nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID"

# Wait for backend
echo -n "  Waiting"
for i in $(seq 1 90); do
    if curl -s --connect-timeout 1 "http://localhost:$BACKEND_PORT/docs" >/dev/null 2>&1; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if ! curl -s --connect-timeout 1 "http://localhost:$BACKEND_PORT/docs" >/dev/null 2>&1; then
    echo -e " ${YELLOW}(still initializing)${NC}"
fi

# Step 3: Start Frontend
echo -e "${GREEN}[3/4] Starting Frontend (port $FRONTEND_PORT)...${NC}"
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install --silent
fi

nohup npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID"

# Wait for frontend
echo -n "  Waiting"
for i in $(seq 1 30); do
    if curl -s --connect-timeout 1 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Step 4: Show status
echo -e "${GREEN}[4/4] Services started${NC}"
echo ""

# Final status check
sleep 2
"$PROJECT_ROOT/status.sh"

echo -e "To stop: ${YELLOW}./stop.sh${NC}"
echo ""
