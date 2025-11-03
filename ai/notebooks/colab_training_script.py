"""
Google Colab Training Script for Custom Knife Detection

This is the Python code that goes in the Google Colab notebook.
Users can copy-paste this into Colab cells or reference it when creating the notebook.

Usage in Google Colab:
    1. Create new notebook on colab.research.google.com
    2. Copy each section below into separate cells
    3. Mark first cell as "markdown" for title
    4. Mark other cells as "code"
    5. Edit ROBOFLOW_API_KEY, WORKSPACE_NAME, PROJECT_NAME in Cell 3
    6. Runtime → Change runtime type → GPU
    7. Runtime → Run all
"""

# =============================================================================
# CELL 1: Title (Markdown Cell)
# =============================================================================
"""
# Custom Knife Detection Training - YOLOv11

Train a custom YOLOv11 model for knife detection with >90% mAP@0.5 accuracy.

**Training Time:** 2-3 hours on free Tesla T4 GPU

**Before running:**
1. Runtime → Change runtime type → GPU (T4 GPU)
2. Get Roboflow API key from https://app.roboflow.com
3. Find knife detection dataset at https://universe.roboflow.com
4. Update Cell 3 with your API key, workspace, and project name
"""

# =============================================================================
# CELL 2: Check GPU and Install Dependencies
# =============================================================================
# Check GPU
print("Checking GPU availability...")
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    print("⚠️ No GPU detected! Go to Runtime → Change runtime type → GPU")

# Install dependencies
print("\nInstalling dependencies...")
import subprocess
subprocess.check_call(["pip", "install", "-q", "ultralytics", "roboflow"])
print("✅ Installation complete!")

# =============================================================================
# CELL 3: Download Dataset (EDIT THIS CELL!)
# =============================================================================
from roboflow import Roboflow

# 🔧 EDIT THESE VALUES:
ROBOFLOW_API_KEY = "YOUR_API_KEY_HERE"  # ⬅️ Paste your API key
WORKSPACE_NAME = "your-workspace"        # ⬅️ Update workspace name
PROJECT_NAME = "knife-detection"         # ⬅️ Update project name
VERSION = 1                              # ⬅️ Update version number

print(f"Downloading dataset: {WORKSPACE_NAME}/{PROJECT_NAME} v{VERSION}")

# Download dataset
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace(WORKSPACE_NAME).project(PROJECT_NAME)
dataset = project.version(VERSION).download("yolov11")

print(f"✅ Dataset downloaded to: {dataset.location}")

# Count images
from pathlib import Path
train_images = len(list(Path(f"{dataset.location}/train/images").glob('*')))
val_images = len(list(Path(f"{dataset.location}/valid/images").glob('*')))
print(f"\n📊 Dataset: {train_images} train, {val_images} val images")

# =============================================================================
# CELL 4: Train Model
# =============================================================================
from ultralytics import YOLO

print("Starting training...")
print("This will take 2-3 hours. You can leave this tab open and check back later.")

# Load pre-trained YOLOv11n model
model = YOLO('yolo11n.pt')

# Train
results = model.train(
    data=f'{dataset.location}/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='knife_detection',
    patience=20,
    save=True,
    save_period=10,
    plots=True,
    device=0,
    workers=8,
    cache=True,
    project='runs/detect',
    exist_ok=True
)

print("✅ Training complete!")

# =============================================================================
# CELL 5: Evaluate Model
# =============================================================================
from ultralytics import YOLO

# Load best model
best_model = YOLO('runs/detect/knife_detection/weights/best.pt')

# Validate
print("Evaluating model...")
metrics = best_model.val()

# Extract metrics
map50 = metrics.box.map50
precision = metrics.box.mp
recall = metrics.box.mr

print(f"\n📊 Performance:")
print(f"   mAP@0.5: {map50:.4f} ({map50*100:.2f}%)")
print(f"   Precision: {precision:.4f} ({precision*100:.2f}%)")
print(f"   Recall: {recall:.4f} ({recall*100:.2f}%)")

if map50 >= 0.90:
    print("\n✅ SUCCESS! Model achieves >90% mAP@0.5")
else:
    print(f"\n⚠️ Model achieves {map50*100:.1f}% (target: 90%)")

# =============================================================================
# CELL 6: Download Model
# =============================================================================
from google.colab import files
import json
from datetime import datetime

# Create model info
model_info = {
    'training_date': datetime.now().isoformat(),
    'metrics': {
        'mAP@0.5': float(map50),
        'precision': float(precision),
        'recall': float(recall)
    },
    'model_type': 'custom_yolov11n',
    'classes': ['knife']
}

# Save info file
with open('runs/detect/knife_detection/weights/model_info.json', 'w') as f:
    json.dump(model_info, f, indent=2)

# Download model
print("Downloading model...")
files.download('runs/detect/knife_detection/weights/best.pt')

print("\n✅ Download complete!")
print("\nNext steps:")
print("1. Save best.pt to: YourProject/ai/models/best.pt")
print("2. Tell your assistant: 'Model is ready for deployment'")

# =============================================================================
# END OF SCRIPT
# =============================================================================

"""
NOTES FOR USERS:

1. Copy each section into separate Colab cells
2. Cell 1 should be markdown (title)
3. Cells 2-6 should be code cells
4. Edit Cell 3 with your actual values
5. Run all cells in order
6. Download best.pt when complete

TROUBLESHOOTING:

- "No GPU": Go to Runtime → Change runtime type → GPU
- "API key invalid": Check you copied full key from Roboflow
- "Dataset not found": Verify workspace and project names match exactly
- "Training stops": Colab free tier has 12-hour limit, re-run from Cell 4

AFTER TRAINING:

1. Download best.pt from Cell 6
2. Move to: YourProject/ai/models/best.pt
3. Run: python ai/scripts/deploy_model.py --model ai/models/best.pt
4. Restart backend
5. Test in browser!

For full guide, see: ai/COLAB_TRAINING_GUIDE.md
"""

