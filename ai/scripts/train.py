#!/usr/bin/env python3
"""
YOLOv11 Knife Detection Training Script

Train a custom YOLOv11 model for knife detection with target >90% mAP@0.5.

Usage:
    python train.py
    python train.py --model yolo11s --epochs 150 --batch 32
    python train.py --device 0 --imgsz 640
    python train.py --resume runs/detect/train/weights/last.pt
"""

import argparse
import torch
from pathlib import Path
from ultralytics import YOLO
import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
DATA_YAML = AI_DIR / "datasets" / "processed" / "data.yaml"
MODELS_DIR = AI_DIR / "models"
TRAINING_RUNS_DIR = MODELS_DIR / "training_runs"


def check_environment():
    """Check training environment and prerequisites."""
    print("="*60)
    print("Environment Check")
    print("="*60)
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"\n🔧 PyTorch version: {torch.__version__}")
    print(f"🔧 CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"🔧 CUDA version: {torch.version.cuda}")
        print(f"🔧 GPU device: {torch.cuda.get_device_name(0)}")
        print(f"🔧 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️  WARNING: No GPU detected! Training will be VERY slow on CPU.")
        print("   Consider using Google Colab or a cloud GPU instance.")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Check dataset
    if not DATA_YAML.exists():
        print(f"\n❌ Dataset not found: {DATA_YAML}")
        print("   Please run prepare_dataset.py first!")
        return False
    
    with open(DATA_YAML, 'r') as f:
        data_config = yaml.safe_load(f)
    
    dataset_path = Path(data_config['path'])
    train_images = list((dataset_path / data_config['train']).glob('*'))
    val_images = list((dataset_path / data_config['val']).glob('*'))
    
    print(f"\n📊 Dataset:")
    print(f"   Train images: {len(train_images)}")
    print(f"   Val images: {len(val_images)}")
    print(f"   Classes: {data_config['nc']} ({', '.join(data_config['names'])})")
    
    if len(train_images) < 50:
        print(f"\n⚠️  WARNING: Only {len(train_images)} training images!")
        print("   Recommend at least 500 images for good accuracy.")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True


def train_model(args):
    """Train YOLOv11 model."""
    print("\n" + "="*60)
    print("Starting Training")
    print("="*60)
    
    # Load model
    print(f"\n📦 Loading {args.model} model...")
    model = YOLO(f'{args.model}.pt')
    
    # Training arguments
    train_args = {
        'data': str(DATA_YAML),
        'epochs': args.epochs,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'device': args.device,
        'workers': args.workers,
        'patience': args.patience,
        'save': True,
        'cache': args.cache,
        'project': str(TRAINING_RUNS_DIR),
        'name': args.name,
        'exist_ok': args.exist_ok,
        'pretrained': True,
        'optimizer': args.optimizer,
        'lr0': args.lr0,
        'momentum': args.momentum,
        'weight_decay': args.weight_decay,
        'warmup_epochs': args.warmup_epochs,
        'val': True,
        'plots': True,
        'verbose': True,
        
        # Augmentation
        'hsv_h': args.hsv_h,
        'hsv_s': args.hsv_s,
        'hsv_v': args.hsv_v,
        'degrees': args.degrees,
        'translate': args.translate,
        'scale': args.scale,
        'shear': args.shear,
        'perspective': args.perspective,
        'flipud': args.flipud,
        'fliplr': args.fliplr,
        'mosaic': args.mosaic,
        'mixup': args.mixup,
        'copy_paste': args.copy_paste,
    }
    
    if args.resume:
        train_args['resume'] = args.resume
    
    print(f"\n📝 Training Configuration:")
    print(f"   Model: {args.model}")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch size: {args.batch}")
    print(f"   Image size: {args.imgsz}")
    print(f"   Device: {args.device}")
    print(f"   Optimizer: {args.optimizer}")
    print(f"   Learning rate: {args.lr0}")
    print(f"   Augmentation: Mosaic={args.mosaic}, Flip={args.fliplr}")
    
    print(f"\n🚀 Training started...")
    print(f"   Output: {TRAINING_RUNS_DIR / args.name}")
    print(f"   Monitor with: tensorboard --logdir {TRAINING_RUNS_DIR}")
    
    # Train
    results = model.train(**train_args)
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    
    # Print results
    print(f"\n📊 Final Metrics:")
    best_results = results.results_dict
    print(f"   mAP@0.5: {best_results.get('metrics/mAP50(B)', 0):.4f}")
    print(f"   mAP@0.5:0.95: {best_results.get('metrics/mAP50-95(B)', 0):.4f}")
    print(f"   Precision: {best_results.get('metrics/precision(B)', 0):.4f}")
    print(f"   Recall: {best_results.get('metrics/recall(B)', 0):.4f}")
    
    # Check if target achieved
    map50 = best_results.get('metrics/mAP50(B)', 0)
    if map50 >= 0.90:
        print(f"\n✅ Target achieved! mAP@0.5 = {map50:.4f} (>90%)")
    else:
        print(f"\n⚠️  Target not achieved: mAP@0.5 = {map50:.4f} (<90%)")
        print("   Consider:")
        print("   - Training for more epochs")
        print("   - Using larger model (yolo11s or yolo11m)")
        print("   - Adding more training data")
        print("   - Adjusting augmentation")
    
    # Save best model to root models directory
    best_pt = TRAINING_RUNS_DIR / args.name / "weights" / "best.pt"
    if best_pt.exists():
        import shutil
        dest = MODELS_DIR / "best.pt"
        shutil.copy2(best_pt, dest)
        print(f"\n📦 Best model saved to: {dest}")
        print(f"   Use this model in production!")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Review training plots: {TRAINING_RUNS_DIR / args.name}")
    print(f"   2. Evaluate model: python scripts/evaluate.py")
    print(f"   3. Export model: python scripts/export_model.py")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Train YOLOv11 knife detection model",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Model configuration
    parser.add_argument('--model', default='yolo11n', choices=['yolo11n', 'yolo11s', 'yolo11m', 'yolo11l', 'yolo11x'],
                       help='YOLOv11 model variant (default: yolo11n)')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='Image size for training (default: 640)')
    parser.add_argument('--device', default='0',
                       help='Device to use: 0, 1, 2, or cpu (default: 0)')
    
    # Training parameters
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs (default: 100)')
    parser.add_argument('--batch', type=int, default=16,
                       help='Batch size (default: 16)')
    parser.add_argument('--patience', type=int, default=20,
                       help='Early stopping patience (default: 20)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of data loading workers (default: 4)')
    parser.add_argument('--cache', action='store_true',
                       help='Cache images for faster training')
    
    # Optimization
    parser.add_argument('--optimizer', default='auto', choices=['SGD', 'Adam', 'AdamW', 'auto'],
                       help='Optimizer (default: auto)')
    parser.add_argument('--lr0', type=float, default=0.01,
                       help='Initial learning rate (default: 0.01)')
    parser.add_argument('--momentum', type=float, default=0.937,
                       help='SGD momentum (default: 0.937)')
    parser.add_argument('--weight_decay', type=float, default=0.0005,
                       help='Weight decay (default: 0.0005)')
    parser.add_argument('--warmup_epochs', type=float, default=3.0,
                       help='Warmup epochs (default: 3.0)')
    
    # Augmentation
    parser.add_argument('--hsv_h', type=float, default=0.015,
                       help='Hue augmentation (default: 0.015)')
    parser.add_argument('--hsv_s', type=float, default=0.7,
                       help='Saturation augmentation (default: 0.7)')
    parser.add_argument('--hsv_v', type=float, default=0.4,
                       help='Value augmentation (default: 0.4)')
    parser.add_argument('--degrees', type=float, default=10.0,
                       help='Rotation degrees (default: 10.0)')
    parser.add_argument('--translate', type=float, default=0.1,
                       help='Translation (default: 0.1)')
    parser.add_argument('--scale', type=float, default=0.5,
                       help='Scaling (default: 0.5)')
    parser.add_argument('--shear', type=float, default=0.0,
                       help='Shear (default: 0.0)')
    parser.add_argument('--perspective', type=float, default=0.0,
                       help='Perspective (default: 0.0)')
    parser.add_argument('--flipud', type=float, default=0.0,
                       help='Vertical flip probability (default: 0.0)')
    parser.add_argument('--fliplr', type=float, default=0.5,
                       help='Horizontal flip probability (default: 0.5)')
    parser.add_argument('--mosaic', type=float, default=1.0,
                       help='Mosaic augmentation probability (default: 1.0)')
    parser.add_argument('--mixup', type=float, default=0.0,
                       help='Mixup augmentation probability (default: 0.0)')
    parser.add_argument('--copy_paste', type=float, default=0.0,
                       help='Copy-paste augmentation probability (default: 0.0)')
    
    # Project management
    parser.add_argument('--name', default='knife_detection_v1',
                       help='Experiment name (default: knife_detection_v1)')
    parser.add_argument('--exist_ok', action='store_true',
                       help='Allow overwriting existing experiment')
    parser.add_argument('--resume', type=str,
                       help='Resume training from checkpoint')
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        return
    
    # Train model
    train_model(args)


if __name__ == "__main__":
    main()

