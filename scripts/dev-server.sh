#!/bin/bash
# Start backend services for development

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Default ports (can be overridden in .env)
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
WAN2GP_PORT="${WAN2GP_PORT:-7860}"
RVC_PORT="${RVC_PORT:-7865}"
AUDIOLDM_PORT="${AUDIOLDM_PORT:-7863}"

# Service directories (customize based on your setup)
COMFYUI_DIR="${COMFYUI_DIR:-../ComfyUI}"
WAN2GP_DIR="${WAN2GP_DIR:-../Wan2GP}"
RVC_DIR="${RVC_DIR:-../RVC}"
AUDIOLDM_DIR="${AUDIOLDM_DIR:-../AudioLDM}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🎬 Movie Director Backend Services Manager"
echo "=========================================="
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service
start_service() {
    local name=$1
    local dir=$2
    local port=$3
    local cmd=$4
    
    echo -n "🔍 Checking $name... "
    
    if check_port $port; then
        echo -e "${GREEN}Already running on port $port${NC}"
    elif [ -d "$dir" ]; then
        echo -e "${YELLOW}Starting on port $port${NC}"
        cd "$dir"
        eval "$cmd" &
        cd - > /dev/null
    else
        echo -e "${RED}Not found at $dir${NC}"
        echo "   Set ${name}_DIR in .env or install $name"
    fi
}

# Parse command line arguments
SERVICE="${1:-all}"

case "$SERVICE" in
    "comfyui")
        start_service "ComfyUI" "$COMFYUI_DIR" "$COMFYUI_PORT" \
            "python main.py --port $COMFYUI_PORT"
        ;;
    
    "wan2gp")
        start_service "Wan2GP" "$WAN2GP_DIR" "$WAN2GP_PORT" \
            "python app.py --port $WAN2GP_PORT"
        ;;
    
    "rvc")
        start_service "RVC" "$RVC_DIR" "$RVC_PORT" \
            "python server.py --port $RVC_PORT"
        ;;
    
    "audioldm")
        start_service "AudioLDM" "$AUDIOLDM_DIR" "$AUDIOLDM_PORT" \
            "python app.py --port $AUDIOLDM_PORT"
        ;;
    
    "status")
        echo "📊 Service Status:"
        echo ""
        
        for service in "ComfyUI:$COMFYUI_PORT" "Wan2GP:$WAN2GP_PORT" \
                      "RVC:$RVC_PORT" "AudioLDM:$AUDIOLDM_PORT"; do
            name="${service%:*}"
            port="${service#*:}"
            
            if check_port $port; then
                echo -e "  ✅ $name: ${GREEN}Running on port $port${NC}"
            else
                echo -e "  ❌ $name: ${RED}Not running${NC}"
            fi
        done
        ;;
    
    "stop")
        echo "🛑 Stopping all services..."
        
        for port in $COMFYUI_PORT $WAN2GP_PORT $RVC_PORT $AUDIOLDM_PORT; do
            if check_port $port; then
                pid=$(lsof -ti:$port)
                if [ -n "$pid" ]; then
                    echo "  Stopping process on port $port (PID: $pid)"
                    kill $pid 2>/dev/null || true
                fi
            fi
        done
        
        echo "✅ All services stopped"
        ;;
    
    "all"|*)
        echo "🚀 Starting all backend services..."
        echo ""
        
        # Start services
        start_service "ComfyUI" "$COMFYUI_DIR" "$COMFYUI_PORT" \
            "python main.py --port $COMFYUI_PORT"
        
        start_service "Wan2GP" "$WAN2GP_DIR" "$WAN2GP_PORT" \
            "python app.py --port $WAN2GP_PORT"
        
        start_service "RVC" "$RVC_DIR" "$RVC_PORT" \
            "python server.py --port $RVC_PORT"
        
        start_service "AudioLDM" "$AUDIOLDM_DIR" "$AUDIOLDM_PORT" \
            "python app.py --port $AUDIOLDM_PORT"
        
        # Wait and show status
        echo ""
        echo "⏳ Waiting for services to start..."
        sleep 3
        
        echo ""
        ./scripts/dev-server.sh status
        
        echo ""
        echo "💡 Tips:"
        echo "  - Check status: ./scripts/dev-server.sh status"
        echo "  - Stop all: ./scripts/dev-server.sh stop"
        echo "  - View logs: Check individual service directories"
        echo "  - Configure: Edit .env file for custom paths/ports"
        ;;
esac