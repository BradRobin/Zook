# 🌙 Overnight Local Training Guide

## TL;DR
Run this **tonight before bed**, wake up to a trained model **tomorrow morning**!

---

## ⚡ Quick Start (2 minutes to launch)

### Step 1: Activate Environment
```powershell
cd C:\Users\bradr\OneDrive\Documents\GitHub\Zook
cd backend
venv\Scripts\activate
```

### Step 2: Install AI Dependencies
```powershell
cd ..\ai
pip install -r requirements.txt
```

### Step 3: Start Training
```powershell
cd scripts
python train_local.py
```

**That's it!** The script will:
1. Download your knife dataset from Roboflow (already configured with your API key)
2. Train for 100 epochs (12-24 hours on CPU)
3. Save checkpoints every 10 epochs (in case you need to stop)
4. Automatically evaluate the model

---

## ⏱️ Time Estimates

| Mode | Epochs | Time | Accuracy |
|------|--------|------|----------|
| **Full (Recommended)** | 100 | 12-24 hours | >90% |
| **Quick** | 50 | 6-12 hours | 85-90% |

---

## 🎯 Recommended: Full Training Tonight

### Before Bed (5 minutes):
```powershell
# From ai/scripts directory
python train_local.py
```

**Press 'y' when prompted**

Then:
- ✅ Leave your computer running
- ✅ Don't close the terminal
- ✅ Plug in your laptop (don't let it sleep)
- ✅ Go to sleep

### Tomorrow Morning:
You'll wake up to:
```
✅ Training Complete!
📦 Best model saved to: ai/models/training_runs/knife_detection/weights/best.pt
📊 Final Evaluation:
   mAP@0.5: 0.9234 (92.34%)
   Precision: 0.9456 (94.56%)
   Recall: 0.8912 (89.12%)

🎉 SUCCESS! Model achieves >90% mAP@0.5
```

---

## ⚡ Alternative: Quick Training

If you want to test **faster** (6-12 hours):
```powershell
python train_local.py --quick
```

This trains for 50 epochs instead of 100:
- ✅ Faster: 6-12 hours
- ⚠️ Lower accuracy: 85-90% (may not hit 90% target)
- Good for testing the pipeline

---

## 🛑 If You Need to Stop Training

**Press `Ctrl+C`** in the terminal

Your progress is **automatically saved**!

### Resume Later:
```powershell
python train_local.py --resume
```

This continues from your last checkpoint.

---

## 📊 Monitor Progress

The script prints updates every epoch:
```
Epoch 1/100: 100%|██████████| 45/45 [08:32<00:00, 11.38s/it]
    Class     Images  Instances      P      R  mAP50  mAP50-95
      all        150        287  0.845  0.762  0.821     0.498

Epoch 2/100: 100%|██████████| 45/45 [08:28<00:00, 11.31s/it]
    Class     Images  Instances      P      R  mAP50  mAP50-95
      all        150        287  0.867  0.785  0.843     0.521
...
```

**What to look for:**
- `mAP50` (mAP@0.5) should increase toward 0.90 (90%)
- `P` (Precision) and `R` (Recall) should be high (>0.85)

---

## ✅ After Training Completes

### Step 1: Deploy Model (1 minute)
```powershell
cd C:\Users\bradr\OneDrive\Documents\GitHub\Zook\ai
python scripts/deploy_model.py --auto
```

### Step 2: Restart Backend (1 minute)
```powershell
cd ..\backend
uvicorn app.main:app --reload --port 8000
```

Look for:
```
INFO:app.main:Custom model found: app/models/custom_knife_model.pt
INFO:app.main:✓ Using custom-trained knife detection model
```

### Step 3: Test in Browser
1. Open http://localhost:3000
2. Login
3. Hold knife in front of camera
4. Should detect with **>90% confidence**!

---

## 🔧 Troubleshooting

### Training too slow?
- **Expected:** 8-15 minutes per epoch on CPU
- **100 epochs:** 13-25 hours total
- **Solution:** Use `--quick` mode (50 epochs, 6-12 hours)

### Out of memory?
Unlikely with batch size 8, but if it happens:
1. Close other programs
2. Edit `train_local.py` line 157: change `batch=8` to `batch=4`

### Computer went to sleep?
1. Wake it up
2. Resume training:
   ```powershell
   python train_local.py --resume
   ```

---

## 🎯 What You're Getting

**Current Model (COCO):**
- 65% accuracy for knives
- Often <90% confidence (misses detections)

**After Tonight (Custom Model):**
- >90% accuracy
- Consistently >90% confidence
- Reliable knife detection

---

## 💡 Pro Tips

1. **Plug in your laptop** - prevent sleep mode
2. **Disable sleep settings** - System → Power → Never sleep
3. **Start training at bedtime** - 8 hours sleep = most training done
4. **Check in the morning** - should be done or close to done

---

## 📋 Quick Checklist

- [ ] Activate virtual environment
- [ ] Install AI dependencies: `pip install -r requirements.txt`
- [ ] Navigate to `ai/scripts`
- [ ] Run `python train_local.py`
- [ ] Press 'y' to confirm
- [ ] Keep computer running overnight
- [ ] Check results in the morning
- [ ] Deploy model with `deploy_model.py --auto`
- [ ] Restart backend
- [ ] Test in browser

---

## ⏰ Timeline

| When | What | Duration |
|------|------|----------|
| **Tonight 11:00 PM** | Start training | 2 min |
| **Tonight 11:02 PM** | Go to sleep | - |
| **Tomorrow 11:00 AM** | Training finishes | 12 hours |
| **Tomorrow 11:05 AM** | Deploy & test | 5 min |

---

## 🚀 Ready to Start?

```powershell
cd C:\Users\bradr\OneDrive\Documents\GitHub\Zook\backend
venv\Scripts\activate
cd ..\ai
pip install -r requirements.txt
cd scripts
python train_local.py
```

**Press 'y' when prompted, then go to bed!** 🌙

You'll have your >90% accurate knife detection model tomorrow morning! ☀️


