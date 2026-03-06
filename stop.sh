#!/bin/bash
# ============================================
# AGRI-COPILOT Stop Script
# Cucumber Irrigation Intelligent Agent System
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_ROOT/logs/services.pid"

# Default ports
BACKEND_PORT=8000
FRONTEND_PORT=3003

# Parse config.ini if exists
if [ -f "$PROJECT_ROOT/config.ini" ]; then
    BACKEND_PORT=$(grep -E "^backend_port\s*=" config.ini | cut -d'=' -f2 | tr -d ' ' || echo "8000")
    FRONTEND_PORT=$(grep -E "^frontend_port\s*=" config.ini | cut -d'=' -f2 | tr -d ' ' || echo "3003")
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           AGRI-COPILOT - Stop Script                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Kill by process patterns
echo -e "${YELLOW}Stopping Backend...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "  ${GREEN}Backend stopped${NC}" || echo -e "  ${YELLOW}Backend not running${NC}"

echo -e "${YELLOW}Stopping Frontend...${NC}"
pkill -f "vite" 2>/dev/null && echo -e "  ${GREEN}Frontend stopped${NC}" || echo -e "  ${YELLOW}Frontend not running${NC}"
pkill -f "node.*$FRONTEND_PORT" 2>/dev/null || true

# Also try fuser if available
fuser -k $BACKEND_PORT/tcp 2>/dev/null || true
fuser -k $FRONTEND_PORT/tcp 2>/dev/null || true

# Remove PID file
rm -f "$PID_FILE" 2>/dev/null

echo ""
echo -e "${GREEN}All services stopped.${NC}"
echo ""
