# Dockerfile for Zook Backend with YOLOv11 Detection Service
# Base image: Python 3.11 slim for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for OpenCV and image processing
# libgl1: OpenCV dependency for image operations
# libglib2.0-0: Required for cv2
# libsm6, libxext6, libxrender-dev: Additional OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# This may take a while due to PyTorch download
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory for custom YOLO models
RUN mkdir -p /app/app/models

# Expose port 8000 for FastAPI
EXPOSE 8000

# Health check to ensure service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run uvicorn server
# --host 0.0.0.0: Listen on all network interfaces
# --port 8000: Default port
# --workers 1: Single worker (model loading is memory intensive)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

