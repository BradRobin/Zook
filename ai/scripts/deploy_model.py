#!/usr/bin/env python3
"""
Deploy trained custom knife detection model to backend.

This script:
1. Validates the trained model
2. Tests inference
3. Copies model to backend directory
4. Creates model metadata file
5. Updates configuration

Usage:
    python deploy_model.py --model path/to/best.pt
    python deploy_model.py --auto  # Auto-detect from training runs
    python deploy_model.py --model ../models/best.pt --test
"""

import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime
import sys

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from ultralytics import YOLO
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install ultralytics pillow numpy")
    sys.exit(1)

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
BACKEND_DIR = AI_DIR.parent / "backend"
TARGET_MODEL_DIR = BACKEND_DIR / "app" / "models"
TARGET_MODEL_PATH = TARGET_MODEL_DIR / "custom_knife_model.pt"


def find_latest_training():
    """Find the most recent training run."""
    training_runs = AI_DIR / "models" / "training_runs"
    
    if not training_runs.exists():
        return None
    
    # Look for runs/detect/*/weights/best.pt pattern
    best_models = list(training_runs.glob("**/weights/best.pt"))
    
    if not best_models:
        return None
    
    # Return most recently modified
    return max(best_models, key=lambda p: p.stat().st_mtime)


def validate_model(model_path: Path) -> dict:
    """
    Validate that the model can be loaded and run inference.
    
    Args:
        model_path: Path to model file
        
    Returns:
        Dictionary with validation results
        
    Raises:
        Exception if model is invalid
    """
    print("\n" + "="*60)
    print("Model Validation")
    print("="*60)
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    file_size = model_path.stat().st_size / (1024 * 1024)
    print(f"\n📁 Model file: {model_path}")
    print(f"   Size: {file_size:.2f} MB")
    
    # Load model
    print("\n🔄 Loading model...")
    try:
        model = YOLO(str(model_path))
        print("✅ Model loaded successfully")
    except Exception as e:
        raise Exception(f"Failed to load model: {e}")
    
    # Check model info
    model_info = {
        'names': model.names,
        'task': model.task,
    }
    
    print(f"\n📊 Model Info:")
    print(f"   Task: {model_info['task']}")
    print(f"   Classes: {len(model_info['names'])}")
    print(f"   Class names: {list(model_info['names'].values())}")
    
    # Verify it's a knife detection model
    class_names = list(model_info['names'].values())
    if 'knife' not in [name.lower() for name in class_names]:
        print("\n⚠️  WARNING: Model does not have 'knife' class!")
        print(f"   Found classes: {class_names}")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            raise Exception("Model validation failed: no knife class")
    
    return model_info


def test_inference(model_path: Path) -> dict:
    """
    Test model inference speed and basic functionality.
    
    Args:
        model_path: Path to model file
        
    Returns:
        Dictionary with inference stats
    """
    print("\n" + "="*60)
    print("Inference Testing")
    print("="*60)
    
    # Load model
    model = YOLO(str(model_path))
    
    # Create test image (random noise)
    print("\n🧪 Creating test image...")
    test_image = Image.fromarray(
        np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    )
    
    # Warmup
    print("🔥 Warming up model...")
    for _ in range(3):
        model.predict(test_image, verbose=False)
    
    # Benchmark
    print("⏱️  Running benchmark (10 iterations)...")
    import time
    times = []
    for _ in range(10):
        start = time.time()
        results = model.predict(test_image, conf=0.9, verbose=False)
        times.append((time.time() - start) * 1000)  # Convert to ms
    
    stats = {
        'mean_ms': np.mean(times),
        'median_ms': np.median(times),
        'min_ms': np.min(times),
        'max_ms': np.max(times),
        'std_ms': np.std(times)
    }
    
    print(f"\n📈 Inference Performance:")
    print(f"   Mean: {stats['mean_ms']:.2f} ms")
    print(f"   Median: {stats['median_ms']:.2f} ms")
    print(f"   Min: {stats['min_ms']:.2f} ms")
    print(f"   Max: {stats['max_ms']:.2f} ms")
    print(f"   Std Dev: {stats['std_ms']:.2f} ms")
    
    if stats['mean_ms'] > 200:
        print(f"\n⚠️  WARNING: Inference is slow ({stats['mean_ms']:.0f}ms)")
        print("   Consider using smaller model or GPU")
    elif stats['mean_ms'] < 100:
        print("\n✅ Excellent inference speed!")
    else:
        print("\n✅ Good inference speed")
    
    return stats


def deploy_model(source_path: Path, target_path: Path, model_info: dict, inference_stats: dict):
    """
    Deploy model to backend directory.
    
    Args:
        source_path: Source model file
        target_path: Target deployment location
        model_info: Model information dictionary
        inference_stats: Inference performance stats
    """
    print("\n" + "="*60)
    print("Model Deployment")
    print("="*60)
    
    # Create target directory
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy model
    print(f"\n📦 Copying model to backend...")
    print(f"   From: {source_path}")
    print(f"   To: {target_path}")
    
    shutil.copy2(source_path, target_path)
    print("✅ Model copied successfully")
    
    # Create model info file
    info_path = target_path.with_suffix('.json')
    metadata = {
        'deployment_date': datetime.utcnow().isoformat(),
        'source_path': str(source_path),
        'model_info': model_info,
        'inference_stats': inference_stats,
        'model_type': 'custom_yolov11n',
        'version': '1.0'
    }
    
    print(f"\n📝 Creating metadata file...")
    print(f"   Path: {info_path}")
    
    with open(info_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Metadata saved")
    
    # Update .env if needed
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        print(f"\n⚙️  Checking .env configuration...")
        
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        if 'USE_CUSTOM_MODEL' not in env_content:
            print("   Adding USE_CUSTOM_MODEL=true to .env")
            with open(env_path, 'a') as f:
                f.write('\n# Custom Model Configuration\n')
                f.write('USE_CUSTOM_MODEL=true\n')
                f.write(f'CUSTOM_MODEL_PATH=app/models/{target_path.name}\n')
            print("✅ .env updated")
        else:
            print("✅ .env already configured")
    
    print("\n" + "="*60)
    print("✅ Deployment Complete!")
    print("="*60)
    print(f"\nModel deployed to: {target_path}")
    print(f"Metadata saved to: {info_path}")
    print("\n📌 Next Steps:")
    print("   1. Restart backend server")
    print("   2. Check logs for 'Custom model loaded'")
    print("   3. Test detection in browser")
    print("\nRestart backend with:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload\n")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy trained knife detection model to backend"
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Path to trained model (best.pt)'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto-detect latest training run'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run inference test before deployment'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip model validation (not recommended)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Custom Model Deployment Script")
    print("="*60)
    
    # Determine source model path
    if args.auto:
        print("\n🔍 Auto-detecting latest training run...")
        model_path = find_latest_training()
        if not model_path:
            print("❌ No training runs found in ai/models/training_runs/")
            print("   Use --model to specify path manually")
            sys.exit(1)
        print(f"✅ Found: {model_path}")
    elif args.model:
        model_path = Path(args.model)
        if not model_path.is_absolute():
            model_path = Path.cwd() / model_path
    else:
        # Interactive mode
        print("\n📁 Available options:")
        print("   1. Specify model path")
        print("   2. Auto-detect latest training")
        choice = input("\nSelect option (1 or 2): ")
        
        if choice == '2':
            model_path = find_latest_training()
            if not model_path:
                print("❌ No training runs found")
                sys.exit(1)
        else:
            model_str = input("Enter path to model file: ")
            model_path = Path(model_str)
            if not model_path.is_absolute():
                model_path = Path.cwd() / model_path
    
    # Validate model exists
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        sys.exit(1)
    
    try:
        # Validate model
        if not args.skip_validation:
            model_info = validate_model(model_path)
        else:
            model_info = {'names': {0: 'knife'}, 'task': 'detect'}
            print("⚠️  Skipping validation (not recommended)")
        
        # Test inference
        if args.test or not args.skip_validation:
            inference_stats = test_inference(model_path)
        else:
            inference_stats = {}
        
        # Deploy
        print(f"\n❓ Deploy model to backend?")
        print(f"   Source: {model_path}")
        print(f"   Target: {TARGET_MODEL_PATH}")
        
        response = input("\nProceed? (y/n): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            sys.exit(0)
        
        deploy_model(model_path, TARGET_MODEL_PATH, model_info, inference_stats)
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

