# Zook FastAPI Server - Quick Start Script for Windows
# This script sets up and starts the authentication server

Write-Host "=== Zook Authentication Server ===" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ from https://python.org" -ForegroundColor Yellow
    exit 1
}

Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from ENV_CONFIG.md defaults..." -ForegroundColor Yellow
    Write-Host "Please edit .env file with your configuration" -ForegroundColor Yellow
    
    # Create basic .env file
    @"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/zook
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3500,http://localhost:3000
ENVIRONMENT=development
USE_HTTPS=false
ENFORCE_HTTPS_REDIRECT=false
USE_CUSTOM_MODEL=true
CUSTOM_MODEL_PATH=app/models/custom_knife_model.pt
DETECTION_DEVICE=cpu
DETECTION_CONFIDENCE_THRESHOLD=0.90
"@ | Out-File -FilePath ".env" -Encoding UTF8
}

# Load and check environment
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    
    # Check for ENVIRONMENT setting
    if ($envContent -match 'ENVIRONMENT=(.+)') {
        $environment = $matches[1].Trim()
        Write-Host "Environment: $environment" -ForegroundColor Cyan
        
        # Check HTTPS settings for production
        if ($environment -eq "production") {
            Write-Host ""
            Write-Host "=== PRODUCTION MODE DETECTED ===" -ForegroundColor Yellow
            
            if ($envContent -match 'USE_HTTPS=(.+)') {
                $useHttps = $matches[1].Trim()
                if ($useHttps -eq "true") {
                    Write-Host "✓ HTTPS is ENABLED" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  WARNING: HTTPS is DISABLED in production!" -ForegroundColor Red
                    Write-Host "   Set USE_HTTPS=true in .env for secure connections" -ForegroundColor Yellow
                }
            }
            
            if ($envContent -match 'PRODUCTION_URL=(.+)') {
                $prodUrl = $matches[1].Trim()
                if ($prodUrl) {
                    Write-Host "✓ Production URL: $prodUrl" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  WARNING: PRODUCTION_URL not set!" -ForegroundColor Yellow
                }
            }
            
            if ($envContent -match 'CLOUDFLARE_TUNNEL_ENABLED=(.+)') {
                $tunnelEnabled = $matches[1].Trim()
                if ($tunnelEnabled -eq "true") {
                    Write-Host "✓ Cloudflare Tunnel is ENABLED" -ForegroundColor Green
                    Write-Host "   Ensure cloudflared service is running" -ForegroundColor Cyan
                }
            }
            
            Write-Host ""
            Write-Host "Production Checklist:" -ForegroundColor Yellow
            Write-Host "  □ Strong JWT_SECRET_KEY generated" -ForegroundColor White
            Write-Host "  □ DATABASE_SSL_MODE=require" -ForegroundColor White
            Write-Host "  □ Cloudflare Tunnel configured and running" -ForegroundColor White
            Write-Host "  □ CORS_ORIGINS includes production domain" -ForegroundColor White
            Write-Host ""
        }
    }
}

Write-Host ""
Write-Host "=== Starting Server ===" -ForegroundColor Green

# Determine server URL based on environment
$serverUrl = "http://localhost:8000"
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match 'PRODUCTION_URL=(.+)') {
        $prodUrl = $matches[1].Trim()
        if ($prodUrl -and $prodUrl -ne "") {
            $serverUrl = $prodUrl
        }
    }
}

Write-Host "Server will be available at: $serverUrl" -ForegroundColor Cyan
Write-Host "API Documentation: $serverUrl/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
uvicorn app.main:app --reload --port 8000


