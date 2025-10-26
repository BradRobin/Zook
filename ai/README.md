# Knife Detection - Custom YOLOv11 Training

**Custom-trained YOLOv11 model for knife detection targeting >90% mAP@0.5 accuracy**

This directory contains all resources for training, evaluating, and deploying a custom knife detection model that outperforms the generic COCO pretrained model.

## 📁 Directory Structure

```
ai/
├── datasets/               # Training data
│   ├── raw/               # Original downloaded datasets
│   ├── processed/         # Prepared train/val/test splits
│   │   ├── images/        # Image files
│   │   ├── labels/        # YOLO format annotations
│   │   └── data.yaml      # Dataset configuration
├── models/                # Trained models
│   ├── best.pt            # Best performing model
│   ├── best.onnx          # ONNX export
│   ├── exports/           # Other format exports
│   └── training_runs/     # Training experiment logs
├── notebooks/             # Jupyter notebooks
│   ├── dataset_exploration.ipynb
│   └── model_evaluation.ipynb
├── scripts/               # Training pipeline scripts
│   ├── download_datasets.py   # Download datasets
│   ├── prepare_dataset.py     # Prepare and split data
│   ├── train.py               # Train model
│   ├── evaluate.py            # Evaluate performance
│   └── export_model.py        # Export to multiple formats
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ai
pip install -r requirements.txt
```

### 2. Download Datasets

**Option A: Using Roboflow**
```bash
python scripts/download_datasets.py --source roboflow \
    --workspace "your-workspace" \
    --project "knife-detection" \
    --version 1 \
    --api-key "YOUR_API_KEY"
```

**Option B: Using Kaggle**
```bash
python scripts/download_datasets.py --source kaggle \
    --dataset "username/knife-detection-dataset"
```

**Option C: Manual Download**
- Download datasets from [Roboflow Universe](https://universe.roboflow.com/search?q=knife)
- Or from [Kaggle](https://www.kaggle.com/search?q=knife+detection)
- Extract to `datasets/raw/`

### 3. Prepare Dataset

```bash
python scripts/prepare_dataset.py
```

This will:
- Validate all images and annotations
- Remove corrupted/duplicate files
- Split into train (70%), val (20%), test (10%)
- Create `datasets/processed/data.yaml`

### 4. Train Model

**Basic training (YOLOv11n, 100 epochs):**
```bash
python scripts/train.py
```

**Advanced training (YOLOv11s, 150 epochs, GPU 0):**
```bash
python scripts/train.py --model yolo11s --epochs 150 --batch 32 --device 0 --cache
```

**Training parameters:**
- `--model`: yolo11n (fast) | yolo11s (balanced) | yolo11m (accurate)
- `--epochs`: Number of training epochs (default: 100)
- `--batch`: Batch size (default: 16)
- `--device`: GPU device (default: 0) or 'cpu'
- `--cache`: Cache images in RAM for faster training

### 5. Evaluate Model

```bash
python scripts/evaluate.py
```

This will:
- Run validation on test set
- Calculate mAP@0.5, precision, recall, F1
- Compare with COCO baseline
- Generate evaluation reports

### 6. Export Model

**Export to ONNX (recommended for deployment):**
```bash
python scripts/export_model.py --format onnx
```

**Export and deploy to Zook backend:**
```bash
python scripts/export_model.py --format onnx --deploy
```

**Export to all formats:**
```bash
python scripts/export_model.py --format all
```

## 📊 Dataset Sources

### Recommended Datasets

1. **Roboflow Universe - Knife Detection**
   - URL: https://universe.roboflow.com/search?q=knife
   - Look for: "Knife Detection", "Weapon Detection"
   - Format: YOLO (preferred)
   - Typical size: 500-2000 images

2. **Kaggle - Knife Detection**
   - Search: https://www.kaggle.com/search?q=knife+detection
   - Check annotation format (YOLO, COCO, Pascal VOC)
   - Convert to YOLO if needed

3. **Open Images Dataset V7**
   - Knife class: `/m/0dt3t`
   - ~2000+ images available
   - Requires format conversion

### Dataset Requirements

- **Minimum**: 500 annotated images
- **Recommended**: 1000+ images
- **Format**: YOLO (class x_center y_center width height)
- **Diversity**: Various lighting, angles, backgrounds, knife types
- **Balance**: Mix of positive (with knives) and negative samples

## 🎯 Performance Targets

### Target Metrics

| Metric | Target | Purpose |
|--------|--------|---------|
| **mAP@0.5** | **>90%** | Main goal - overall detection accuracy |
| mAP@0.5:0.95 | >70% | Accuracy across IoU thresholds |
| Precision | >90% | Minimize false positives |
| Recall | >85% | Minimize missed detections |
| F1 Score | >87% | Balanced precision-recall |

### Performance Comparison

| Model | mAP@0.5 | Precision | Recall | Inference (GPU) |
|-------|---------|-----------|--------|-----------------|
| COCO Baseline | ~65% | ~70% | ~60% | 15-25ms |
| **Custom YOLOv11n** | **>90%** | **>90%** | **>85%** | 15-25ms |
| Custom YOLOv11s | >92% | >92% | >88% | 20-30ms |

## 🔧 Training Configuration

### Default Training Parameters

```python
epochs = 100                  # Training epochs
batch = 16                    # Batch size
imgsz = 640                   # Image size
lr0 = 0.01                    # Initial learning rate
patience = 20                 # Early stopping patience

# Augmentation (critical for >90% accuracy)
mosaic = 1.0                  # Mosaic augmentation
fliplr = 0.5                  # Horizontal flip
hsv_h = 0.015                 # Hue variation
hsv_s = 0.7                   # Saturation variation
hsv_v = 0.4                   # Value variation
degrees = 10.0                # Rotation
translate = 0.1               # Translation
scale = 0.5                   # Scaling
```

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | NVIDIA GTX 1660 (6GB) | RTX 3060 (12GB) |
| RAM | 8GB | 16GB+ |
| Storage | 10GB | 20GB+ |
| OS | Windows/Linux/macOS | Linux (best GPU support) |

**Alternative**: Google Colab (free GPU) or cloud VM (AWS, GCP, Azure)

### Training Time Estimates

| Model | Hardware | Time (100 epochs) |
|-------|----------|-------------------|
| YOLOv11n | RTX 3060 | 2-3 hours |
| YOLOv11n | GTX 1660 Ti | 3-4 hours |
| YOLOv11s | RTX 3060 | 4-6 hours |
| YOLOv11s | GTX 1660 Ti | 6-8 hours |
| YOLOv11n | CPU (8-core) | 40-60 hours ❌ |

## 📈 Training Tips

### If mAP < 90%

**Dataset Issues:**
- ✅ Collect more diverse training data (aim for 1000+ images)
- ✅ Check annotation quality (use labelImg to verify)
- ✅ Balance positive/negative samples
- ✅ Add hard negatives (similar objects that aren't knives)

**Training Issues:**
- ✅ Train for more epochs (150-300)
- ✅ Try larger model (yolo11s or yolo11m)
- ✅ Adjust learning rate (try 0.005 or 0.02)
- ✅ Tune augmentation parameters

**Model Issues:**
- ✅ Check for overfitting (val loss vs train loss)
- ✅ Add regularization (increase dropout/weight decay)
- ✅ Use transfer learning from best checkpoint

### Monitoring Training

**TensorBoard:**
```bash
tensorboard --logdir models/training_runs
```

Open http://localhost:6006 to view:
- Training/validation losses
- mAP curves
- Precision/recall curves
- Learning rate schedule

## 🚀 Deployment

### Integration with Zook Backend

**Automatic (recommended):**
```bash
python scripts/export_model.py --deploy
```

**Manual:**
```bash
cp models/best.pt ../backend/app/models/custom_knife_model.pt
```

The backend automatically detects and loads the custom model on startup!

### Model Formats

| Format | Use Case | Size | Speed |
|--------|----------|------|-------|
| **PyTorch (.pt)** | **Production (recommended)** | ~6MB | Fast |
| ONNX (.onnx) | Cross-platform, edge devices | ~5MB | Fast |
| TensorRT (.engine) | NVIDIA GPU optimization | ~4MB | Fastest |
| CoreML (.mlmodel) | iOS deployment | ~5MB | Fast |

### Inference Performance

| Hardware | Format | Latency | Throughput |
|----------|--------|---------|------------|
| RTX 3060 | PyTorch | 15-20ms | ~50-60 FPS |
| GTX 1660 Ti | PyTorch | 20-25ms | ~40-50 FPS |
| CPU (8-core) | ONNX | 80-120ms | ~8-12 FPS |
| RTX 3060 | TensorRT | 10-15ms | ~65-100 FPS |

## 📝 Results (Example)

### Training Run: knife_detection_v1

**Configuration:**
- Model: YOLOv11n
- Dataset: 1200 images (840 train, 240 val, 120 test)
- Epochs: 100
- GPU: RTX 3060

**Final Metrics:**
- mAP@0.5: **92.3%** ✅ (Target: >90%)
- mAP@0.5:0.95: 73.1%
- Precision: 91.8%
- Recall: 87.5%
- F1 Score: 89.6%

**Improvement over COCO baseline:**
- mAP@0.5: +27.3% improvement
- Precision: +21.8% improvement
- Recall: +27.5% improvement

**Training Time:** 2 hours 45 minutes

## 🔬 Advanced Topics

### Custom Data Collection

If existing datasets are insufficient:

1. **Capture Images:**
   - Use phone camera or webcam
   - Various knife types (kitchen, pocket, utility)
   - Different contexts (hands, tables, backgrounds)
   - Multiple lighting conditions

2. **Annotation:**
   - Use [LabelImg](https://github.com/HumanSignal/labelImg)
   - Or [Roboflow](https://roboflow.com/) (has auto-labeling)
   - Save in YOLO format
   - Review and verify all annotations

3. **Dataset Augmentation:**
   - Brightness/contrast variations
   - Rotations and flips
   - Add synthetic backgrounds
   - Blur and noise augmentation

### Multi-Class Detection

To detect multiple threat types (knives, scissors, weapons):

1. Update `data.yaml`:
```yaml
nc: 3
names: ['knife', 'scissors', 'gun']
```

2. Ensure labels use correct class IDs (0, 1, 2, ...)

3. Train with multi-class dataset

### Model Optimization

**Quantization (reduce model size):**
```python
from ultralytics import YOLO
model = YOLO('best.pt')
model.export(format='onnx', int8=True)  # INT8 quantization
```

**Pruning (reduce inference time):**
```python
# Requires additional pruning libraries
# See: https://pytorch.org/tutorials/intermediate/pruning_tutorial.html
```

## 🐛 Troubleshooting

### Common Issues

**Issue: Low mAP (<70%)**
- Check dataset quality and size (need 500+ images)
- Verify annotations are correct
- Train for more epochs
- Try larger model

**Issue: Overfitting (train mAP high, val mAP low)**
- Add more training data
- Increase augmentation
- Reduce model size
- Add regularization

**Issue: Slow training**
- Enable `--cache` flag
- Increase `--workers` (data loading threads)
- Use smaller batch size if GPU memory full
- Close other GPU applications

**Issue: Out of memory**
- Reduce batch size: `--batch 8` or `--batch 4`
- Use smaller model: `yolo11n` instead of `yolo11s`
- Reduce image size: `--imgsz 512`

## 📚 Resources

- [Ultralytics YOLOv11 Docs](https://docs.ultralytics.com/)
- [YOLOv11 Training Guide](https://docs.ultralytics.com/modes/train/)
- [YOLOv11 Model Export](https://docs.ultralytics.com/modes/export/)
- [Roboflow Datasets](https://universe.roboflow.com/)
- [Kaggle Datasets](https://www.kaggle.com/datasets)
- [LabelImg Annotation Tool](https://github.com/HumanSignal/labelImg)

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review training logs and plots
3. Refer to Ultralytics documentation
4. Open an issue in the main Zook repository

---

**Last Updated:** 2025-10-25
**Model Version:** v1.0
**Target Achievement:** >90% mAP@0.5

