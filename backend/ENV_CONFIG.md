# Environment Configuration Guide

This file documents all environment variables for the Zook Authentication Server.
Copy these settings to your `.env` file and update with your values.

## Database Configuration

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/zook
DATABASE_SSL_MODE=prefer  # prefer | require | verify-full (use "require" in production)
```

## JWT Authentication

```env
JWT_SECRET_KEY=your-secret-key-change-this-in-production  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

## CORS Configuration

```env
CORS_ORIGINS=http://localhost:3500,http://localhost:3000  # Add production domain when deploying
```

## Application Settings

```env
ENVIRONMENT=development  # development | production
API_V1_STR=/api
PROJECT_NAME=Zook Auth Server
```

## HTTPS & Security Configuration

```env
# Enable HTTPS features (set to true in production)
USE_HTTPS=false

# Force HTTP to HTTPS redirect (only when USE_HTTPS=true)
ENFORCE_HTTPS_REDIRECT=false

# Your production domain (e.g., https://zook.yourdomain.com)
PRODUCTION_URL=

# Cloudflare Tunnel (recommended for production)
CLOUDFLARE_TUNNEL_ENABLED=false
```

## Direct SSL Configuration (Alternative to Cloudflare)

```env
# Path to SSL certificate and key files
# Only needed if not using Cloudflare Tunnel
SSL_CERT_PATH=/path/to/fullchain.pem
SSL_KEY_PATH=/path/to/privkey.pem
```

## AI Detection Model Configuration

```env
# Use custom-trained model (true) or COCO pretrained (false)
USE_CUSTOM_MODEL=true
CUSTOM_MODEL_PATH=app/models/custom_knife_model.pt

# Detection device: cpu | cuda | mps (Apple Silicon)
DETECTION_DEVICE=cpu

# Minimum confidence threshold (0.0 - 1.0)
DETECTION_CONFIDENCE_THRESHOLD=0.90
```

## Production Deployment Examples

### Cloudflare Tunnel Deployment (Recommended)

```env
ENVIRONMENT=production
USE_HTTPS=true
ENFORCE_HTTPS_REDIRECT=true
CLOUDFLARE_TUNNEL_ENABLED=true
PRODUCTION_URL=https://zook.yourdomain.com
DATABASE_SSL_MODE=require
JWT_SECRET_KEY=<generated-secure-key>
CORS_ORIGINS=https://zook.yourdomain.com
```

### Traditional Deployment with Nginx

```env
ENVIRONMENT=production
USE_HTTPS=true
ENFORCE_HTTPS_REDIRECT=true
CLOUDFLARE_TUNNEL_ENABLED=false
PRODUCTION_URL=https://zook.yourdomain.com
DATABASE_SSL_MODE=require
JWT_SECRET_KEY=<generated-secure-key>
CORS_ORIGINS=https://zook.yourdomain.com
```

## Security Checklist

Before deploying to production:

- [ ] Generate a strong JWT_SECRET_KEY using `openssl rand -hex 32`
- [ ] Set ENVIRONMENT=production
- [ ] Set USE_HTTPS=true
- [ ] Set DATABASE_SSL_MODE=require
- [ ] Add production domain to CORS_ORIGINS
- [ ] Enable ENFORCE_HTTPS_REDIRECT=true after verifying SSL works
- [ ] Review DETECTION_CONFIDENCE_THRESHOLD for your use case
- [ ] Ensure PostgreSQL is configured for SSL connections
- [ ] Follow backend/cloudflare-tunnel-setup.md for tunnel configuration

## Testing HTTPS Locally

For local HTTPS testing with self-signed certificates:

```env
ENVIRONMENT=development
USE_HTTPS=true
ENFORCE_HTTPS_REDIRECT=false
SSL_CERT_PATH=./certs/localhost.pem
SSL_KEY_PATH=./certs/localhost-key.pem
```

Generate self-signed certificates:

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out localhost.pem -keyout localhost-key.pem -days 365 -subj "/CN=localhost"
```

