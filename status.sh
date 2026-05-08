#!/bin/bash
# ============================================
# AGRI-COPILOT Status Script
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_PORT=8000
FRONTEND_PORT=3003

echo -e "${BLUE}"
echo "============================================"
echo "   AGRI-COPILOT - Service Status"
echo "============================================"
echo -e "${NC}"

# Check Backend
echo -n "Backend  (port $BACKEND_PORT): "
if curl -s --connect-timeout 2 "http://localhost:$BACKEND_PORT/docs" >/dev/null 2>&1; then
    echo -e "${GREEN}Running${NC}"

    # Get RAG status
    RAG_INFO=$(curl -s "http://localhost:$BACKEND_PORT/api/chat/rag-status" 2>/dev/null)
    if [ -n "$RAG_INFO" ]; then
        CHUNKS=$(echo "$RAG_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('chunk_count',0))" 2>/dev/null || echo "?")
        echo "           RAG: yes ($CHUNKS chunks)"
    fi
else
    echo -e "${RED}Stopped${NC}"
fi

# Check Frontend
echo -n "Frontend (port $FRONTEND_PORT): "
if curl -s --connect-timeout 2 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Stopped${NC}"
fi

echo ""
echo -e "${BLUE}URLs:${NC}"
echo "  Web UI:   http://localhost:$FRONTEND_PORT"
echo "  API:      http://localhost:$BACKEND_PORT"
echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
echo ""
