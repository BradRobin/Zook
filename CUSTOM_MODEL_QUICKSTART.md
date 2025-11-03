# Custom Model Quick Start

Train and deploy a custom knife detection model in 3 hours.

---

## 🚀 Quick Steps

### 1. Train Model (2-3 hours)

1. **Get Roboflow API key**: https://app.roboflow.com → Account Settings → API
2. **Open guide**: `ai/COLAB_TRAINING_GUIDE.md`
3. **Follow all steps** in the guide
4. **Download** `best.pt` from Google Colab after training

**Result**: Custom model with >90% accuracy

---

### 2. Deploy Model (1 minute)

Once you have `best.pt` downloaded:

```bash
# Copy model to ai/models directory
cp ~/Downloads/best.pt ai/models/best.pt

# Run deployment script
cd ai
python scripts/deploy_model.py --model models/best.pt
```

**Or automatic deployment:**
```bash
cd ai
python scripts/deploy_model.py --auto
```

The script will:
- ✅ Validate model
- ✅ Test inference
- ✅ Copy to `backend/app/models/custom_knife_model.pt`
- ✅ Create metadata file
- ✅ Update configuration

---

### 3. Restart Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Look for these logs:**
```
INFO: Custom model found: app/models/custom_knife_model.pt
INFO: Knife class detected: ID=0, name='knife'
INFO: Model loaded on device: cpu
✓ Using custom-trained knife detection model
INFO: Detection model initialized and ready
```

---

### 4. Test in Browser

1. Open: http://localhost:3000
2. Login with your credentials
3. Hold knife in front of camera
4. **Expected**: Detection with >90% confidence

---

## 📊 Before vs After

| Metric | COCO Model | Custom Model |
|--------|------------|--------------|
| **Accuracy** | ~65% | >90% ✅ |
| **Confidence** | Often <90% | Consistently >90% ✅ |
| **Detection Rate** | Inconsistent | Reliable ✅ |
| **False Negatives** | Common | Rare ✅ |
| **Inference Speed** | ~100ms | ~100ms (same) |

---

## 🧪 Testing

### Test Custom Model

```bash
cd backend
python test_custom_model.py
```

**Output shows:**
- Custom vs COCO comparison
- Detection rates
- Average confidence
- Inference times

### Benchmark Performance

```bash
python test_custom_model.py --benchmark-only
```

**Shows:**
- Mean inference time
- P95/P99 latency
- Estimated FPS

---

## ⚙️ Configuration

### Use Custom Model (Default)

In `backend/app/config.py`:
```python
USE_CUSTOM_MODEL: bool = True
CUSTOM_MODEL_PATH: str = "app/models/custom_knife_model.pt"
```

### Fallback to COCO Model

Set in environment or config:
```python
USE_CUSTOM_MODEL: bool = False
```

Backend will auto-fallback to COCO if custom model not found.

---

## 🐛 Troubleshooting

### "Custom model not found"

**Check:**
```bash
ls backend/app/models/custom_knife_model.pt
```

**If missing:**
```bash
cd ai
python scripts/deploy_model.py --model path/to/best.pt
```

### "Model loads but doesn't detect"

**Check model class ID:**
- Custom models use class ID 0
- Backend auto-detects this
- Check logs for: `Knife class detected: ID=0`

### "Inference is slow (>200ms)"

**Options:**
1. Use GPU instead of CPU
2. Use smaller model (YOLOv11n)
3. Reduce image size

---

## 📚 Full Documentation

- **Training Guide**: `ai/COLAB_TRAINING_GUIDE.md` (complete step-by-step)
- **AI README**: `ai/README.md` (training details, datasets, best practices)
- **Backend README**: `backend/README.md` (API usage, deployment)
- **Implementation Status**: `WEBSOCKET_IMPLEMENTATION_STATUS.md` (technical details)

---

## 💡 Tips

### Getting Best Accuracy

1. **Dataset Quality**: Use 1000+ diverse images
2. **Training Duration**: 100-150 epochs
3. **Model Selection**: YOLOv11s for best accuracy
4. **Validation**: Check mAP@0.5 >0.90 before deployment

### Continuous Improvement

1. **Collect Edge Cases**: Save missed detections
2. **Retrain Periodically**: Add new data, retrain
3. **Monitor Performance**: Track confidence scores
4. **A/B Testing**: Compare old vs new models

---

## 🎯 Success Criteria

Your custom model is working if:

- [x] Backend logs show "Using custom-trained knife detection model"
- [x] Model info shows `knife_class_id: 0`
- [x] Browser detections have >90% confidence
- [x] Consistent detection across angles/lighting
- [x] Few false negatives
- [x] Inference time <100ms

---

## 🆘 Need Help?

1. **Training Issues**: See `ai/COLAB_TRAINING_GUIDE.md` troubleshooting section
2. **Deployment Issues**: Check `ai/scripts/deploy_model.py` output
3. **Detection Issues**: Run `python test_custom_model.py` for diagnostics
4. **Performance Issues**: Check inference time with benchmark

---

**Total Time**: ~3 hours (mostly training)  
**Improvement**: 65% → 90%+ accuracy  
**Worth it**: Absolutely! 🎉

Start with Step 1: Open `ai/COLAB_TRAINING_GUIDE.md`

