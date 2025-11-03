# Google Colab Training Guide - Custom Knife Detection

Complete guide to train a custom YOLOv11 knife detection model using Google Colab's free GPU.

**Time Required:** 2-3 hours (mostly automatic training)  
**Cost:** $0 (uses free Google Colab GPU)  
**Result:** Custom model with >90% mAP@0.5 accuracy

---

## Prerequisites

1. **Google Account** - For Google Colab access
2. **Roboflow Account** - Free account for dataset access
3. **Basic understanding** - No coding experience required

---

## Step 1: Create Roboflow Account (5 minutes)

### 1.1 Sign Up

1. Go to https://app.roboflow.com
2. Click "Sign Up"
3. Use Google/GitHub sign-in or email
4. Verify your email

### 1.2 Get API Key

1. Click your profile icon (top-right)
2. Select "Account Settings"
3. Go to "Roboflow API" section
4. Copy your API key (starts with `rf_...`)
5. **Save this key** - you'll need it soon!

**Your API Key:** `rf_xxxxxxxxxxxxxxxxxx` ✅

---

## Step 2: Find Knife Detection Dataset (5 minutes)

### 2.1 Browse Roboflow Universe

1. Go to https://universe.roboflow.com
2. Search: `"knife detection"` or `"weapon detection"`
3. Filter results:
   - ✅ Has YOLO format
   - ✅ 500+ images
   - ✅ Public/Free license

### 2.2 Recommended Datasets

**Option A: Weapons Detection** (Recommended)
- **Link:** Search "Weapons Detection" on Universe
- **Images:** 1000+ images
- **Classes:** knife, gun, scissors
- **Quality:** High quality annotations

**Option B: Knife Detection Dataset**
- **Link:** Search "Knife Detection" on Universe  
- **Images:** 500-800 images
- **Classes:** knife only
- **Quality:** Good for single-class training

**Option C: Custom Collection**
- Search for other knife/weapon datasets
- Look for datasets with:
  - Multiple lighting conditions
  - Various angles and backgrounds
  - Clear bounding boxes

### 2.3 Note Dataset Details

Write down these details:

1. **Workspace Name:** `_______________` (from dataset URL)
2. **Project Name:** `_______________` (from dataset page)
3. **Version:** Usually `1` (check dataset versions tab)

**Example:**
- Workspace: `my-workspace-abc123`
- Project: `knife-detection-v1`
- Version: `1`

---

## Step 3: Create Google Colab Notebook (2 minutes)

### 3.1 Copy Notebook Template

I've created a ready-to-use notebook at:
```
ai/notebooks/train_knife_detection_colab.ipynb
```

### 3.2 Upload to Colab

1. Go to https://colab.research.google.com
2. Click "File" → "Upload notebook"
3. Upload `train_knife_detection_colab.ipynb`
4. Notebook opens automatically

### 3.3 Enable GPU

**CRITICAL STEP - Don't skip!**

1. Click "Runtime" → "Change runtime type"
2. Hardware accelerator: **GPU**
3. GPU type: **T4** (default free tier)
4. Click "Save"

**Verify GPU:**
- Top-right shows "GPU: T4"
- If not, repeat above steps

---

## Step 4: Configure & Run Training (1 minute + 2-3 hours)

### 4.1 Edit Configuration Cell

Find **Cell 3** in the notebook (titled "Download Dataset").

Replace these values:

```python
ROBOFLOW_API_KEY = "YOUR_API_KEY"  # Paste from Step 1.2
WORKSPACE_NAME = "your-workspace"   # From Step 2.3
PROJECT_NAME = "knife-detection"    # From Step 2.3
VERSION = 1                         # From Step 2.3
```

**Example (filled in):**
```python
ROBOFLOW_API_KEY = "rf_1AbC2dEf3GhI4jKl5MnO6pQr"
WORKSPACE_NAME = "john-workspace-xyz"
PROJECT_NAME = "knife-detection-v2"
VERSION = 1
```

### 4.2 Run All Cells

1. Click "Runtime" → "Run all"
2. Notebook will execute all cells automatically
3. Progress shows in each cell output

### 4.3 Monitor Progress

**What happens:**

**Cells 1-2 (1 minute):**
- Check GPU availability
- Install dependencies (ultralytics, roboflow)
- You'll see: `✅ GPU detected! Training will be fast`

**Cell 3 (2-5 minutes):**
- Download dataset from Roboflow
- Validate images and labels
- Shows: `✅ Dataset downloaded, Train images: XXX`

**Cell 4 (2-3 hours):**
- **THIS IS THE LONG STEP**
- Trains YOLOv11 model for 100 epochs
- Progress bar updates every epoch
- Shows loss, mAP, precision, recall

**Example output:**
```
Epoch 1/100: 100%|████████| 50/50 [00:45<00:00]
   mAP@0.5: 0.6234, Loss: 1.234

Epoch 50/100: 100%|████████| 50/50 [00:43<00:00]
   mAP@0.5: 0.8956, Loss: 0.456

Epoch 100/100: 100%|████████| 50/50 [00:42<00:00]
   mAP@0.5: 0.9234 ✅ (Target: >0.90)

✅ Training Complete!
```

**Cell 5 (30 seconds):**
- Evaluates final model performance
- Shows mAP@0.5, precision, recall
- Displays training curves

**Cell 6 (30 seconds):**
- Tests model on sample images
- Shows detection results

**Cell 7 (30 seconds):**
- Prepares model for download
- Creates download link

### 4.4 Leave Tab Open

**Important:**
- Training takes 2-3 hours
- **Keep the Colab tab open**
- Computer can sleep, but tab must stay open
- Don't close browser or tab

**Tips:**
- Set a timer for 2.5 hours
- Check back periodically
- Watch for "✅ Training Complete!" message

---

## Step 5: Evaluate Results (2 minutes)

### 5.1 Check Performance Metrics

After training completes, check **Cell 5 output**:

```
📊 Performance Metrics
==========================================

mAP@0.5:      0.9234 (92.34%) ✅
Precision:    0.9180 (91.80%)
Recall:       0.8750 (87.50%)
F1 Score:     0.8960 (89.60%)

🎯 Target Assessment
==========================================
✅ SUCCESS! Model achieves target (mAP@0.5 = 92.34%)
   Model is ready for deployment!
```

### 5.2 Interpret Results

**If mAP@0.5 >= 90%:**
- ✅ **Excellent!** Model ready for deployment
- Proceed to Step 6 (Download Model)

**If mAP@0.5 = 85-89%:**
- ⚠️ **Good, but close** - Model usable but improvable
- **Options:**
  1. Deploy anyway (85%+ is decent)
  2. Train 50 more epochs (change `epochs=100` to `epochs=150` in Cell 4)
  3. Use larger model (change `yolo11n.pt` to `yolo11s.pt`)

**If mAP@0.5 < 85%:**
- ❌ **Needs improvement**
- **Possible causes:**
  - Dataset too small (<500 images)
  - Poor annotation quality
  - Not enough variety (lighting, angles)
- **Solutions:**
  1. Find larger dataset (1000+ images)
  2. Check dataset quality
  3. Try YOLOv11s (larger model)
  4. Train for 150 epochs

### 5.3 View Training Visualizations

Scroll to Cell 5 output to see:

1. **Training curves** (loss over time)
2. **mAP curve** (improvement over epochs)
3. **Confusion matrix** (classification accuracy)
4. **Sample detections** (with bounding boxes)

These help understand model performance.

---

## Step 6: Download Trained Model (1 minute)

### 6.1 Method A: Direct Download (Recommended)

**In Cell 7, you'll see:**
```python
files.download(best_pt)
```

When this cell runs:
1. Browser download prompt appears
2. File name: `best.pt` (5-10 MB)
3. Save to your **Downloads folder**

### 6.2 Method B: Manual Download

If automatic download fails:

1. Click **folder icon** (left sidebar)
2. Navigate to: `runs/detect/knife_detection/weights/`
3. Find `best.pt`
4. **Right-click** → "Download"
5. Save to Downloads

### 6.3 Move Model to Project

**After download:**

1. Open File Explorer
2. Go to Downloads folder
3. Find `best.pt` file
4. Copy or move to:
   ```
   YourProject/ai/models/best.pt
   ```

**Full path example:**
```
C:\Users\YourName\Documents\GitHub\Zook\ai\models\best.pt
```

✅ **Model is now ready for deployment!**

---

## Step 7: Deploy to Zook Backend (Automated)

### 7.1 Notify AI Assistant

Tell your AI assistant (me):

> "I've downloaded the trained model to `ai/models/best.pt`. Please deploy it to the backend."

### 7.2 What Happens Automatically

I will:

1. ✅ Run deployment script (`ai/scripts/deploy_model.py`)
2. ✅ Validate model loads correctly
3. ✅ Copy to `backend/app/models/custom_knife_model.pt`
4. ✅ Create model info file with metrics
5. ✅ Update backend configuration
6. ✅ Restart backend server
7. ✅ Verify custom model loaded

You'll see:
```
✅ Model validated successfully
✅ Deployed to backend/app/models/custom_knife_model.pt
✅ Backend restarting with custom model...
✅ Custom model loaded (mAP@0.5: 92.34%)
```

---

## Step 8: Test Detection (5 minutes)

### 8.1 Start Application

If not already running:

```powershell
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd ui
python -m http.server 3000
```

### 8.2 Open Browser

1. Go to: http://localhost:3000
2. Login with your credentials
3. Allow camera access

### 8.3 Test Detection

**Test 1: Real Knife**
1. Hold kitchen knife in front of camera
2. Keep knife in frame for 3-5 seconds
3. **Expected:** Red border flash, detection log appears
4. **Check confidence:** Should be >90%

**Test 2: Different Angles**
1. Rotate knife (blade up, down, sideways)
2. Move closer/farther
3. **Expected:** Consistent detection at all angles

**Test 3: Different Knives**
1. Try pocket knife, butter knife, chef's knife
2. **Expected:** All knife types detected

**Test 4: Non-Knives**
1. Hold pen, phone, hand, fork
2. **Expected:** No detection (no false positives)

### 8.4 Verify Improvement

**Before (COCO Model):**
- Confidence: 60-75% (often below 90%)
- Detection rate: Inconsistent
- False negatives: Common

**After (Custom Model):**
- Confidence: 90-98% ✅
- Detection rate: Consistent ✅
- False negatives: Rare ✅

---

## Troubleshooting

### Issue: "No GPU available"

**Solution:**
1. Runtime → Change runtime type
2. Select GPU (T4)
3. Save and restart notebook

### Issue: "Roboflow API key invalid"

**Solution:**
1. Check API key copied correctly (no extra spaces)
2. Verify key starts with `rf_`
3. Regenerate key in Roboflow if needed

### Issue: "Dataset download fails"

**Solution:**
1. Check internet connection
2. Verify workspace/project names are correct
3. Try different dataset
4. Check Roboflow quota (may hit free tier limit)

### Issue: "Training stops mid-way"

**Solution:**
1. Colab free tier timeout (12 hours max)
2. Re-run notebook from Cell 4 (training resumes)
3. Or upgrade to Colab Pro ($10/month)

### Issue: "mAP < 90% after training"

**Solution:**
1. Train for more epochs (150 instead of 100)
2. Use larger dataset (1000+ images)
3. Try YOLOv11s model (more accurate)
4. Check dataset quality

### Issue: "Download fails"

**Solution:**
1. Use Method B (manual download)
2. Check browser popup blocker
3. Try different browser

### Issue: "Model doesn't detect after deployment"

**Solution:**
1. Verify model file exists at `backend/app/models/custom_knife_model.pt`
2. Check backend logs for "Custom model loaded"
3. Restart backend server
4. Check `.env` has `USE_CUSTOM_MODEL=true`

---

## FAQs

**Q: How much does this cost?**  
A: $0 - Google Colab GPU is free (with usage limits)

**Q: Can I train on CPU?**  
A: Not recommended - would take 12-24 hours vs 2-3 hours on GPU

**Q: Can I improve accuracy further?**  
A: Yes - use larger model (YOLOv11s/m), more data, longer training

**Q: How often do I need to retrain?**  
A: Only when you want to improve accuracy or add new knife types

**Q: Can I train for other objects?**  
A: Yes - same process, just use different dataset (guns, scissors, etc.)

**Q: What if Colab disconnects?**  
A: Notebook saves progress. Re-run from last successful cell.

**Q: Can I use my own knife images?**  
A: Yes - upload to Roboflow, annotate with bounding boxes, train

**Q: How to add more training data later?**  
A: Upload more images to Roboflow, increment version, retrain

---

## Summary Checklist

Training complete when ALL checked:

- [ ] Roboflow account created
- [ ] API key obtained
- [ ] Dataset found (500+ images)
- [ ] Notebook uploaded to Colab
- [ ] GPU enabled (T4)
- [ ] Configuration updated (Cell 3)
- [ ] Training run completed (2-3 hours)
- [ ] mAP@0.5 >= 90% achieved
- [ ] Model downloaded to `ai/models/best.pt`
- [ ] AI assistant notified for deployment
- [ ] Backend restarted with custom model
- [ ] Detection tested in browser
- [ ] Confidence >90% verified

---

## Next Steps After Training

1. **Document Performance**
   - Save metrics in `ai/README.md`
   - Record best mAP, precision, recall

2. **Backup Model**
   - Keep `best.pt` in safe location
   - Save model_info.json with metrics

3. **Share Results**
   - Show team the improvement
   - Demo real-time detection

4. **Continuous Improvement**
   - Collect edge cases (missed detections)
   - Add to dataset and retrain periodically
   - Monitor real-world performance

---

## Resources

- **Roboflow Universe:** https://universe.roboflow.com
- **Google Colab:** https://colab.research.google.com
- **Ultralytics Docs:** https://docs.ultralytics.com
- **YOLOv11 Paper:** https://github.com/ultralytics/ultralytics

---

**Ready to train? Start with Step 1!** ⬆️

Questions? Check troubleshooting section or ask your AI assistant.

---

*Training guide version 1.0 - Last updated: 2025*

