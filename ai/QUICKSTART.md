# Quick Start Guide - Custom Knife Detection Training

**Get started training a custom YOLOv11 model in 15 minutes!**

## 📋 Prerequisites

- Python 3.11+
- NVIDIA GPU (recommended) or CPU
- 10GB+ free disk space

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies (5 minutes)

```bash
cd ai
pip install -r requirements.txt
```

**First time setup downloads ~2-3GB of PyTorch and dependencies.**

### Step 2: Download Dataset (5 minutes)

**Option A: Roboflow (Easiest)**

1. Create free account at [Roboflow](https://app.roboflow.com/)
2. Find a knife detection dataset on [Universe](https://universe.roboflow.com/search?q=knife)
3. Get your API key from Account Settings
4. Download:

```bash
python scripts/download_datasets.py --source roboflow \
    --workspace "workspace-name" \
    --project "knife-detection" \
    --version 1 \
    --api-key "YOUR_API_KEY"
```

**Option B: Kaggle**

1. Setup Kaggle API credentials: https://www.kaggle.com/docs/api
2. Find dataset: https://www.kaggle.com/search?q=knife+detection
3. Download:

```bash
python scripts/download_datasets.py --source kaggle \
    --dataset "username/knife-detection"
```

**Option C: Manual Download**

1. Download from [Roboflow Universe](https://universe.roboflow.com/search?q=knife)
2. Choose YOLO format export
3. Extract to `datasets/raw/your_dataset_name/`

### Step 3: Prepare Dataset (2 minutes)

```bash
python scripts/prepare_dataset.py
```

This will:
- Validate all images
- Remove duplicates
- Split train/val/test (70/20/10)
- Create `datasets/processed/data.yaml`

Expected output:
```
✅ Processed 1200 images
   Valid pairs: 1150
   Train: 805 images
   Val: 230 images
   Test: 115 images
```

### Step 4: Train Model (2-4 hours)

**Quick Training (YOLOv11n - fastest):**
```bash
python scripts/train.py
```

**Better Accuracy (YOLOv11s):**
```bash
python scripts/train.py --model yolo11s --epochs 150 --cache
```

**Monitor Training:**
```bash
# In a new terminal
tensorboard --logdir models/training_runs
# Open http://localhost:6006
```

**Training will show progress:**
```
Epoch 1/100: 100%|████| 50/50 [00:45<00:00]
   mAP@0.5: 0.6234, Loss: 1.234

Epoch 50/100: 100%|████| 50/50 [00:43<00:00]
   mAP@0.5: 0.8956, Loss: 0.456

Epoch 100/100: 100%|████| 50/50 [00:42<00:00]
   mAP@0.5: 0.9234 ✅ (Target: >0.90)
```

### Step 5: Evaluate Model (1 minute)

```bash
python scripts/evaluate.py
```

Output:
```
📊 Performance Metrics:
   mAP@0.5:      0.9234 (92.34%) ✅
   Precision:    0.9180 (91.80%)
   Recall:       0.8750 (87.50%)
   F1 Score:     0.8960 (89.60%)

🎯 Target Assessment: PASSED - Model achieves target!
```

### Step 6: Export & Deploy (1 minute)

```bash
python scripts/export_model.py --deploy
```

This will:
- Export to ONNX format
- Copy to `backend/app/models/custom_knife_model.pt`
- Backend will auto-load on next restart

### Step 7: Test in Browser

```bash
# Restart backend (if running)
cd ../backend
uvicorn app.main:app --reload --port 8000

# Open browser: http://localhost:3500
# Login and test detection with real knife!
```

## ⏱️ Time Summary

| Step | Time | Activity |
|------|------|----------|
| 1 | 5 min | Install dependencies |
| 2 | 5 min | Download dataset |
| 3 | 2 min | Prepare dataset |
| 4 | 2-4 hrs | Train model (GPU) |
| 5 | 1 min | Evaluate model |
| 6 | 1 min | Export & deploy |
| 7 | 1 min | Test in browser |
| **Total** | **2-4 hours** | (mostly training time) |

## 💡 Tips for Success

### Getting >90% mAP

1. **Dataset Quality** (Most Important!)
   - Need 500+ images minimum
   - 1000+ images recommended
   - Diverse lighting, angles, backgrounds
   - Accurate bounding box annotations

2. **Training Duration**
   - Start with 100 epochs
   - Extend to 150-200 if needed
   - Watch for mAP plateau

3. **Model Selection**
   - YOLOv11n: Fast (15-20ms), 88-92% mAP
   - YOLOv11s: Balanced (20-25ms), 90-94% mAP
   - YOLOv11m: Accurate (30-35ms), 92-96% mAP

4. **Augmentation**
   - Default settings work well
   - Mosaic augmentation is critical
   - Don't over-augment (can hurt accuracy)

### If mAP < 90%

**After 100 epochs:**
- ✅ Train 50 more epochs
- ✅ Try YOLOv11s (larger model)
- ✅ Check dataset quality
- ✅ Add more training data

**Consistently < 85%:**
- ❌ Dataset too small (need 500+)
- ❌ Poor annotation quality
- ❌ Not enough diversity
- ❌ Consider collecting custom data

## 🐛 Common Issues

### "No module named 'ultralytics'"
```bash
pip install ultralytics>=8.3.0
```

### "CUDA out of memory"
```bash
# Reduce batch size
python scripts/train.py --batch 8

# Or use smaller model
python scripts/train.py --model yolo11n --batch 8
```

### "No datasets found"
```bash
# Check raw directory
ls -la datasets/raw/

# Should contain downloaded datasets
# If empty, download datasets first
```

### Training very slow
```bash
# Enable caching
python scripts/train.py --cache

# Reduce image size (not recommended)
python scripts/train.py --imgsz 512
```

## 📚 Next Steps

After successful training:

1. **Test thoroughly** with various knife images
2. **Document performance** in `ai/README.md`
3. **Share results** with team
4. **Consider multi-class** (knives, scissors, weapons)
5. **Optimize for edge** if deploying to embedded devices

## 🆘 Need Help?

- Check `ai/README.md` for detailed docs
- Review training logs in `models/training_runs/`
- Check TensorBoard for visualizations
- See [Ultralytics Docs](https://docs.ultralytics.com/)

---

**You're ready to train! Start with Step 1** ⬆️

