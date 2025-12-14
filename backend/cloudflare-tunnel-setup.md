# Cloudflare Tunnel Setup Guide

Complete guide for setting up Cloudflare Tunnel to enable HTTPS encryption for your Zook production deployment.

## Overview

Cloudflare Tunnel creates a secure, encrypted connection between your server and Cloudflare's edge network without opening inbound ports. Benefits include:

- **Free SSL/TLS certificates** - Automatic certificate management
- **Zero firewall configuration** - No need to open ports 80/443
- **DDoS protection** - Built-in Cloudflare security
- **Global CDN** - Low latency worldwide
- **Automatic certificate renewal** - No manual intervention needed

## Prerequisites

- Domain name (can be registered through Cloudflare or any registrar)
- Cloudflare account (free tier is sufficient)
- Domain DNS managed by Cloudflare
- Linux/Windows/Mac server with internet access

## Step 1: Domain Setup

### 1.1 Add Domain to Cloudflare

1. Sign up at [Cloudflare](https://dash.cloudflare.com/sign-up)
2. Click "Add a Site" and enter your domain
3. Select the Free plan
4. Update nameservers at your domain registrar to Cloudflare's nameservers
5. Wait for DNS propagation (5 minutes to 48 hours)

### 1.2 Verify DNS is Active

```bash
# Check if Cloudflare DNS is active
dig yourdomain.com NS +short
# Should show Cloudflare nameservers like: alec.ns.cloudflare.com
```

## Step 2: Install Cloudflared

### Linux (Debian/Ubuntu)

```bash
# Download and install
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

### Linux (RHEL/CentOS)

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo rpm -i cloudflared-linux-x86_64.rpm
cloudflared --version
```

### macOS

```bash
brew install cloudflared
cloudflared --version
```

### Windows

```powershell
# Download from GitHub releases
# https://github.com/cloudflare/cloudflared/releases/latest
# Install cloudflared-windows-amd64.exe to C:\Program Files\cloudflared\

# Or use Chocolatey
choco install cloudflared
cloudflared --version
```

## Step 3: Authenticate with Cloudflare

```bash
# This will open a browser window for authentication
cloudflared tunnel login

# After successful login, a certificate file is created at:
# Linux/Mac: ~/.cloudflared/cert.pem
# Windows: C:\Users\<username>\.cloudflared\cert.pem
```

Verify the certificate exists:

```bash
# Linux/Mac
ls -la ~/.cloudflared/cert.pem

# Windows
dir %USERPROFILE%\.cloudflared\cert.pem
```

## Step 4: Create Tunnel

```bash
# Create a tunnel named "zook-production"
cloudflared tunnel create zook-production

# Output will show:
# Tunnel credentials written to /home/user/.cloudflared/<TUNNEL_ID>.json
# Tunnel created successfully with ID: <TUNNEL_ID>
```

**Important:** Save the Tunnel ID and credentials file path. You'll need them for configuration.

## Step 5: Configure Tunnel

### 5.1 Create Configuration File

Create `~/.cloudflared/config.yml` (Linux/Mac) or `C:\Users\<username>\.cloudflared\config.yml` (Windows):

```yaml
# Cloudflare Tunnel Configuration for Zook
tunnel: <YOUR_TUNNEL_ID>
credentials-file: /home/user/.cloudflared/<YOUR_TUNNEL_ID>.json

# Ingress rules - route traffic to your FastAPI backend
ingress:
  # Route your domain to localhost:8000 (FastAPI)
  - hostname: zook.yourdomain.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      # WebSocket support
      disableChunkedEncoding: false
  
  # Catch-all rule (required)
  - service: http_status:404

# Auto-update cloudflared
autoupdate-freq: 24h

# Logging
loglevel: info
logfile: /var/log/cloudflared.log
```

**Replace:**
- `<YOUR_TUNNEL_ID>` with your actual tunnel ID
- `<YOUR_TUNNEL_ID>.json` with your credentials file name
- `zook.yourdomain.com` with your actual domain

### 5.2 Alternative: Backend Directory Configuration

You can also place the config in your backend directory for easier deployment:

```bash
# Copy to backend directory
cp ~/.cloudflared/config.yml backend/cloudflare-tunnel.yml
cp ~/.cloudflared/<TUNNEL_ID>.json backend/cloudflare-credentials.json

# Add to .gitignore
echo "cloudflare-credentials.json" >> backend/.gitignore
```

Then reference it in the tunnel config:

```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: ./cloudflare-credentials.json
# ... rest of config
```

## Step 6: Configure DNS

Route your domain to the tunnel:

```bash
# Create DNS CNAME record pointing to tunnel
cloudflared tunnel route dns zook-production zook.yourdomain.com
```

This automatically creates a CNAME record in Cloudflare DNS pointing to your tunnel.

**Manual DNS Configuration (Alternative):**

1. Go to Cloudflare Dashboard > DNS
2. Add CNAME record:
   - **Name:** zook (or @ for root domain)
   - **Target:** `<TUNNEL_ID>.cfargotunnel.com`
   - **Proxy status:** Proxied (orange cloud)
   - **TTL:** Auto

## Step 7: Test Tunnel

Start the tunnel manually to test:

```bash
cloudflared tunnel run zook-production
```

You should see:

```
INFO  Connection established                            connIndex=0 location=LAX
INFO  Connection established                            connIndex=1 location=SJC
INFO  Connection established                            connIndex=2 location=PHX
INFO  Connection established                            connIndex=3 location=DFW
```

In another terminal, ensure your FastAPI backend is running:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Now test your domain:

```bash
curl https://zook.yourdomain.com/health
# Should return: {"status":"healthy","service":"zook-auth-server"}
```

## Step 8: Install as System Service

Make cloudflared start automatically on boot.

### Linux (systemd)

```bash
# Install as system service
sudo cloudflared service install

# Enable and start service
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Check status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f
```

### Windows (Service)

```powershell
# Run as Administrator
cloudflared service install

# Start service
sc start cloudflared

# Check status
sc query cloudflared
```

### macOS (launchd)

```bash
# Install as launch daemon
sudo cloudflared service install

# Start service
sudo launchctl start cloudflared

# Check status
sudo launchctl list | grep cloudflared
```

## Step 9: Update Zook Configuration

Update your backend `.env` file:

```env
# Enable production mode
ENVIRONMENT=production

# Enable HTTPS
USE_HTTPS=true
ENFORCE_HTTPS_REDIRECT=true

# Enable Cloudflare Tunnel
CLOUDFLARE_TUNNEL_ENABLED=true

# Set production URL
PRODUCTION_URL=https://zook.yourdomain.com

# Update CORS origins
CORS_ORIGINS=https://zook.yourdomain.com

# Enable database SSL
DATABASE_SSL_MODE=require
```

Restart your backend server:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Step 10: Verify HTTPS

### Test SSL Certificate

```bash
# Check SSL certificate
curl -v https://zook.yourdomain.com/health

# Should show:
# * SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
# * Server certificate:
# *  subject: CN=zook.yourdomain.com
# *  issuer: C=US; O=Cloudflare, Inc.; CN=Cloudflare Inc ECC CA-3
```

### Test Security Headers

```bash
curl -I https://zook.yourdomain.com/

# Should include headers like:
# strict-transport-security: max-age=31536000; includeSubDomains
# x-content-type-options: nosniff
# x-frame-options: DENY
```

### Test WebSocket (WSS)

```bash
# Install wscat if needed
npm install -g wscat

# Test WebSocket connection
wscat -c "wss://zook.yourdomain.com/ws/stream?token=YOUR_JWT_TOKEN"
```

### Browser Test

1. Navigate to `https://zook.yourdomain.com`
2. Check for padlock icon in address bar
3. Click padlock → Certificate → Should show Cloudflare certificate
4. Open browser console (F12) → No mixed content warnings

## Troubleshooting

### Tunnel Won't Start

```bash
# Check tunnel status
cloudflared tunnel info zook-production

# Test connectivity
cloudflared tunnel run zook-production --loglevel debug
```

### 502 Bad Gateway

- Ensure FastAPI backend is running on localhost:8000
- Check `config.yml` service URL is correct
- Verify firewall allows localhost connections

### WebSocket Connection Failed

- Ensure `disableChunkedEncoding: false` in config
- Check CORS settings include production domain
- Verify JWT token is valid

### DNS Not Resolving

```bash
# Check DNS record
dig zook.yourdomain.com +short

# Should show Cloudflare IPs like: 104.18.x.x
```

Wait up to 5 minutes for DNS propagation.

### Certificate Errors

- Ensure Cloudflare proxy is enabled (orange cloud)
- Check SSL/TLS mode in Cloudflare Dashboard → SSL/TLS → Overview
- Set to "Full" or "Full (strict)"

## Monitoring & Maintenance

### View Tunnel Logs

```bash
# Linux
sudo journalctl -u cloudflared -f

# Manual run logs
cloudflared tunnel run zook-production --loglevel debug
```

### Update Cloudflared

```bash
# Linux
sudo cloudflared update

# Or if service is running
sudo systemctl stop cloudflared
sudo cloudflared update
sudo systemctl start cloudflared
```

### Tunnel Analytics

View tunnel analytics in Cloudflare Dashboard:
1. Go to Zero Trust → Networks → Tunnels
2. Click on your tunnel name
3. View traffic, health, and performance metrics

## Security Best Practices

1. **Restrict Access**: Use Cloudflare Access to add authentication
2. **Rate Limiting**: Configure Cloudflare rate limiting rules
3. **WAF Rules**: Enable Web Application Firewall
4. **IP Restrictions**: Whitelist specific IPs if needed
5. **DDoS Protection**: Enable "Under Attack Mode" during attacks
6. **Audit Logs**: Review Cloudflare audit logs regularly

## Backup Configuration

Save these files securely:

```bash
# Backup tunnel configuration
cp ~/.cloudflared/config.yml ~/zook-tunnel-config-backup.yml
cp ~/.cloudflared/<TUNNEL_ID>.json ~/zook-tunnel-creds-backup.json

# Store in secure location (password manager, encrypted storage)
```

## Uninstalling

If you need to remove the tunnel:

```bash
# Stop and uninstall service
sudo cloudflared service uninstall

# Delete tunnel
cloudflared tunnel delete zook-production

# Remove DNS record
# Do this manually in Cloudflare Dashboard
```

## Cost Summary

- **Cloudflare Tunnel**: Free (unlimited)
- **SSL Certificate**: Free (auto-renewed)
- **Bandwidth**: Free (up to Cloudflare's generous limits)
- **DDoS Protection**: Included
- **Total Cost**: $0/month

## Next Steps

- Set up monitoring with Cloudflare analytics
- Configure Cloudflare Page Rules for caching
- Enable Cloudflare Access for additional security
- Set up alerting for tunnel downtime
- Review logs regularly for security events

## Support Resources

- **Cloudflare Docs**: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **Community**: https://community.cloudflare.com/
- **Status**: https://www.cloudflarestatus.com/

