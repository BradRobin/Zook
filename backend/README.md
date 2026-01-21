# Zook Authentication Server (FastAPI)

Python/FastAPI-based authentication and session management server for the Zook AI surveillance platform.

## Features

- **User Registration** (`POST /api/auth`)
- **User Login** (`POST /api/login`) with JWT tokens
- **Session Management** - Track active sessions with device information
- **AI Threat Detection** (`POST /detect`) - YOLOv11-based knife detection
- **Stream Validation** (`POST /api/stream/validate`) for MediaMTX integration
- **Token Verification** (`GET /api/verify`)
- **Secure Password Hashing** - bcrypt with 12 rounds
- **PostgreSQL Database** - Async SQLAlchemy with proper relationships
- **CORS Support** - Configurable origins
- **HTTPS Redirect** - Production-ready security

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/zook
JWT_SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:3500,http://localhost:3000
ENVIRONMENT=development
```

**Generate a secure JWT secret key:**
```bash
openssl rand -hex 32
```

### 3. Setup Database

Make sure PostgreSQL is running, then create the database:

```bash
psql -U postgres
CREATE DATABASE zook;
\q
```

Run the migration script:

```bash
psql -U postgres -d zook -f migrations/init.sql
```

### 4. Start the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload --port 8000

# Or using Python directly
python -m app.main

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start on: `http://localhost:8000`

### 5. Test the API

Visit the interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Monitoring (Prometheus)

Prometheus metrics are exposed at `/metrics` and require an admin JWT.

Example:
```http
GET /metrics
Authorization: Bearer <admin-jwt-token>
```

Metrics can be disabled by setting `METRICS_ENABLED=false`.

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123"
}
```

#### Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "session_id": "uuid-here",
  "username": "john_doe",
  "expires_in": 86400
}
```

#### Verify Token
```http
GET /api/verify
Authorization: Bearer <your-jwt-token>

Response:
{
  "id": "uuid",
  "username": "john_doe",
  "created_at": "2025-10-24T...",
  "last_login": "2025-10-24T..."
}
```

#### Logout
```http
POST /api/logout
Authorization: Bearer <your-jwt-token>

Response:
{
  "message": "Logged out successfully"
}
```

### AI Threat Detection

#### Detect Threats in Image
```http
POST /detect
Authorization: Bearer <your-jwt-token>
Content-Type: multipart/form-data

Form Data:
  image: <JPEG file>

Response (threat detected):
{
  "threats": [
    {
      "type": "knife",
      "confidence": 0.95,
      "bbox": {
        "x1": 120.5,
        "y1": 200.3,
        "x2": 250.8,
        "y2": 400.1
      }
    }
  ],
  "processing_time_ms": 25.3
}

Response (no threat):
{
  "threats": [],
  "processing_time_ms": 18.7
}
```

**Detection Specifications:**
- Model: YOLOv11n (nano variant for speed)
- Input: JPEG images, automatically resized to 640x640
- Target class: Knife (COCO class ID 43)
- Confidence threshold: 90% (0.90)
- Performance: <30ms per frame on mid-tier GPU, ~100-200ms on CPU

**Testing the Endpoint:**
```bash
# Using curl
curl -X POST "http://localhost:8000/detect" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "image=@tests/sample_images/knife.jpg"

# Using the test script
python test_detection.py
```

#### Check Detection Service Health
```http
GET /detect/health

Response:
{
  "status": "healthy",
  "service": "threat_detection",
  "model_info": {
    "model_type": "pretrained",
    "device": "cpu",
    "confidence_threshold": 0.90,
    "target_classes": ["knife"],
    "input_size": "640x640",
    "architecture": "YOLOv11n"
  }
}
```

#### Update Detection Threshold
```http
POST /detect/threshold?threshold=0.85
Authorization: Bearer <your-jwt-token>

Response:
{
  "message": "Threshold updated successfully",
  "new_threshold": 0.85
}
```

### Stream Validation (MediaMTX)

#### Validate Stream Access
```http
POST /api/stream/validate
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "action": "read",
  "protocol": "webrtc",
  "path": "/mystream"
}

Response:
{
  "authorized": true,
  "user_id": "uuid",
  "username": "john_doe",
  "message": "Stream access granted"
}
```

## Database Schema

### Users Table
- `id` - UUID primary key
- `username` - Unique username
- `password_hash` - bcrypt hashed password
- `created_at` - Registration timestamp
- `last_login` - Last login timestamp

### Sessions Table
- `id` - UUID primary key
- `user_id` - Foreign key to users
- `session_token` - JWT token
- `created_at` - Session creation time
- `expires_at` - Expiration time
- `is_active` - Active status
- `ip_address` - Client IP
- `user_agent` - Browser/client info
- `last_activity` - Last activity timestamp
- `device_info` - Additional device metadata

## Security Features

1. **Password Hashing**: bcrypt with 12 rounds (4096 iterations)
2. **JWT Tokens**: HS256 algorithm with 24-hour expiry
3. **Session Tracking**: Active session management with device info
4. **CORS Protection**: Configurable allowed origins
5. **HTTPS Redirect**: Automatic redirect in production
6. **Input Validation**: Pydantic schemas for all requests
7. **SQL Injection Protection**: SQLAlchemy parameterized queries

## YOLOv11 Detection System

### Model Information

The detection system uses **YOLOv11** from Ultralytics for real-time threat detection:

- **Architecture**: YOLOv11n (lightweight) or YOLOv11s (balanced)
- **Training Data**: COCO dataset (pretrained) OR Custom trained model
- **Target Class**: Knife (COCO class ID 43)
- **Input Size**: 640x640 RGB images
- **Confidence Threshold**: 0.90 (90%)
- **Performance Target**: <30ms per frame on mid-tier GPU

### Model Options

**Option 1: COCO Pretrained (Default)**
- Out-of-the-box functionality
- ~65% mAP on knife detection
- Good for initial testing
- No training required

**Option 2: Custom Trained Model (Recommended)**
- >90% mAP on knife detection
- Better accuracy for your specific use case
- Trained on 1000+ knife images
- See `../ai/README.md` for training guide

The backend automatically loads custom model if present at `app/models/custom_knife_model.pt`!

### Custom Model Training

For improved accuracy (>90% mAP), train a custom YOLOv11 model:

**📚 Complete Training Guide**: See [`../ai/README.md`](../ai/README.md)

**Quick Start**: See [`../ai/QUICKSTART.md`](../ai/QUICKSTART.md) for 15-minute setup

The `ai/` directory contains a complete training pipeline:

**Training Steps:**

```bash
# 1. Install dependencies
cd ../ai
pip install -r requirements.txt

# 2. Download dataset (Roboflow, Kaggle, or manual)
python scripts/download_datasets.py --source roboflow \
    --workspace "workspace" --project "knife-detection" \
    --version 1 --api-key "YOUR_KEY"

# 3. Prepare dataset (validate, clean, split)
python scripts/prepare_dataset.py

# 4. Train model (2-4 hours on GPU)
python scripts/train.py --model yolo11s --epochs 150 --cache

# 5. Evaluate performance
python scripts/evaluate.py

# 6. Export and deploy to backend
python scripts/export_model.py --deploy

# 7. Restart backend - custom model loads automatically!
cd ../backend
uvicorn app.main:app --reload
```

**Features:**
- ✅ Automated dataset download (Roboflow, Kaggle)
- ✅ Data validation and cleaning
- ✅ Training with full augmentation pipeline
- ✅ Comprehensive evaluation metrics
- ✅ Multi-format export (PyTorch, ONNX, TensorRT)
- ✅ One-command deployment to backend

**Expected Results:**
- >90% mAP@0.5 on custom knife dataset
- 15-25ms inference time on GPU
- 27%+ improvement over COCO baseline

For complete documentation, see [`../ai/README.md`](../ai/README.md)

### Performance Benchmarks

Target performance on different hardware:

| Hardware | Average Latency | Throughput |
|----------|----------------|------------|
| RTX 3060 (GPU) | 15-25ms | ~40-60 FPS |
| GTX 1660 (GPU) | 20-30ms | ~33-50 FPS |
| CPU (8 cores) | 100-200ms | ~5-10 FPS |
| Raspberry Pi 4 | 500-1000ms | ~1-2 FPS |

**Optimization Tips:**
- Use GPU for production (CUDA-enabled)
- Consider YOLOv11n for speed vs YOLOv11s/m for accuracy
- Batch processing for multiple cameras (not yet implemented)
- TensorRT optimization for NVIDIA GPUs (advanced)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Database connection setup
│   ├── models.py            # SQLAlchemy models (DB)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── auth.py              # JWT utilities
│   ├── security.py          # Password hashing
│   ├── models/              # YOLO model storage
│   │   ├── .gitkeep
│   │   └── custom_knife_model.pt  # (optional) Custom trained model
│   ├── services/
│   │   ├── __init__.py
│   │   └── detector.py      # YOLOv11 detection service
│   └── routers/
│       ├── __init__.py
│       ├── auth_routes.py   # Authentication endpoints
│       ├── stream_routes.py # Stream validation endpoints
│       └── detection_routes.py  # Threat detection endpoints
├── tests/
│   └── sample_images/       # Test images for validation
│       └── README.md
├── migrations/
│   └── init.sql             # Database schema
├── requirements.txt
├── test_detection.py        # Detection endpoint test script
├── Dockerfile
├── .dockerignore
├── .env.example
└── README.md
```

## Development

### Running Tests

#### Authentication Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

#### Detection Tests
```bash
# Test detection endpoint with sample images
python test_detection.py

# Test specific image
python test_detection.py --image tests/sample_images/knife.jpg

# Test against remote server
python test_detection.py --url https://your-server.com

# See all options
python test_detection.py --help
```

### Code Formatting
```bash
pip install black isort
black app/
isort app/
```

### Type Checking
```bash
pip install mypy
mypy app/
```

## Deployment

### Docker (Recommended)

#### Build and Run
```bash
# Build Docker image
cd backend
docker build -t zook-backend:latest .

# Run container (CPU)
docker run -d \
  --name zook-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/zook" \
  -e JWT_SECRET_KEY="your-secret-key" \
  zook-backend:latest

# Run container (with GPU support)
docker run -d \
  --name zook-backend \
  --gpus all \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/zook" \
  -e JWT_SECRET_KEY="your-secret-key" \
  zook-backend:latest

# Check logs
docker logs -f zook-backend

# Stop container
docker stop zook-backend
```

#### Using Custom Model in Docker
```bash
# Build with custom model
docker build -t zook-backend:custom .

# Or mount custom model as volume
docker run -d \
  --name zook-backend \
  -p 8000:8000 \
  -v /path/to/custom_knife_model.pt:/app/app/models/custom_knife_model.pt \
  zook-backend:latest
```

### Environment Variables for Production
- Set `ENVIRONMENT=production`
- Use strong `JWT_SECRET_KEY`
- Configure proper `CORS_ORIGINS`
- Use connection pooling for database
- Enable HTTPS

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check `DATABASE_URL` format
- Verify database exists: `psql -U postgres -l`

### Token Validation Errors
- Check JWT_SECRET_KEY matches between sessions
- Verify token hasn't expired (24 hours)
- Ensure proper Authorization header: `Bearer <token>`

### CORS Errors
- Add frontend URL to `CORS_ORIGINS` in `.env`
- Check browser console for specific CORS error

### Detection Service Issues

#### Model Download Fails
- Ensure internet connection (first run downloads YOLOv11n ~6MB)
- Model cached in `~/.cache/ultralytics/`
- Manually download: `yolo checks`

#### Slow Detection Performance
- Check device: Look for "Model loaded on device: cpu" in logs
- For GPU: Install PyTorch with CUDA support
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  ```
- Verify GPU: `python -c "import torch; print(torch.cuda.is_available())"`

#### Low Accuracy
- Default COCO model may not be optimized for your environment
- Consider training custom model (see Custom Model Training section)
- Adjust confidence threshold: `POST /detect/threshold?threshold=0.85`

#### Memory Issues
- YOLOv11n uses ~100-200MB RAM
- Reduce batch size if processing multiple images
- Consider model quantization for embedded devices

## License

Part of the Zook project - Open-source foundation

## Contact

For issues and questions, refer to the main Zook project documentation.


