#!/usr/bin/env python3
"""
Local training script for knife detection.

Trains YOLOv11n model on your local machine (CPU).
Expected time: 12-24 hours on CPU for 100 epochs.

Usage:
    python train_local.py
    python train_local.py --epochs 50  # Faster but lower accuracy
    python train_local.py --resume  # Resume from last checkpoint
"""

import argparse
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from ultralytics import YOLO
    from roboflow import Roboflow
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nInstall dependencies:")
    print("  cd ai")
    print("  pip install -r requirements.txt")
    sys.exit(1)

# Configuration
API_KEY = "ss5l2EPlTz7MtYfpYsvn"
WORKSPACE = "weapon-rcjrw"
PROJECT = "weapon-detection-pgqnr"
VERSION = 8

SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
DATASET_DIR = AI_DIR / "datasets" / "downloaded"
MODELS_DIR = AI_DIR / "models"
TRAINING_DIR = MODELS_DIR / "training_runs"


def download_dataset():
    """Download dataset from Roboflow if not already present."""
    print("="*70)
    print("Step 1: Download Dataset")
    print("="*70)
    
    dataset_path = DATASET_DIR / f"{PROJECT}-{VERSION}"
    
    if dataset_path.exists():
        print(f"\n✅ Dataset already downloaded: {dataset_path}")
        response = input("   Re-download? (y/n): ")
        if response.lower() != 'y':
            return dataset_path
    
    print(f"\n📥 Downloading from Roboflow...")
    print(f"   Workspace: {WORKSPACE}")
    print(f"   Project: {PROJECT}")
    print(f"   Version: {VERSION}")
    
    try:
        rf = Roboflow(api_key=API_KEY)
        project_obj = rf.workspace(WORKSPACE).project(PROJECT)
        dataset = project_obj.version(VERSION).download(
            "yolov11",
            location=str(DATASET_DIR)
        )
        
        print(f"\n✅ Dataset downloaded!")
        print(f"   Location: {dataset.location}")
        
        # Count images
        train_images = len(list(Path(f"{dataset.location}/train/images").glob('*')))
        val_images = len(list(Path(f"{dataset.location}/valid/images").glob('*')))
        
        print(f"\n📊 Dataset size:")
        print(f"   Train: {train_images} images")
        print(f"   Val: {val_images} images")
        
        return Path(dataset.location)
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)


def train_model(dataset_path: Path, epochs: int = 100, resume: bool = False):
    """Train YOLOv11n model."""
    print("\n" + "="*70)
    print("Step 2: Train Model")
    print("="*70)
    
    # Find data.yaml
    data_yaml = dataset_path / "data.yaml"
    if not data_yaml.exists():
        print(f"❌ data.yaml not found at {data_yaml}")
        sys.exit(1)
    
    print(f"\n📄 Dataset config: {data_yaml}")
    print(f"⏱️  Training time estimate: {epochs * 8} - {epochs * 15} minutes")
    print(f"   (That's {epochs * 8 / 60:.1f} - {epochs * 15 / 60:.1f} hours)")
    
    print("\n⚠️  IMPORTANT: This will run on CPU (slow!)")
    print("   - Leave your computer running")
    print("   - Best to run overnight")
    print("   - Don't close this terminal")
    
    response = input("\n   Ready to start training? (y/n): ")
    if response.lower() != 'y':
        print("Training cancelled.")
        return
    
    print("\n🚀 Starting training...")
    print("="*70)
    
    try:
        # Load model
        if resume:
            # Try to resume from last checkpoint
            last_checkpoint = TRAINING_DIR / "knife_detection" / "weights" / "last.pt"
            if last_checkpoint.exists():
                print(f"📂 Resuming from: {last_checkpoint}")
                model = YOLO(str(last_checkpoint))
            else:
                print("⚠️  No checkpoint found, starting fresh")
                model = YOLO('yolo11n.pt')
        else:
            model = YOLO('yolo11n.pt')
        
        # Train
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=640,
            batch=8,  # Smaller batch for CPU
            name='knife_detection',
            patience=30,  # More patience for CPU training
            save=True,
            save_period=10,  # Save every 10 epochs
            plots=True,
            device='cpu',  # Force CPU
            workers=4,  # Fewer workers for CPU
            project=str(TRAINING_DIR),
            exist_ok=True,
            # Augmentation
            mosaic=1.0,
            mixup=0.1,
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            flipud=0.0,
            fliplr=0.5,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4
        )
        
        print("\n" + "="*70)
        print("✅ Training Complete!")
        print("="*70)
        
        best_model_path = TRAINING_DIR / "knife_detection" / "weights" / "best.pt"
        print(f"\n📦 Best model saved to:")
        print(f"   {best_model_path}")
        
        # Evaluate
        print("\n📊 Final Evaluation:")
        model = YOLO(str(best_model_path))
        metrics = model.val()
        
        map50 = metrics.box.map50
        precision = metrics.box.mp
        recall = metrics.box.mr
        
        print(f"\n   mAP@0.5: {map50:.4f} ({map50*100:.2f}%)")
        print(f"   Precision: {precision:.4f} ({precision*100:.2f}%)")
        print(f"   Recall: {recall:.4f} ({recall*100:.2f}%)")
        
        if map50 >= 0.90:
            print("\n🎉 SUCCESS! Model achieves >90% mAP@0.5")
        elif map50 >= 0.85:
            print(f"\n⚠️  Close! Model achieves {map50*100:.1f}% (target: 90%)")
            print("   Consider training for more epochs")
        else:
            print(f"\n❌ Model achieves {map50*100:.1f}% (target: 90%)")
            print("   May need more training or better dataset")
        
        print("\n📋 Next steps:")
        print("   1. Deploy: python scripts/deploy_model.py --auto")
        print("   2. Restart backend")
        print("   3. Test detection in browser")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted!")
        print("   Your progress is saved.")
        print("   Resume with: python train_local.py --resume")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Train knife detection model locally")
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs (default: 100)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick training (50 epochs, faster but less accurate)'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        args.epochs = 50
        print("⚡ Quick training mode: 50 epochs (~6-12 hours)")
    
    print("="*70)
    print("Local Knife Detection Training")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"   Epochs: {args.epochs}")
    print(f"   Device: CPU")
    print(f"   Resume: {args.resume}")
    print(f"   Estimated time: {args.epochs * 8 / 60:.1f} - {args.epochs * 15 / 60:.1f} hours")
    
    # Step 1: Download dataset
    dataset_path = download_dataset()
    
    # Step 2: Train model
    train_model(dataset_path, args.epochs, args.resume)


if __name__ == '__main__':
    main()


