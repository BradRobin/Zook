#!/usr/bin/env python3
"""
Model Export Script for Knife Detection

Export trained model to multiple formats for deployment:
- PyTorch (.pt) - default format
- ONNX (.onnx) - cross-platform, optimized
- TensorRT (.engine) - NVIDIA GPU optimization
- CoreML (.mlmodel) - iOS deployment

Usage:
    python export_model.py
    python export_model.py --format onnx
    python export_model.py --format all
    python export_model.py --model ../models/best.pt --output ../models/exports
"""

import argparse
from pathlib import Path
from ultralytics import YOLO
import shutil

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
MODELS_DIR = AI_DIR / "models"
BACKEND_MODELS_DIR = AI_DIR.parent / "backend" / "app" / "models"


class ModelExporter:
    """Export YOLO model to various formats."""
    
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"📦 Loading model: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        print(f"✅ Model loaded successfully")
    
    def export_pytorch(self, output_dir):
        """Copy PyTorch model (already in .pt format)."""
        print("\n📦 Exporting to PyTorch format...")
        
        output_path = output_dir / "knife_model.pt"
        shutil.copy2(self.model_path, output_path)
        
        file_size = output_path.stat().st_size / (1024 * 1024)
        print(f"   ✅ PyTorch model: {output_path}")
        print(f"   Size: {file_size:.2f} MB")
        
        return output_path
    
    def export_onnx(self, output_dir, simplify=True):
        """
        Export to ONNX format for cross-platform deployment.
        
        ONNX Benefits:
        - Cross-platform compatibility
        - Optimized inference
        - Smaller model size
        - Faster CPU inference
        """
        print("\n📦 Exporting to ONNX format...")
        
        try:
            export_path = self.model.export(
                format='onnx',
                simplify=simplify,
                opset=12
            )
            
            file_size = Path(export_path).stat().st_size / (1024 * 1024)
            print(f"   ✅ ONNX model: {export_path}")
            print(f"   Size: {file_size:.2f} MB")
            print(f"   Simplified: {simplify}")
            
            # Move to output directory
            dest = output_dir / Path(export_path).name
            shutil.move(export_path, dest)
            
            return dest
            
        except Exception as e:
            print(f"   ❌ ONNX export failed: {e}")
            return None
    
    def export_tensorrt(self, output_dir, device=0):
        """
        Export to TensorRT for NVIDIA GPU optimization.
        
        Requirements:
        - NVIDIA GPU
        - TensorRT installed
        - CUDA-enabled PyTorch
        """
        print("\n📦 Exporting to TensorRT format...")
        
        try:
            import torch
            if not torch.cuda.is_available():
                print("   ❌ CUDA not available! TensorRT requires NVIDIA GPU.")
                return None
            
            export_path = self.model.export(
                format='engine',
                device=device,
                half=True  # FP16 for faster inference
            )
            
            file_size = Path(export_path).stat().st_size / (1024 * 1024)
            print(f"   ✅ TensorRT model: {export_path}")
            print(f"   Size: {file_size:.2f} MB")
            print(f"   Precision: FP16 (half precision)")
            
            # Move to output directory
            dest = output_dir / Path(export_path).name
            shutil.move(export_path, dest)
            
            return dest
            
        except Exception as e:
            print(f"   ❌ TensorRT export failed: {e}")
            print("   Install TensorRT: https://docs.nvidia.com/deeplearning/tensorrt/")
            return None
    
    def export_coreml(self, output_dir):
        """
        Export to CoreML for iOS deployment.
        
        Requirements:
        - macOS (for full CoreML support)
        - coremltools installed
        """
        print("\n📦 Exporting to CoreML format...")
        
        try:
            export_path = self.model.export(format='coreml')
            
            print(f"   ✅ CoreML model: {export_path}")
            
            # Move to output directory
            dest = output_dir / Path(export_path).name
            if Path(export_path).is_dir():
                shutil.copytree(export_path, dest, dirs_exist_ok=True)
            else:
                shutil.move(export_path, dest)
            
            return dest
            
        except Exception as e:
            print(f"   ❌ CoreML export failed: {e}")
            print("   CoreML export works best on macOS")
            return None
    
    def deploy_to_backend(self, pt_path):
        """Copy PyTorch model to backend for integration."""
        print("\n🚀 Deploying to Zook backend...")
        
        BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dest = BACKEND_MODELS_DIR / "custom_knife_model.pt"
        
        shutil.copy2(pt_path, dest)
        
        file_size = dest.stat().st_size / (1024 * 1024)
        print(f"   ✅ Deployed to: {dest}")
        print(f"   Size: {file_size:.2f} MB")
        print(f"\n   Backend will automatically load this model on next restart!")
        
        return dest


def main():
    parser = argparse.ArgumentParser(
        description="Export knife detection model to multiple formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export to ONNX
  python export_model.py --format onnx
  
  # Export to all formats
  python export_model.py --format all
  
  # Export and deploy to backend
  python export_model.py --deploy
        """
    )
    
    parser.add_argument('--model', type=str, default='../models/best.pt',
                       help='Path to trained model (default: ../models/best.pt)')
    parser.add_argument('--format', choices=['pytorch', 'onnx', 'tensorrt', 'coreml', 'all'],
                       default='onnx',
                       help='Export format (default: onnx)')
    parser.add_argument('--output', type=str, default='../models/exports',
                       help='Output directory (default: ../models/exports)')
    parser.add_argument('--deploy', action='store_true',
                       help='Deploy PyTorch model to backend after export')
    parser.add_argument('--device', type=int, default=0,
                       help='GPU device for TensorRT export (default: 0)')
    
    args = parser.parse_args()
    
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Please train a model first: python scripts/train.py")
        return
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Knife Detection Model Export")
    print("="*60)
    print(f"\n📁 Output directory: {output_dir}")
    
    try:
        exporter = ModelExporter(model_path)
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    exported_files = {}
    
    # Export based on format
    if args.format == 'all':
        formats = ['pytorch', 'onnx', 'tensorrt', 'coreml']
    else:
        formats = [args.format]
    
    for fmt in formats:
        if fmt == 'pytorch':
            exported_files['pytorch'] = exporter.export_pytorch(output_dir)
        elif fmt == 'onnx':
            exported_files['onnx'] = exporter.export_onnx(output_dir)
        elif fmt == 'tensorrt':
            exported_files['tensorrt'] = exporter.export_tensorrt(output_dir, args.device)
        elif fmt == 'coreml':
            exported_files['coreml'] = exporter.export_coreml(output_dir)
    
    # Deploy to backend if requested
    if args.deploy:
        pt_path = exported_files.get('pytorch') or model_path
        exporter.deploy_to_backend(pt_path)
    
    # Summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    
    print(f"\n📦 Exported Files:")
    for fmt, path in exported_files.items():
        if path:
            file_size = Path(path).stat().st_size / (1024 * 1024) if Path(path).exists() else 0
            print(f"   {fmt:10s}: {path} ({file_size:.2f} MB)")
    
    print(f"\n🚀 Next steps:")
    if args.deploy:
        print(f"   1. Restart backend server to load custom model")
        print(f"   2. Test with: python backend/test_detection.py")
    else:
        print(f"   1. Deploy to backend: python export_model.py --deploy")
        print(f"   2. Or manually copy to: {BACKEND_MODELS_DIR}")
    
    print("\n" + "="*60)
    print("✅ Export complete!")
    print("="*60)


if __name__ == "__main__":
    main()

