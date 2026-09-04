#!/usr/bin/env bash

# ============================================================
# Intelligent Land Record Digitization and Validation System
# Service Shutdown Script
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${PROJECT_ROOT}/.pids"

echo "============================================================"
echo " Stopping Land Record AI System"
echo "============================================================"

stop_pid() {
    local name="$1"
    local pid_file="${PID_DIR}/${name}.pid"

    if [ -f "${pid_file}" ]; then
        local pid=$(cat "${pid_file}")
        if kill -0 "${pid}" 2>/dev/null; then
            echo "Stopping ${name} (PID: ${pid})..."
            kill "${pid}" 2>/dev/null || true
            sleep 1
            if kill -0 "${pid}" 2>/dev/null; then
                kill -9 "${pid}" 2>/dev/null || true
            fi
        else
            echo "${name} (PID: ${pid}) was not running."
        fi
        rm -f "${pid_file}"
    fi
}

# 1. Stop Frontend
stop_pid "frontend"
# Kill any lingering next dev process on port 3000
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

# 2. Stop Backend
stop_pid "backend"
# Kill any lingering uvicorn process on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# 3. Stop Celery Worker
stop_pid "celery"
pkill -f "celery -A app.workers.celery_app" 2>/dev/null || true

echo ""
echo "All application services have been stopped."
echo "If you also want to stop Docker containers (Postgres, Redis, MinIO), run:"
echo "  docker compose stop"
echo "============================================================"
