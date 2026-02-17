#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  🤖 Autonomous Coding Agent — VPS Setup & Launch Script
# ═══════════════════════════════════════════════════════════════
set -e

# Colors
RED='\033[0;91m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
BLUE='\033[0;94m'
CYAN='\033[0;96m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════╗"
echo "║        🤖 Autonomous Coding Agent Setup         ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Check Python ───────────────────────────────────────────
echo -e "${BLUE}[1/5] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=python3
    echo -e "  ${GREEN}✅ Python3 found: $(python3 --version)${NC}"
elif command -v python &> /dev/null; then
    PYTHON=python
    echo -e "  ${GREEN}✅ Python found: $(python --version)${NC}"
else
    echo -e "  ${RED}❌ Python not found. Install Python 3.11+${NC}"
    exit 1
fi

# ─── Check Ollama ───────────────────────────────────────────
echo -e "${BLUE}[2/5] Checking Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "  ${GREEN}✅ Ollama found${NC}"
else
    echo -e "  ${YELLOW}⚠ Ollama not found. Installing...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Ollama is running${NC}"
else
    echo -e "  ${YELLOW}⚠ Starting Ollama...${NC}"
    ollama serve &
    sleep 3
fi

# ─── Check Models ──────────────────────────────────────────
echo -e "${BLUE}[3/5] Checking models...${NC}"

CODER_MODEL="${CODER_MODEL:-qwen2.5-coder:32b-instruct-q3_K_M}"
REVIEWER_MODEL="${REVIEWER_MODEL:-qwen2.5-coder:14b}"

check_model() {
    local model=$1
    if ollama list | grep -q "$model"; then
        echo -e "  ${GREEN}✅ $model${NC}"
    else
        echo -e "  ${YELLOW}⚠ Pulling $model (this may take a while)...${NC}"
        ollama pull "$model"
    fi
}

check_model "$CODER_MODEL"
check_model "$REVIEWER_MODEL"

# ─── Install Python deps ──────────────────────────────────
echo -e "${BLUE}[4/5] Installing Python dependencies...${NC}"
$PYTHON -m pip install -r requirements.txt -q 2>/dev/null
echo -e "  ${GREEN}✅ Dependencies installed${NC}"

# ─── Create workspace ─────────────────────────────────────
echo -e "${BLUE}[5/5] Setting up workspace...${NC}"
mkdir -p workspace
echo -e "  ${GREEN}✅ Workspace ready: ./workspace/${NC}"

# ─── Launch Menu ──────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════╗"
echo "║              Ready to Launch!                    ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║  [1] CLI Mode  — Terminal agent                  ║"
echo "║  [2] Web Mode  — Browser UI (port 8080)          ║"
echo "║  [3] Both      — CLI + Web UI                    ║"
echo "║                                                  ║"
echo -e "╚══════════════════════════════════════════════════╝${NC}"
echo ""

read -p "Choose mode [1/2/3]: " mode

case $mode in
    1)
        echo -e "\n${GREEN}🚀 Starting CLI Agent...${NC}\n"
        echo -e "${YELLOW}Enter your goal when prompted.${NC}\n"
        $PYTHON agent.py
        ;;
    2)
        echo -e "\n${GREEN}🌐 Starting Web UI on port ${WEB_PORT:-8080}...${NC}"
        echo -e "${YELLOW}Open: http://your-vps-ip:${WEB_PORT:-8080}${NC}\n"
        $PYTHON server.py
        ;;
    3)
        echo -e "\n${GREEN}🚀 Starting Web UI + CLI...${NC}\n"
        $PYTHON server.py &
        SERVER_PID=$!
        echo -e "${YELLOW}Web UI: http://your-vps-ip:${WEB_PORT:-8080}${NC}"
        echo -e "${YELLOW}CLI starting below...${NC}\n"
        sleep 2
        $PYTHON agent.py
        kill $SERVER_PID 2>/dev/null
        ;;
    *)
        echo -e "${RED}Invalid choice. Run again.${NC}"
        exit 1
        ;;
esac
