# YOLOv11 Detection Service - Quick Setup Guide

This guide will help you get the YOLOv11 threat detection service up and running.

## Prerequisites

- Python 3.11+
- PostgreSQL (already configured)
- 4GB+ RAM (8GB recommended for GPU)
- Optional: CUDA-capable GPU for better performance

## Installation Steps

### 1. Install New Dependencies

```bash
cd backend

# Activate virtual environment if not already active
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install new packages (YOLOv11, PyTorch, OpenCV, etc.)
pip install -r requirements.txt
```

**Note**: This will download PyTorch (~2GB) and other dependencies. First-time installation may take 5-10 minutes.

### 2. Verify Installation

```bash
# Check if ultralytics is installed
python -c "import ultralytics; print(ultralytics.__version__)"

# Check PyTorch and GPU availability
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 3. Test Model Loading

```bash
# This will download YOLOv11n model (~6MB) on first run
python -c "from ultralytics import YOLO; model = YOLO('yolo11n.pt'); print('Model loaded successfully!')"
```

The model will be cached in `~/.cache/ultralytics/` for future use.

### 4. Start the Server

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Watch the startup logs for:
```
INFO:     Initializing YOLOv11 threat detection model...
INFO:     Loading pretrained YOLOv11n model from Ultralytics
INFO:     Model loaded on device: cpu
INFO:     Warming up model...
INFO:     Model warmup completed
INFO:     Detection model initialized and ready
```

### 5. Test the Detection Endpoint

#### Using curl:
```bash
# Get JWT token first
TOKEN=$(curl -s -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"Brad","password":"12345678"}' | jq -r '.access_token')

# Test with an image
curl -X POST "http://localhost:8000/detect" \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/test_image.jpg"
```

#### Using the test script:
```bash
# Test with sample images
python test_detection.py

# Check service health
curl http://localhost:8000/detect/health
```

## GPU Support (Optional but Recommended)

For significantly faster detection (<30ms vs ~100-200ms):

### Install CUDA Toolkit

1. Check your NVIDIA GPU: `nvidia-smi`
2. Install CUDA Toolkit 11.8 or 12.1 from [NVIDIA website](https://developer.nvidia.com/cuda-downloads)

### Install PyTorch with CUDA

```bash
# Uninstall CPU-only PyTorch
pip uninstall torch torchvision

# Install CUDA-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Verify GPU Setup

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

### Update Detector to Use GPU

Edit `backend/app/main.py`, line 40:
```python
# Change from:
detector = get_detector(confidence_threshold=0.90, device='cpu')

# To:
detector = get_detector(confidence_threshold=0.90, device='cuda')
```

Restart the server and check logs for "Model loaded on device: cuda".

## Docker Deployment

### Build Image

```bash
cd backend
docker build -t zook-backend:latest .
```

### Run Container (CPU)

```bash
docker run -d \
  --name zook-backend \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/zook" \
  -e JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  -e CORS_ORIGINS="http://localhost:3500" \
  zook-backend:latest
```

### Run Container (GPU)

```bash
# Requires nvidia-docker runtime
docker run -d \
  --name zook-backend \
  --gpus all \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/zook" \
  -e JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  -e CORS_ORIGINS="http://localhost:3500" \
  zook-backend:latest
```

## Testing the Full Stack

1. **Start backend**: `uvicorn app.main:app --reload --port 8000`
2. **Start frontend**: `cd ui/src && python -m http.server 3500`
3. **Open browser**: http://localhost:3500
4. **Login**: Username: `Brad`, Password: `12345678`
5. **Allow camera access** when prompted
6. **Watch for detections**: Every 5 seconds, a frame is sent to the detection endpoint

The frontend is already configured to use the `/detect` endpoint!

## Troubleshooting

### "No module named 'ultralytics'"
```bash
pip install ultralytics>=8.3.0
```

### "Model download failed"
- Check internet connection
- Manually download: `yolo checks`
- Firewall may be blocking downloads

### "CUDA out of memory"
- YOLOv11n uses ~500MB GPU memory
- Close other GPU applications
- Use CPU if GPU memory insufficient

### "Detection too slow (>200ms)"
- Confirm GPU is being used: Check logs for "device: cuda"
- Install CUDA-enabled PyTorch (see GPU Support section)
- Consider using YOLOv11n (fastest) vs YOLOv11s/m

### Frontend not showing detections
- Open browser console (F12) and check for errors
- Verify backend is running: http://localhost:8000/health
- Check detection service: http://localhost:8000/detect/health
- Ensure token is valid: Check localStorage for 'zook_auth_token'

## Performance Expectations

| Setup | Detection Latency | Notes |
|-------|------------------|-------|
| CPU (modern 8-core) | 100-200ms | Acceptable for 5s intervals |
| GPU (GTX 1660+) | 20-30ms | Real-time capable |
| GPU (RTX 3060+) | 15-25ms | Optimal performance |

## Next Steps

1. ✅ Basic detection working with COCO pretrained model
2. 🔄 Collect knife images for custom training
3. 🔄 Train custom model for improved accuracy
4. 🔄 Deploy custom model to production
5. 🔄 Add visualization of bounding boxes in frontend
6. 🔄 Implement alert notifications (email/SMS)

## Custom Model Training (Advanced)

See `backend/README.md` section "Custom Model Training" for detailed instructions on training a custom YOLOv11 model for knife detection with higher accuracy.

## Additional Resources

- [Ultralytics YOLOv11 Docs](https://docs.ultralytics.com/)
- [PyTorch Installation](https://pytorch.org/get-started/locally/)
- [CUDA Toolkit Download](https://developer.nvidia.com/cuda-downloads)
- [YOLOv11 Model Zoo](https://github.com/ultralytics/ultralytics)

## Support

For issues or questions:
1. Check `backend/README.md` troubleshooting section
2. Review server logs: `docker logs zook-backend` or console output
3. Test endpoint with `python test_detection.py --image /path/to/test.jpg`

