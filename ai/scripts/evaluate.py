#!/usr/bin/env python3
"""
Model Evaluation Script for Knife Detection

Comprehensive evaluation of trained model on test set:
- Calculate mAP, precision, recall, F1
- Generate confusion matrix
- Create precision-recall curves
- Visualize predictions
- Compare with baseline

Usage:
    python evaluate.py
    python evaluate.py --model ../models/best.pt
    python evaluate.py --conf 0.25 --iou 0.6
"""

import argparse
import torch
from pathlib import Path
from ultralytics import YOLO
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_curve, f1_score
import numpy as np
import json

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
DATA_YAML = AI_DIR / "datasets" / "processed" / "data.yaml"
MODELS_DIR = AI_DIR / "models"


class ModelEvaluator:
    """Evaluate trained YOLO model."""
    
    def __init__(self, model_path, data_yaml):
        self.model = YOLO(str(model_path))
        self.data_yaml = data_yaml
        self.model_path = model_path
        
        with open(data_yaml, 'r') as f:
            self.data_config = yaml.safe_load(f)
        
        print(f"📦 Model loaded: {model_path}")
        print(f"📊 Dataset: {data_yaml}")
    
    def run_validation(self, conf=0.25, iou=0.6):
        """Run validation on test set."""
        print("\n🔍 Running validation...")
        
        results = self.model.val(
            data=str(self.data_yaml),
            split='test',
            conf=conf,
            iou=iou,
            plots=True,
            save_json=True,
            save_hybrid=True
        )
        
        return results
    
    def print_metrics(self, results):
        """Print evaluation metrics."""
        print("\n" + "="*60)
        print("Evaluation Metrics")
        print("="*60)
        
        metrics = results.results_dict
        
        # Main metrics
        map50 = metrics.get('metrics/mAP50(B)', 0)
        map50_95 = metrics.get('metrics/mAP50-95(B)', 0)
        precision = metrics.get('metrics/precision(B)', 0)
        recall = metrics.get('metrics/recall(B)', 0)
        
        # Calculate F1
        if precision > 0 and recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0
        
        print(f"\n📊 Performance Metrics:")
        print(f"   mAP@0.5:      {map50:.4f} ({map50*100:.2f}%)")
        print(f"   mAP@0.5:0.95: {map50_95:.4f} ({map50_95*100:.2f}%)")
        print(f"   Precision:    {precision:.4f} ({precision*100:.2f}%)")
        print(f"   Recall:       {recall:.4f} ({recall*100:.2f}%)")
        print(f"   F1 Score:     {f1:.4f} ({f1*100:.2f}%)")
        
        # Target assessment
        print(f"\n🎯 Target Assessment (>90% mAP@0.5):")
        if map50 >= 0.90:
            print(f"   ✅ PASSED - Model achieves target!")
        else:
            shortfall = 0.90 - map50
            print(f"   ❌ FAILED - {shortfall*100:.2f}% below target")
            print(f"\n   Improvement suggestions:")
            if map50 < 0.70:
                print(f"   - Collect more diverse training data")
                print(f"   - Check dataset quality and annotations")
                print(f"   - Try larger model (yolo11s or yolo11m)")
            elif map50 < 0.85:
                print(f"   - Train for more epochs (extend to 200-300)")
                print(f"   - Fine-tune augmentation parameters")
                print(f"   - Add hard negative mining")
            else:
                print(f"   - Almost there! Try a few more epochs")
                print(f"   - Slightly adjust confidence threshold")
        
        return {
            'map50': map50,
            'map50_95': map50_95,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    def compare_with_baseline(self, custom_metrics):
        """Compare custom model with COCO baseline."""
        print("\n" + "="*60)
        print("Baseline Comparison")
        print("="*60)
        
        print(f"\n📊 Custom Model vs COCO Baseline:")
        print(f"\n   {'Metric':<15} {'COCO Baseline':<15} {'Custom Model':<15} {'Improvement':<15}")
        print(f"   {'-'*60}")
        
        # Estimated COCO baseline (typical performance on knife class)
        baseline = {
            'map50': 0.65,  # Estimated
            'precision': 0.70,
            'recall': 0.60,
            'f1': 0.65
        }
        
        for metric in ['map50', 'precision', 'recall', 'f1']:
            baseline_val = baseline[metric]
            custom_val = custom_metrics[metric]
            improvement = ((custom_val - baseline_val) / baseline_val) * 100 if baseline_val > 0 else 0
            
            print(f"   {metric:<15} {baseline_val:>6.2%}         {custom_val:>6.2%}         {improvement:>+6.1f}%")
        
        if custom_metrics['map50'] > baseline['map50']:
            improvement = (custom_metrics['map50'] - baseline['map50']) * 100
            print(f"\n   ✅ Custom model is {improvement:.1f}% better than baseline!")
        else:
            print(f"\n   ⚠️  Custom model underperforms baseline.")
            print(f"   Consider collecting more training data.")
    
    def generate_report(self, metrics, output_dir):
        """Generate evaluation report."""
        print(f"\n📝 Generating evaluation report...")
        
        report = {
            'model_path': str(self.model_path),
            'dataset': str(self.data_yaml),
            'metrics': metrics,
            'target_achieved': metrics['map50'] >= 0.90
        }
        
        report_path = output_dir / "evaluation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"   ✅ Report saved: {report_path}")
        
        # Create markdown report
        md_path = output_dir / "evaluation_report.md"
        with open(md_path, 'w') as f:
            f.write("# Knife Detection Model Evaluation Report\n\n")
            f.write(f"## Model Information\n")
            f.write(f"- Model: `{self.model_path}`\n")
            f.write(f"- Dataset: `{self.data_yaml}`\n\n")
            
            f.write(f"## Performance Metrics\n\n")
            f.write(f"| Metric | Value | Percentage |\n")
            f.write(f"|--------|-------|------------|\n")
            for key, value in metrics.items():
                f.write(f"| {key.upper()} | {value:.4f} | {value*100:.2f}% |\n")
            
            f.write(f"\n## Target Assessment\n\n")
            if metrics['map50'] >= 0.90:
                f.write(f"✅ **PASSED** - Model achieves >90% mAP@0.5 target!\n")
            else:
                f.write(f"❌ **FAILED** - Model below 90% mAP@0.5 target.\n")
                f.write(f"\nShortfall: {(0.90 - metrics['map50'])*100:.2f}%\n")
        
        print(f"   ✅ Markdown report: {md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate trained knife detection model"
    )
    
    parser.add_argument('--model', type=str, default='../models/best.pt',
                       help='Path to trained model (default: ../models/best.pt)')
    parser.add_argument('--data', type=str, default=str(DATA_YAML),
                       help=f'Path to data.yaml (default: {DATA_YAML})')
    parser.add_argument('--conf', type=float, default=0.25,
                       help='Confidence threshold (default: 0.25)')
    parser.add_argument('--iou', type=float, default=0.6,
                       help='IoU threshold for NMS (default: 0.6)')
    parser.add_argument('--output', type=str, default='../models/evaluation',
                       help='Output directory for reports')
    
    args = parser.parse_args()
    
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Please train a model first: python scripts/train.py")
        return
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Knife Detection Model Evaluation")
    print("="*60)
    
    # Create evaluator
    evaluator = ModelEvaluator(model_path, args.data)
    
    # Run validation
    results = evaluator.run_validation(args.conf, args.iou)
    
    # Print metrics
    metrics = evaluator.print_metrics(results)
    
    # Compare with baseline
    evaluator.compare_with_baseline(metrics)
    
    # Generate report
    evaluator.generate_report(metrics, output_dir)
    
    print("\n" + "="*60)
    print("✅ Evaluation complete!")
    print("="*60)
    print(f"\n📁 Results saved to: {output_dir}")
    print(f"\n🚀 Next steps:")
    print(f"   1. Review evaluation report")
    print(f"   2. If target achieved, export model: python scripts/export_model.py")
    print(f"   3. Integrate with backend")


if __name__ == "__main__":
    main()

