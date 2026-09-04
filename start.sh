#!/usr/bin/env bash

# ============================================================
# Intelligent Land Record Digitization and Validation System
# Service Startup Script
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/.pids"

mkdir -p "${LOG_DIR}" "${PID_DIR}"

echo "============================================================"
echo " Starting Land Record AI System"
echo "============================================================"

# 1. Start Docker Infrastructure (PostgreSQL, Redis, MinIO)
echo "[1/4] Checking supporting Docker containers..."
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "       Starting PostgreSQL, Redis, and MinIO via docker compose..."
    (cd "${PROJECT_ROOT}" && docker compose up -d) || {
        echo "       [WARNING] Docker compose failed or docker is not running."
        echo "       Make sure Docker Desktop is open if you need DB/Redis/MinIO."
    }
else
    echo "       [WARNING] Docker compose not found. Ensure DB, Redis, and MinIO are running."
fi

# 2. Start FastAPI Backend
echo "[2/4] Starting FastAPI backend on http://localhost:8000..."
if [ -f "${PROJECT_ROOT}/backend/.venv/bin/uvicorn" ]; then
    PYTHON_BIN="${PROJECT_ROOT}/backend/.venv/bin/python"
    UVICORN_BIN="${PROJECT_ROOT}/backend/.venv/bin/uvicorn"
else
    PYTHON_BIN="python3"
    UVICORN_BIN="uvicorn"
fi

(cd "${PROJECT_ROOT}/backend" && \
    nohup "${UVICORN_BIN}" app.main:app --host 0.0.0.0 --port 8000 --reload > "${LOG_DIR}/backend.log" 2>&1 & echo $! > "${PID_DIR}/backend.pid")
echo "       FastAPI started (PID: $(cat "${PID_DIR}/backend.pid")) -> logs at logs/backend.log"

# 3. Start Celery AI Worker
echo "[3/4] Starting Celery AI processing worker..."
if [ -f "${PROJECT_ROOT}/backend/.venv/bin/celery" ]; then
    CELERY_BIN="${PROJECT_ROOT}/backend/.venv/bin/celery"
else
    CELERY_BIN="celery"
fi

(cd "${PROJECT_ROOT}/backend" && \
    nohup "${CELERY_BIN}" -A app.workers.celery_app.celery_app worker --loglevel=info -c 2 > "${LOG_DIR}/celery.log" 2>&1 & echo $! > "${PID_DIR}/celery.pid")
echo "       Celery worker started (PID: $(cat "${PID_DIR}/celery.pid")) -> logs at logs/celery.log"

# 4. Start Next.js Frontend
echo "[4/4] Starting Next.js frontend on http://localhost:3000..."
(cd "${PROJECT_ROOT}/frontend" && \
    nohup npm run dev > "${LOG_DIR}/frontend.log" 2>&1 & echo $! > "${PID_DIR}/frontend.pid")
echo "       Next.js frontend started (PID: $(cat "${PID_DIR}/frontend.pid")) -> logs at logs/frontend.log"

echo ""
echo "============================================================"
echo " All services started successfully!"
echo "============================================================"
echo " - Government Portal (Frontend) : http://localhost:3000"
echo " - FastAPI Backend & Docs       : http://localhost:8000/docs"
echo " - Health Check Endpoint        : http://localhost:8000/health"
echo " - MinIO Console (if running)   : http://localhost:9001"
echo ""
echo " To stop all services, run:"
echo "   ./stop.sh"
echo "============================================================"
