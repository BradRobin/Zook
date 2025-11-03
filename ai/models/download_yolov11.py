#!/usr/bin/env python3
"""Quick script to download YOLOv11n model."""
import urllib.request
import sys
from pathlib import Path

MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov11n.pt"
OUTPUT_FILE = "yolov11n.pt"

print("Downloading YOLOv11n model...")
print(f"From: {MODEL_URL}")
print(f"To: {OUTPUT_FILE}")

try:
    urllib.request.urlretrieve(MODEL_URL, OUTPUT_FILE)
    file_size = Path(OUTPUT_FILE).stat().st_size / (1024 * 1024)
    print(f"\n✅ Download complete!")
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Size: {file_size:.2f} MB")
    print(f"\nNext: Rename to best.pt")
    print(f"   Run: python deploy_this_model.py")
except Exception as e:
    print(f"\n❌ Download failed: {e}")
    print("\nManual download:")
    print(f"1. Open: {MODEL_URL}")
    print(f"2. Save as: {OUTPUT_FILE}")
    sys.exit(1)


