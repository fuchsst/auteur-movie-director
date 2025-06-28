#!/bin/bash
# Backend Service Manager for Blender Movie Director
# Supports both local Python and Docker deployments

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Default configuration
COMFYUI_PORT="${COMFYUI_PORT:-8188}"
WAN2GP_PORT="${WAN2GP_PORT:-7860}"
RVC_PORT="${RVC_PORT:-7865}"
AUDIOLDM_PORT="${AUDIOLDM_PORT:-7863}"

# Service directories
COMFYUI_DIR="${COMFYUI_DIR:-../ComfyUI}"
WAN2GP_DIR="${WAN2GP_DIR:-../Wan2GP}"
RVC_DIR="${RVC_DIR:-../RVC}"
AUDIOLDM_DIR="${AUDIOLDM_DIR:-../AudioLDM}"

# Docker settings
USE_DOCKER="${USE_DOCKER:-false}"
DOCKER_NETWORK="${DOCKER_NETWORK:-bmad-network}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Log file
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "$LOG_DIR"

echo "🎬 Blender Movie Director - Backend Service Manager"
echo "=================================================="
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":$port "
    else
        # Fallback: try to connect
        timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/$port" 2>/dev/null
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    local max_attempts=30
    local attempt=0
    
    echo -n "⏳ Waiting for $name to be ready"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://localhost:$port$endpoint" >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to start service in Python virtual environment
start_python_service() {
    local name=$1
    local dir=$2
    local port=$3
    local cmd=$4
    local venv_name="${5:-venv}"
    local health_endpoint="${6:-/}"
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}✗ $name directory not found at: $dir${NC}"
        return 1
    fi
    
    cd "$dir"
    
    # Find and use the virtual environment
    local python_cmd=""
    if [ -f "venv/bin/python" ]; then
        echo "  Using venv/bin/python"
        python_cmd="venv/bin/python"
    elif [ -f ".venv/bin/python" ]; then
        echo "  Using .venv/bin/python"
        python_cmd=".venv/bin/python"
    elif [ -f "venv/Scripts/python.exe" ]; then
        # Windows venv
        echo "  Using venv/Scripts/python.exe"
        python_cmd="venv/Scripts/python.exe"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        # Windows .venv
        echo "  Using .venv/Scripts/python.exe"
        python_cmd=".venv/Scripts/python.exe"
    else
        echo -e "${YELLOW}⚠️  No virtual environment found, using system Python${NC}"
        python_cmd="python"
    fi
    
    # Replace python in the command with the venv python
    local actual_cmd="${cmd/python/$python_cmd}"
    
    # Start the service
    echo -e "${BLUE}Starting $name on port $port...${NC}"
    nohup $actual_cmd > "$LOG_DIR/${name,,}.log" 2>&1 &
    local pid=$!
    echo $pid > "$LOG_DIR/${name,,}.pid"
    
    cd - > /dev/null
    
    # Wait for service to be ready
    wait_for_service "$name" "$port" "$health_endpoint"
}

# Function to start service in Docker
start_docker_service() {
    local name=$1
    local image=$2
    local port=$3
    local env_vars=$4
    
    echo -e "${BLUE}Starting $name (Docker) on port $port...${NC}"
    
    # Create network if it doesn't exist
    docker network create $DOCKER_NETWORK 2>/dev/null || true
    
    # Stop existing container if running
    docker stop "bmad-${name,,}" 2>/dev/null || true
    docker rm "bmad-${name,,}" 2>/dev/null || true
    
    # Start new container
    docker run -d \
        --name "bmad-${name,,}" \
        --network $DOCKER_NETWORK \
        -p "$port:$port" \
        $env_vars \
        "$image"
}

# Function to stop a service
stop_service() {
    local name=$1
    local port=$2
    
    echo -n "🛑 Stopping $name... "
    
    # Try to stop using PID file
    if [ -f "$LOG_DIR/${name,,}.pid" ]; then
        local pid=$(cat "$LOG_DIR/${name,,}.pid")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            rm "$LOG_DIR/${name,,}.pid"
            echo -e "${GREEN}✓${NC}"
            return
        fi
    fi
    
    # Try to stop Docker container
    if docker ps -q -f name="bmad-${name,,}" 2>/dev/null | grep -q .; then
        docker stop "bmad-${name,,}"
        echo -e "${GREEN}✓${NC}"
        return
    fi
    
    # Try to stop by port
    if check_port $port; then
        if command -v lsof >/dev/null 2>&1; then
            local pid=$(lsof -ti:$port)
            if [ -n "$pid" ]; then
                kill $pid 2>/dev/null || true
                echo -e "${GREEN}✓${NC}"
                return
            fi
        fi
    fi
    
    echo -e "${YELLOW}Not running${NC}"
}

# Function to show service status
show_status() {
    echo "📊 Service Status:"
    echo ""
    
    local services=(
        "ComfyUI:$COMFYUI_PORT:/system_stats"
        "Wan2GP:$WAN2GP_PORT:/api/health"
        "RVC:$RVC_PORT:/api/status"
        "AudioLDM:$AUDIOLDM_PORT:/api/ready"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port endpoint <<< "$service"
        
        echo -n "  $name: "
        if check_port $port; then
            # Try to get actual health status
            if curl -s "http://localhost:$port$endpoint" >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Running (healthy) on port $port${NC}"
            else
                echo -e "${YELLOW}⚠️  Running (unhealthy) on port $port${NC}"
            fi
        else
            echo -e "${RED}❌ Not running${NC}"
        fi
    done
    
    echo ""
    
    # Show Docker status if using Docker
    if [ "$USE_DOCKER" = "true" ]; then
        echo "🐳 Docker Containers:"
        docker ps -a --filter "name=bmad-" --format "table {{.Names}}\t{{.Status}}" | tail -n +2
    fi
}

# Function to show logs
show_logs() {
    local service=$1
    local lines=${2:-50}
    
    if [ -z "$service" ]; then
        echo "Available log files:"
        ls -la "$LOG_DIR"/*.log 2>/dev/null || echo "No logs found"
    else
        local log_file="$LOG_DIR/${service,,}.log"
        if [ -f "$log_file" ]; then
            echo "📄 Last $lines lines of $service logs:"
            tail -n $lines "$log_file"
        else
            echo "No log file found for $service"
        fi
    fi
}

# Main command handling
case "${1:-help}" in
    start)
        shift
        SERVICE="${1:-all}"
        
        if [ "$SERVICE" = "all" ]; then
            echo "🚀 Starting all backend services..."
            echo ""
            
            if [ "$USE_DOCKER" = "true" ]; then
                # Docker deployment
                start_docker_service "ComfyUI" "comfyui/comfyui:latest" "$COMFYUI_PORT" ""
                start_docker_service "Wan2GP" "wan2gp/wan2gp:latest" "$WAN2GP_PORT" ""
                start_docker_service "RVC" "rvc/rvc:latest" "$RVC_PORT" ""
                start_docker_service "AudioLDM" "audioldm/audioldm:latest" "$AUDIOLDM_PORT" ""
            else
                # Local Python deployment
                # Add --listen flag if running in WSL to allow access from Linux side
                local comfyui_args="--port $COMFYUI_PORT"
                if grep -qi microsoft /proc/version 2>/dev/null; then
                    comfyui_args="$comfyui_args --listen"
                fi
                start_python_service "ComfyUI" "$COMFYUI_DIR" "$COMFYUI_PORT" \
                    "python main.py $comfyui_args" "venv" "/system_stats"
                    
                start_python_service "Wan2GP" "$WAN2GP_DIR" "$WAN2GP_PORT" \
                    "python app.py --port $WAN2GP_PORT" "venv" "/api/health"
                    
                start_python_service "RVC" "$RVC_DIR" "$RVC_PORT" \
                    "python server.py --port $RVC_PORT" "venv" "/api/status"
                    
                start_python_service "AudioLDM" "$AUDIOLDM_DIR" "$AUDIOLDM_PORT" \
                    "python app.py --port $AUDIOLDM_PORT" "venv" "/api/ready"
            fi
            
            echo ""
            show_status
        else
            # Start specific service
            case "$SERVICE" in
                comfyui)
                    if [ "$USE_DOCKER" = "true" ]; then
                        start_docker_service "ComfyUI" "comfyui/comfyui:latest" "$COMFYUI_PORT" ""
                    else
                        start_python_service "ComfyUI" "$COMFYUI_DIR" "$COMFYUI_PORT" \
                            "python main.py --port $COMFYUI_PORT" "venv" "/system_stats"
                    fi
                    ;;
                wan2gp)
                    if [ "$USE_DOCKER" = "true" ]; then
                        start_docker_service "Wan2GP" "wan2gp/wan2gp:latest" "$WAN2GP_PORT" ""
                    else
                        start_python_service "Wan2GP" "$WAN2GP_DIR" "$WAN2GP_PORT" \
                            "python app.py --port $WAN2GP_PORT" "venv" "/api/health"
                    fi
                    ;;
                rvc)
                    if [ "$USE_DOCKER" = "true" ]; then
                        start_docker_service "RVC" "rvc/rvc:latest" "$RVC_PORT" ""
                    else
                        start_python_service "RVC" "$RVC_DIR" "$RVC_PORT" \
                            "python server.py --port $RVC_PORT" "venv" "/api/status"
                    fi
                    ;;
                audioldm)
                    if [ "$USE_DOCKER" = "true" ]; then
                        start_docker_service "AudioLDM" "audioldm/audioldm:latest" "$AUDIOLDM_PORT" ""
                    else
                        start_python_service "AudioLDM" "$AUDIOLDM_DIR" "$AUDIOLDM_PORT" \
                            "python app.py --port $AUDIOLDM_PORT" "venv" "/api/ready"
                    fi
                    ;;
                *)
                    echo "Unknown service: $SERVICE"
                    echo "Available services: comfyui, wan2gp, rvc, audioldm"
                    exit 1
                    ;;
            esac
        fi
        ;;
        
    stop)
        shift
        SERVICE="${1:-all}"
        
        if [ "$SERVICE" = "all" ]; then
            echo "🛑 Stopping all services..."
            stop_service "ComfyUI" "$COMFYUI_PORT"
            stop_service "Wan2GP" "$WAN2GP_PORT"
            stop_service "RVC" "$RVC_PORT"
            stop_service "AudioLDM" "$AUDIOLDM_PORT"
            echo "✅ All services stopped"
        else
            case "$SERVICE" in
                comfyui) stop_service "ComfyUI" "$COMFYUI_PORT" ;;
                wan2gp) stop_service "Wan2GP" "$WAN2GP_PORT" ;;
                rvc) stop_service "RVC" "$RVC_PORT" ;;
                audioldm) stop_service "AudioLDM" "$AUDIOLDM_PORT" ;;
                *)
                    echo "Unknown service: $SERVICE"
                    exit 1
                    ;;
            esac
        fi
        ;;
        
    restart)
        shift
        SERVICE="${1:-all}"
        $0 stop $SERVICE
        sleep 2
        $0 start $SERVICE
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        shift
        show_logs "$1" "${2:-50}"
        ;;
        
    help|*)
        echo "Usage: $0 {start|stop|restart|status|logs} [service] [options]"
        echo ""
        echo "Commands:"
        echo "  start [service]    Start service(s) (default: all)"
        echo "  stop [service]     Stop service(s) (default: all)"
        echo "  restart [service]  Restart service(s) (default: all)"
        echo "  status             Show status of all services"
        echo "  logs [service] [n] Show last n lines of logs (default: 50)"
        echo ""
        echo "Services:"
        echo "  all      All services (default)"
        echo "  comfyui  ComfyUI service"
        echo "  wan2gp   Wan2GP service"
        echo "  rvc      RVC service"
        echo "  audioldm AudioLDM service"
        echo ""
        echo "Environment Variables:"
        echo "  USE_DOCKER=true    Use Docker instead of local Python"
        echo "  COMFYUI_DIR        Path to ComfyUI directory"
        echo "  COMFYUI_PORT       ComfyUI port (default: 8188)"
        echo "  (Similar for other services)"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start all services"
        echo "  $0 start comfyui   # Start only ComfyUI"
        echo "  $0 status          # Check service status"
        echo "  $0 logs comfyui    # View ComfyUI logs"
        echo "  USE_DOCKER=true $0 start  # Start with Docker"
        ;;
esac