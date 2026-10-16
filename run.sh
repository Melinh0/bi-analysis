
set -e

MODE="development"
BACKEND_ONLY=false
FRONTEND_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --production) MODE="production" ;;
        --backend-only) BACKEND_ONLY=true ;;
        --frontend-only) FRONTEND_ONLY=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON_EXE="$ROOT_DIR/.venv/bin/python"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[90m'
NC='\033[0m' # No Color

log() {
    local prefix=$1
    local message=$2
    local color=$3
    local timestamp=$(date '+%H:%M:%S')
    echo -e "${GRAY}[$timestamp]${NC} ${color}[$prefix]${NC} $message"
}

log_system() { log "SYSTEM" "$1" "$YELLOW"; }
log_backend() { log "BACKEND" "$1" "$CYAN"; }
log_frontend() { log "FRONTEND" "$1" "$GREEN"; }
log_error() { log "ERROR" "$1" "$RED"; }

cleanup() {
    echo ""
    log_system "Shutdown signal received..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    sleep 1
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null
        fi
    done
    log_system "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

log_system "=== BI Analysis Full Stack ==="
log_system "Mode: $MODE"
log_system "Root: $ROOT_DIR"
echo ""

PIDS=()

if [ "$FRONTEND_ONLY" = false ]; then
    if [ ! -f "$PYTHON_EXE" ]; then
        log_error "Python not found at $PYTHON_EXE. Run 'uv sync' first."
        exit 1
    fi

    log_system "Starting Backend (FastAPI on http://localhost:8000)..."
    
    PYTHONPATH="$BACKEND_DIR" "$PYTHON_EXE" -m uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | while IFS= read -r line; do
        log_backend "$line"
    done &
    PIDS+=($!)
fi

if [ "$BACKEND_ONLY" = false ]; then
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_system "Installing frontend dependencies..."
        cd "$FRONTEND_DIR" && npm install
    fi

    log_system "Starting Frontend (Vite on http://localhost:5173)..."
    
    cd "$FRONTEND_DIR" && npm run dev 2>&1 | while IFS= read -r line; do
        log_frontend "$line"
    done &
    PIDS+=($!)
fi

echo ""
log_system "All services started!"
[ "$FRONTEND_ONLY" = false ] && log_system "Backend:  http://localhost:8000 (API: http://localhost:8000/api)"
[ "$BACKEND_ONLY" = false ] && log_system "Frontend: http://localhost:5173"
log_system "Press Ctrl+C to stop all services."
echo ""

wait