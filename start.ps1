# ============================================================
# Intelligent Land Record Digitization and Validation System
# Windows Startup Script (PowerShell)
# ============================================================

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Starting Land Record AI System (Windows)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check Docker / Infrastructure
Write-Host "[1/3] Checking Infrastructure..." -ForegroundColor Yellow
$DockerAvailable = $false
try {
    $null = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $DockerAvailable = $true
    }
} catch {
    $DockerAvailable = $false
}

if ($DockerAvailable) {
    Write-Host "       Docker detected. Starting PostgreSQL, Redis, MinIO..." -ForegroundColor Green
    Set-Location $ProjectRoot
    docker compose up -d
} else {
    Write-Host "       Docker is not running. Using local SQLite database." -ForegroundColor DarkYellow
}

# 2. Start Backend
Write-Host "[2/3] Starting FastAPI Backend..." -ForegroundColor Yellow
$BackendDir = Join-Path $ProjectRoot "backend"
Set-Location $BackendDir

Write-Host "       Running database migrations..." -ForegroundColor Gray
python -m app.db.migrate

Write-Host "       Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
Start-Process python -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory $BackendDir -WindowStyle Hidden

# 3. Start Frontend
Write-Host "[3/3] Starting Next.js Frontend..." -ForegroundColor Yellow
$FrontendDir = Join-Path $ProjectRoot "frontend"
Set-Location $FrontendDir

Write-Host "       Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
Start-Process npm.cmd -ArgumentList "run dev" -WorkingDirectory $FrontendDir -WindowStyle Hidden

Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " All services started successfully!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host " Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host " API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host " To stop all services, run: .\stop.ps1 or .\stop.bat" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
