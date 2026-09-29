# ============================================================
# Intelligent Land Record Digitization and Validation System
# Windows Service Shutdown Script (PowerShell)
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Stopping Land Record AI System" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Stop python processes (uvicorn backend) running on port 8000
$BackendProc = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($BackendProc) {
    Write-Host "Stopping Backend (PID: $BackendProc)..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProc -Force -ErrorAction SilentlyContinue
}

# Stop node processes (next dev frontend) running on port 3000
$FrontendProc = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($FrontendProc) {
    Write-Host "Stopping Frontend (PID: $FrontendProc)..." -ForegroundColor Yellow
    Stop-Process -Id $FrontendProc -Force -ErrorAction SilentlyContinue
}

# Stop docker containers if running
try {
    $null = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Stopping Docker containers..." -ForegroundColor Yellow
        docker compose stop 2>$null
    }
} catch {}

Write-Host "All services stopped." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
