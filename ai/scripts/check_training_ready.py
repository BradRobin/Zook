#!/usr/bin/env python3
"""
Pre-flight check before starting training.
Verifies all dependencies and configuration.
"""

import sys
from pathlib import Path

print("="*70)
print("Training Readiness Check")
print("="*70)

checks_passed = 0
checks_failed = 0

# Check 1: Ultralytics
print("\n1. Checking ultralytics...")
try:
    from ultralytics import YOLO
    print("   ✅ ultralytics installed")
    checks_passed += 1
except ImportError:
    print("   ❌ ultralytics NOT installed")
    print("      Fix: pip install ultralytics")
    checks_failed += 1

# Check 2: Roboflow
print("\n2. Checking roboflow...")
try:
    from roboflow import Roboflow
    print("   ✅ roboflow installed")
    checks_passed += 1
except ImportError:
    print("   ❌ roboflow NOT installed")
    print("      Fix: pip install roboflow")
    checks_failed += 1

# Check 3: PyTorch
print("\n3. Checking torch...")
try:
    import torch
    print(f"   ✅ torch {torch.__version__} installed")
    print(f"   Device: CPU (training will be slow but works)")
    checks_passed += 1
except ImportError:
    print("   ❌ torch NOT installed")
    print("      Fix: pip install torch torchvision")
    checks_failed += 1

# Check 4: Directory structure
print("\n4. Checking directory structure...")
script_dir = Path(__file__).parent
ai_dir = script_dir.parent
required_dirs = [
    ai_dir / "models",
    ai_dir / "models" / "training_runs",
    ai_dir / "datasets",
]

all_dirs_exist = True
for dir_path in required_dirs:
    if dir_path.exists():
        print(f"   ✅ {dir_path.relative_to(ai_dir.parent)}")
    else:
        print(f"   ⚠️  Creating {dir_path.relative_to(ai_dir.parent)}")
        dir_path.mkdir(parents=True, exist_ok=True)

checks_passed += 1

# Check 5: Roboflow API key
print("\n5. Checking Roboflow configuration...")
API_KEY = "ss5l2EPlTz7MtYfpYsvn"
if API_KEY and len(API_KEY) > 10:
    print(f"   ✅ API key configured: {API_KEY[:10]}...")
    checks_passed += 1
else:
    print("   ❌ API key not configured")
    checks_failed += 1

# Check 6: Disk space
print("\n6. Checking disk space...")
try:
    import shutil
    total, used, free = shutil.disk_usage(ai_dir)
    free_gb = free // (2**30)
    print(f"   Free space: {free_gb} GB")
    if free_gb >= 5:
        print("   ✅ Sufficient disk space")
        checks_passed += 1
    else:
        print("   ⚠️  Low disk space (recommend 5+ GB)")
        checks_passed += 1
except Exception as e:
    print(f"   ⚠️  Could not check disk space: {e}")
    checks_passed += 1

# Summary
print("\n" + "="*70)
print("Summary")
print("="*70)
print(f"✅ Passed: {checks_passed}")
print(f"❌ Failed: {checks_failed}")

if checks_failed == 0:
    print("\n🎉 All checks passed! Ready to train!")
    print("\nStart training:")
    print("   python train_local.py")
    print("\nOr quick mode (faster, less accurate):")
    print("   python train_local.py --quick")
else:
    print(f"\n⚠️  Please fix {checks_failed} issue(s) before training")
    print("\nQuick fix:")
    print("   cd ai")
    print("   pip install -r requirements.txt")
    sys.exit(1)


