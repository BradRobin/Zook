#!/bin/bash

################################################################################
# Cloudflare Tunnel Installation Script for Zook Production
# 
# This script automates the installation and configuration of Cloudflare Tunnel
# for HTTPS encryption in production deployments.
#
# Usage:
#   sudo bash install_cloudflare_tunnel.sh
#
# Prerequisites:
#   - Root/sudo access
#   - Active internet connection
#   - Cloudflare account with domain added
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_info "Starting Cloudflare Tunnel installation for Zook..."
echo ""

################################################################################
# Step 1: Detect OS and Install Cloudflared
################################################################################

print_info "Detecting operating system..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    print_success "Detected OS: $OS $VERSION"
else
    print_error "Cannot detect OS. Unsupported system."
    exit 1
fi

print_info "Installing cloudflared..."

case $OS in
    ubuntu|debian)
        # Download and install DEB package
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
        dpkg -i /tmp/cloudflared.deb
        rm /tmp/cloudflared.deb
        ;;
    
    centos|rhel|fedora)
        # Download and install RPM package
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm -O /tmp/cloudflared.rpm
        rpm -i /tmp/cloudflared.rpm
        rm /tmp/cloudflared.rpm
        ;;
    
    *)
        print_warning "Unsupported OS. Attempting generic binary installation..."
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared
        chmod +x /usr/local/bin/cloudflared
        ;;
esac

# Verify installation
if command -v cloudflared &> /dev/null; then
    CLOUDFLARED_VERSION=$(cloudflared --version | head -n1)
    print_success "cloudflared installed: $CLOUDFLARED_VERSION"
else
    print_error "cloudflared installation failed"
    exit 1
fi

echo ""

################################################################################
# Step 2: Authenticate with Cloudflare
################################################################################

print_info "Authenticating with Cloudflare..."
print_warning "A browser window will open for authentication."
print_warning "Please log in to your Cloudflare account and authorize the tunnel."
echo ""

# Run as the original user (not root)
ORIGINAL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
ORIGINAL_HOME=$(eval echo ~$ORIGINAL_USER)

if [ -z "$ORIGINAL_USER" ]; then
    print_error "Cannot determine original user. Please run as: sudo -E bash $0"
    exit 1
fi

# Authenticate (this opens a browser)
sudo -u $ORIGINAL_USER cloudflared tunnel login

if [ ! -f "$ORIGINAL_HOME/.cloudflared/cert.pem" ]; then
    print_error "Authentication failed. Certificate not found at $ORIGINAL_HOME/.cloudflared/cert.pem"
    exit 1
fi

print_success "Authentication successful!"
echo ""

################################################################################
# Step 3: Create Tunnel
################################################################################

print_info "Creating Cloudflare Tunnel..."
echo ""

read -p "Enter tunnel name (default: zook-production): " TUNNEL_NAME
TUNNEL_NAME=${TUNNEL_NAME:-zook-production}

# Create tunnel as original user
TUNNEL_OUTPUT=$(sudo -u $ORIGINAL_USER cloudflared tunnel create $TUNNEL_NAME)

# Extract tunnel ID from output
TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep -oP 'Tunnel credentials written to.*\/\K[a-f0-9-]+(?=\.json)')

if [ -z "$TUNNEL_ID" ]; then
    print_error "Failed to extract tunnel ID. Output:"
    echo "$TUNNEL_OUTPUT"
    exit 1
fi

CREDENTIALS_FILE="$ORIGINAL_HOME/.cloudflared/$TUNNEL_ID.json"

if [ ! -f "$CREDENTIALS_FILE" ]; then
    print_error "Credentials file not found: $CREDENTIALS_FILE"
    exit 1
fi

print_success "Tunnel created successfully!"
print_info "Tunnel ID: $TUNNEL_ID"
print_info "Credentials: $CREDENTIALS_FILE"
echo ""

################################################################################
# Step 4: Configure Tunnel
################################################################################

print_info "Configuring tunnel..."
echo ""

read -p "Enter your domain (e.g., zook.yourdomain.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Domain is required"
    exit 1
fi

# Create config directory if it doesn't exist
mkdir -p $ORIGINAL_HOME/.cloudflared

# Create config file
CONFIG_FILE="$ORIGINAL_HOME/.cloudflared/config.yml"

cat > $CONFIG_FILE <<EOF
# Cloudflare Tunnel Configuration for Zook
tunnel: $TUNNEL_ID
credentials-file: $CREDENTIALS_FILE

ingress:
  - hostname: $DOMAIN
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      disableChunkedEncoding: false
  
  - service: http_status:404

autoupdate-freq: 24h
loglevel: info
EOF

chown $ORIGINAL_USER:$ORIGINAL_USER $CONFIG_FILE
print_success "Configuration created: $CONFIG_FILE"
echo ""

################################################################################
# Step 5: Configure DNS
################################################################################

print_info "Configuring DNS..."
echo ""

read -p "Route DNS automatically? (y/n, default: y): " AUTO_DNS
AUTO_DNS=${AUTO_DNS:-y}

if [[ "$AUTO_DNS" == "y" ]]; then
    sudo -u $ORIGINAL_USER cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN
    print_success "DNS configured for $DOMAIN"
else
    print_warning "Skipping automatic DNS configuration."
    print_info "Manual DNS setup:"
    print_info "1. Go to Cloudflare Dashboard > DNS"
    print_info "2. Add CNAME record:"
    print_info "   Name: $(echo $DOMAIN | cut -d'.' -f1)"
    print_info "   Target: $TUNNEL_ID.cfargotunnel.com"
    print_info "   Proxy: Enabled (orange cloud)"
fi

echo ""

################################################################################
# Step 6: Test Tunnel
################################################################################

print_info "Testing tunnel configuration..."
echo ""

# Test tunnel (runs for 5 seconds then kills)
timeout 5 sudo -u $ORIGINAL_USER cloudflared tunnel run $TUNNEL_NAME &> /tmp/tunnel_test.log || true

if grep -q "Connection established" /tmp/tunnel_test.log; then
    print_success "Tunnel test successful!"
else
    print_warning "Tunnel test inconclusive. Check logs:"
    cat /tmp/tunnel_test.log
fi

rm -f /tmp/tunnel_test.log
echo ""

################################################################################
# Step 7: Install as System Service
################################################################################

print_info "Installing tunnel as system service..."
echo ""

# Install service
cloudflared service install

# Enable and start service
systemctl enable cloudflared
systemctl start cloudflared

# Wait a moment for service to start
sleep 2

# Check status
if systemctl is-active --quiet cloudflared; then
    print_success "Cloudflared service is running!"
else
    print_warning "Service installed but not running. Check with: sudo systemctl status cloudflared"
fi

echo ""

################################################################################
# Step 8: Save Configuration Summary
################################################################################

SUMMARY_FILE="$ORIGINAL_HOME/cloudflare-tunnel-summary.txt"

cat > $SUMMARY_FILE <<EOF
Cloudflare Tunnel Configuration Summary
========================================

Installation Date: $(date)
Tunnel Name: $TUNNEL_NAME
Tunnel ID: $TUNNEL_ID
Domain: $DOMAIN

Files:
- Config: $CONFIG_FILE
- Credentials: $CREDENTIALS_FILE
- Certificate: $ORIGINAL_HOME/.cloudflared/cert.pem

Service Management:
- Start: sudo systemctl start cloudflared
- Stop: sudo systemctl stop cloudflared
- Restart: sudo systemctl restart cloudflared
- Status: sudo systemctl status cloudflared
- Logs: sudo journalctl -u cloudflared -f

Next Steps:
1. Update backend/.env:
   ENVIRONMENT=production
   USE_HTTPS=true
   ENFORCE_HTTPS_REDIRECT=true
   CLOUDFLARE_TUNNEL_ENABLED=true
   PRODUCTION_URL=https://$DOMAIN
   CORS_ORIGINS=https://$DOMAIN

2. Ensure FastAPI is running:
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000

3. Test your domain:
   curl https://$DOMAIN/health

4. Verify SSL:
   curl -v https://$DOMAIN/health | grep "SSL connection"

Troubleshooting:
- View logs: sudo journalctl -u cloudflared -f
- Test tunnel: cloudflared tunnel run $TUNNEL_NAME
- DNS check: dig $DOMAIN +short
- Tunnel info: cloudflared tunnel info $TUNNEL_NAME

Documentation:
- Setup guide: backend/cloudflare-tunnel-setup.md
- Config template: backend/cloudflare-tunnel.yml.template
EOF

chown $ORIGINAL_USER:$ORIGINAL_USER $SUMMARY_FILE
print_success "Configuration summary saved: $SUMMARY_FILE"

################################################################################
# Final Summary
################################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_success "Cloudflare Tunnel is now running!"
echo ""
print_info "Configuration Details:"
print_info "  Tunnel Name: $TUNNEL_NAME"
print_info "  Tunnel ID: $TUNNEL_ID"
print_info "  Domain: $DOMAIN"
print_info "  Service: Active"
echo ""
print_info "Next Steps:"
echo "  1. Update backend/.env with production settings"
echo "  2. Start/restart your FastAPI backend"
echo "  3. Test: curl https://$DOMAIN/health"
echo "  4. Review summary: cat $SUMMARY_FILE"
echo ""
print_info "Service Commands:"
echo "  View logs:   sudo journalctl -u cloudflared -f"
echo "  Stop tunnel: sudo systemctl stop cloudflared"
echo "  Restart:     sudo systemctl restart cloudflared"
echo ""
print_success "Your Zook application is now accessible via HTTPS!"
echo ""

exit 0

