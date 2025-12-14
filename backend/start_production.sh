#!/bin/bash

################################################################################
# Zook Production Startup Script
# 
# Starts the FastAPI backend with production-optimized settings
# Includes pre-flight checks for SSL, Cloudflare Tunnel, and configuration
################################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Zook Production Server - Startup Script            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

################################################################################
# Step 1: Environment Check
################################################################################

print_info "Checking environment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Please create .env file with production settings."
    print_info "See ENV_CONFIG.md for reference."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Verify critical environment variables
if [ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "your-secret-key-change-this-in-production" ]; then
    print_error "JWT_SECRET_KEY not set or using default value!"
    print_info "Generate a secure key with: openssl rand -hex 32"
    exit 1
fi

if [ "$ENVIRONMENT" != "production" ]; then
    print_warning "ENVIRONMENT is not set to 'production' in .env"
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

print_success "Environment validated"
echo ""

################################################################################
# Step 2: HTTPS Configuration Check
################################################################################

print_info "Checking HTTPS configuration..."

if [ "$USE_HTTPS" = "true" ]; then
    print_success "HTTPS is ENABLED"
    
    if [ "$ENFORCE_HTTPS_REDIRECT" = "true" ]; then
        print_success "HTTP → HTTPS redirect is ENABLED"
    else
        print_warning "HTTP → HTTPS redirect is DISABLED"
    fi
    
    if [ "$CLOUDFLARE_TUNNEL_ENABLED" = "true" ]; then
        print_success "Cloudflare Tunnel is ENABLED"
        
        # Check if cloudflared is running
        if systemctl is-active --quiet cloudflared 2>/dev/null; then
            print_success "cloudflared service is running"
        elif pgrep -x "cloudflared" > /dev/null; then
            print_success "cloudflared process is running"
        else
            print_warning "cloudflared does not appear to be running"
            print_info "Start it with: sudo systemctl start cloudflared"
            print_info "Or run manually: cloudflared tunnel run <tunnel-name>"
        fi
    else
        print_info "Cloudflare Tunnel is disabled"
        
        # Check for direct SSL certificates
        if [ -n "$SSL_CERT_PATH" ] && [ -n "$SSL_KEY_PATH" ]; then
            if [ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ]; then
                print_success "SSL certificates found"
            else
                print_error "SSL certificate paths set but files not found!"
                print_error "  SSL_CERT_PATH: $SSL_CERT_PATH"
                print_error "  SSL_KEY_PATH: $SSL_KEY_PATH"
                exit 1
            fi
        else
            print_warning "No SSL configuration detected"
            print_info "For HTTPS, configure Cloudflare Tunnel or set SSL_CERT_PATH/SSL_KEY_PATH"
        fi
    fi
    
    if [ -n "$PRODUCTION_URL" ]; then
        print_success "Production URL: $PRODUCTION_URL"
    else
        print_warning "PRODUCTION_URL not set"
    fi
else
    print_error "⚠️  USE_HTTPS is FALSE in production mode!"
    print_warning "Your application will run over insecure HTTP"
    print_info "Set USE_HTTPS=true in .env for secure connections"
    read -p "Continue with insecure HTTP? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

echo ""

################################################################################
# Step 3: Database Check
################################################################################

print_info "Checking database configuration..."

if [ -z "$DATABASE_URL" ]; then
    print_error "DATABASE_URL not set in .env!"
    exit 1
fi

print_success "Database URL configured"

# Check database SSL mode
if [ "$DATABASE_SSL_MODE" = "require" ] || [ "$DATABASE_SSL_MODE" = "verify-full" ]; then
    print_success "Database SSL mode: $DATABASE_SSL_MODE"
else
    print_warning "Database SSL mode: ${DATABASE_SSL_MODE:-prefer} (consider using 'require' in production)"
fi

echo ""

################################################################################
# Step 4: Python Environment
################################################################################

print_info "Checking Python environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
print_success "Python: $PYTHON_VERSION"

# Check if virtual environment should be activated
if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
elif [ -n "$VIRTUAL_ENV" ]; then
    print_success "Virtual environment already active: $VIRTUAL_ENV"
fi

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    print_warning "Dependencies not installed. Installing..."
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
fi

echo ""

################################################################################
# Step 5: AI Model Check
################################################################################

print_info "Checking AI detection model..."

if [ "$USE_CUSTOM_MODEL" = "true" ]; then
    if [ -f "$CUSTOM_MODEL_PATH" ]; then
        print_success "Custom model found: $CUSTOM_MODEL_PATH"
    else
        print_warning "Custom model not found at: $CUSTOM_MODEL_PATH"
        print_info "Will fall back to COCO pretrained model"
    fi
else
    print_info "Using COCO pretrained model"
fi

echo ""

################################################################################
# Step 6: Production Checklist
################################################################################

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Production Readiness Checklist                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check each item
CHECKS_PASSED=0
CHECKS_TOTAL=7

# 1. JWT Secret
if [ "$JWT_SECRET_KEY" != "your-secret-key-change-this-in-production" ]; then
    echo "✓ Strong JWT secret key configured"
    ((CHECKS_PASSED++))
else
    echo "✗ Using default JWT secret key (INSECURE!)"
fi

# 2. HTTPS
if [ "$USE_HTTPS" = "true" ]; then
    echo "✓ HTTPS enabled"
    ((CHECKS_PASSED++))
else
    echo "✗ HTTPS disabled"
fi

# 3. Database SSL
if [ "$DATABASE_SSL_MODE" = "require" ] || [ "$DATABASE_SSL_MODE" = "verify-full" ]; then
    echo "✓ Database SSL enabled"
    ((CHECKS_PASSED++))
else
    echo "✗ Database SSL not enforced"
fi

# 4. Production URL
if [ -n "$PRODUCTION_URL" ]; then
    echo "✓ Production URL configured"
    ((CHECKS_PASSED++))
else
    echo "✗ Production URL not set"
fi

# 5. CORS Origins
if echo "$CORS_ORIGINS" | grep -q "http://localhost"; then
    echo "⚠ CORS includes localhost (remove in production)"
else
    echo "✓ CORS origins configured for production"
    ((CHECKS_PASSED++))
fi

# 6. Cloudflare Tunnel or SSL
if [ "$CLOUDFLARE_TUNNEL_ENABLED" = "true" ] || ([ -f "$SSL_CERT_PATH" ] && [ -f "$SSL_KEY_PATH" ]); then
    echo "✓ SSL/Tunnel infrastructure configured"
    ((CHECKS_PASSED++))
else
    echo "✗ No SSL infrastructure detected"
fi

# 7. Environment set to production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "✓ Environment set to production"
    ((CHECKS_PASSED++))
else
    echo "⚠ Environment not set to production"
fi

echo ""
print_info "Checks passed: $CHECKS_PASSED/$CHECKS_TOTAL"

if [ $CHECKS_PASSED -lt 5 ]; then
    print_warning "Some production checks failed. Review your configuration."
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

echo ""

################################################################################
# Step 7: Start Server
################################################################################

print_info "Starting Zook production server..."
echo ""

# Determine number of workers (2x CPU cores, minimum 2)
WORKERS=${WORKERS:-$(( $(nproc) * 2 ))}
[ $WORKERS -lt 2 ] && WORKERS=2

print_info "Workers: $WORKERS"
print_info "Host: 0.0.0.0"
print_info "Port: 8000"
print_info "Server URL: ${PRODUCTION_URL:-http://localhost:8000}"
print_info "API Docs: ${PRODUCTION_URL:-http://localhost:8000}/docs"
echo ""

# Create logs directory
mkdir -p logs

# Start server with production settings
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $WORKERS \
    --log-level info \
    --access-log \
    --log-config logging.conf 2>/dev/null || \
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers $WORKERS \
    --log-level info

# Note: First command tries with logging.conf, falls back to default if not found

