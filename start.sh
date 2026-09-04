#!/usr/bin/env bash

# ============================================================
# Intelligent Land Record Digitization and Validation System
# Unified Development Startup Script
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/.pids"

mkdir -p "${LOG_DIR}" "${PID_DIR}"

echo "============================================================"
echo " Starting Land Record AI System"
echo "============================================================"

# ------------------------------------------------------------
# 1. Start Docker Infrastructure
# ------------------------------------------------------------

echo "[1/4] Starting Docker infrastructure..."

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "[ERROR] Docker Compose is not available."
    exit 1
fi

(cd "${PROJECT_ROOT}" && docker compose up -d)

echo "       PostgreSQL + PostGIS + pgvector : started"
echo "       Redis                            : started"
echo "       MinIO                            : started"

# ------------------------------------------------------------
# Wait for PostgreSQL
# ------------------------------------------------------------

echo "       Waiting for PostgreSQL..."

until docker exec land-record-postgres \
    pg_isready -U land_admin -d land_records >/dev/null 2>&1
do
    sleep 2
done

echo "       PostgreSQL is ready."

# ------------------------------------------------------------
# Wait for Redis
# ------------------------------------------------------------

echo "       Waiting for Redis..."

until docker exec land-record-redis \
    redis-cli ping >/dev/null 2>&1
do
    sleep 2
done

echo "       Redis is ready."

# ------------------------------------------------------------
# 2. Start FastAPI Backend
# ------------------------------------------------------------

echo "[2/4] Starting FastAPI backend..."

PYTHON_BIN="${PROJECT_ROOT}/backend/.venv/bin/python"
UVICORN_BIN="${PROJECT_ROOT}/backend/.venv/bin/uvicorn"

if [ ! -f "${PYTHON_BIN}" ]; then
    echo "[ERROR] Backend virtual environment not found."
    echo "        Expected: ${PYTHON_BIN}"
    exit 1
fi

if [ ! -f "${UVICORN_BIN}" ]; then
    echo "[ERROR] Uvicorn not found in backend virtual environment."
    exit 1
fi

echo "       Backend: http://localhost:8000"

(
    cd "${PROJECT_ROOT}/backend"

    echo "       Running database migrations..."
    "${PYTHON_BIN}" -m app.db.migrate > "${LOG_DIR}/migrate.log" 2>&1 || true

    nohup "${UVICORN_BIN}" \
        app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        > "${LOG_DIR}/backend.log" 2>&1 &

    echo $! > "${PID_DIR}/backend.pid"
)

echo "       FastAPI PID: $(cat "${PID_DIR}/backend.pid")"

# ------------------------------------------------------------
# 3. Start Celery Worker
# ------------------------------------------------------------

echo "[3/4] Starting Celery AI worker..."

CELERY_BIN="${PROJECT_ROOT}/backend/.venv/bin/celery"

if [ ! -f "${CELERY_BIN}" ]; then
    echo "[ERROR] Celery not found in backend virtual environment."
    exit 1
fi

(
    cd "${PROJECT_ROOT}/backend"

    nohup "${CELERY_BIN}" \
        -A app.workers.celery_app.celery_app \
        worker \
        --loglevel=info \
        -c 2 \
        > "${LOG_DIR}/celery.log" 2>&1 &

    echo $! > "${PID_DIR}/celery.pid"
)

echo "       Celery PID: $(cat "${PID_DIR}/celery.pid")"

# ------------------------------------------------------------
# 4. Start Next.js Frontend
# ------------------------------------------------------------

echo "[4/4] Starting Next.js frontend..."

if [ ! -f "${PROJECT_ROOT}/frontend/package.json" ]; then
    echo "[ERROR] frontend/package.json not found."
    exit 1
fi

(
    cd "${PROJECT_ROOT}/frontend"

    # Clear stale build cache to prevent "Cannot find module './NNN.js'" errors
    rm -rf .next

    nohup npm run dev \
        > "${LOG_DIR}/frontend.log" 2>&1 &

    echo $! > "${PID_DIR}/frontend.pid"
)

echo "       Next.js PID: $(cat "${PID_DIR}/frontend.pid")"

# ------------------------------------------------------------
# Final
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " All services started!"
echo "============================================================"
echo ""
echo " Frontend:"
echo "   http://localhost:3000"
echo ""
echo " Backend:"
echo "   http://localhost:8000"
echo ""
echo " API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo " Health:"
echo "   http://localhost:8000/health"
echo ""
echo " MinIO:"
echo "   http://localhost:9001"
echo ""
echo " Logs:"
echo "   logs/backend.log"
echo "   logs/celery.log"
echo "   logs/frontend.log"
echo ""
echo " Stop everything:"
echo "   ./stop.sh"
echo ""
echo "============================================================"