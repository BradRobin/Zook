# Zook Frontend - Quick Start Script
# Simple HTTP server for development

Write-Host "=== Zook Frontend UI ===" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan
Write-Host ""

# Navigate to src directory
$srcPath = Join-Path $PSScriptRoot "src"
Set-Location $srcPath

Write-Host "=== Starting Frontend Server ===" -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3500" -ForegroundColor Cyan
Write-Host "Make sure backend is running on: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Python HTTP server on port 3500
python -m http.server 3500

