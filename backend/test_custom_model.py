#!/usr/bin/env python3
"""
Test custom knife detection model.

Compares performance and accuracy of custom model vs COCO pretrained model.

Usage:
    python test_custom_model.py
    python test_custom_model.py --test-dir tests/sample_images
    python test_custom_model.py --benchmark-only
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict
import numpy as np

# Add app to path
sys.path.append(str(Path(__file__).parent))

from app.services.detector import ThreatDetector

def load_test_images(test_dir: Path) -> List[Path]:
    """Load all test images from directory."""
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return []
    
    # Support common image formats
    extensions = ['*.jpg', '*.jpeg', '*.png']
    images = []
    for ext in extensions:
        images.extend(test_dir.glob(ext))
    
    return sorted(images)


def test_model(detector: ThreatDetector, image_path: Path) -> Dict:
    """
    Test model on a single image.
    
    Returns dict with detection results and timing.
    """
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    start_time = time.time()
    threats = detector.detect_threats(image_bytes)
    inference_time = (time.time() - start_time) * 1000  # ms
    
    return {
        'threats': threats,
        'count': len(threats),
        'confidence': threats[0].confidence if threats else 0.0,
        'time_ms': inference_time
    }


def compare_models(test_images: List[Path]):
    """
    Compare custom model vs COCO model performance.
    """
    print("="*60)
    print("MODEL COMPARISON TEST")
    print("="*60)
    
    # Load custom model
    print("\n📦 Loading custom model...")
    custom_detector = ThreatDetector(
        confidence_threshold=0.90,
        custom_model_path=Path("app/models/custom_knife_model.pt"),
        device='cpu'
    )
    print(f"✅ Custom model loaded: {custom_detector.get_model_info()}")
    
    # Load COCO model
    print("\n📦 Loading COCO pretrained model...")
    coco_detector = ThreatDetector(
        confidence_threshold=0.90,
        custom_model_path=None,  # Force COCO
        device='cpu'
    )
    # Need to create new instance since singleton
    from app.services.detector import ThreatDetector as TD2
    TD2._instance = None  # Reset singleton
    coco_detector = TD2(confidence_threshold=0.90, device='cpu')
    print(f"✅ COCO model loaded: {coco_detector.get_model_info()}")
    
    if not test_images:
        print("\n⚠️  No test images found!")
        return
    
    print(f"\n🧪 Testing on {len(test_images)} images...")
    
    # Results storage
    custom_results = {
        'detections': 0,
        'total_confidence': 0.0,
        'total_time': 0.0,
        'times': []
    }
    
    coco_results = {
        'detections': 0,
        'total_confidence': 0.0,
        'total_time': 0.0,
        'times': []
    }
    
    # Test each image
    for i, image_path in enumerate(test_images, 1):
        print(f"\n  [{i}/{len(test_images)}] {image_path.name}")
        
        # Test custom model
        custom_result = test_model(custom_detector, image_path)
        custom_results['times'].append(custom_result['time_ms'])
        custom_results['total_time'] += custom_result['time_ms']
        
        if custom_result['count'] > 0:
            custom_results['detections'] += 1
            custom_results['total_confidence'] += custom_result['confidence']
            print(f"    Custom: ✓ Detected ({custom_result['confidence']:.2%}, {custom_result['time_ms']:.1f}ms)")
        else:
            print(f"    Custom: ✗ Not detected ({custom_result['time_ms']:.1f}ms)")
        
        # Test COCO model
        coco_result = test_model(coco_detector, image_path)
        coco_results['times'].append(coco_result['time_ms'])
        coco_results['total_time'] += coco_result['time_ms']
        
        if coco_result['count'] > 0:
            coco_results['detections'] += 1
            coco_results['total_confidence'] += coco_result['confidence']
            print(f"    COCO:   ✓ Detected ({coco_result['confidence']:.2%}, {coco_result['time_ms']:.1f}ms)")
        else:
            print(f"    COCO:   ✗ Not detected ({coco_result['time_ms']:.1f}ms)")
    
    # Calculate statistics
    print("\n" + "="*60)
    print("RESULTS COMPARISON")
    print("="*60)
    
    print("\n📊 Custom Model:")
    print(f"   Detections: {custom_results['detections']}/{len(test_images)} ({custom_results['detections']/len(test_images)*100:.1f}%)")
    if custom_results['detections'] > 0:
        print(f"   Avg Confidence: {custom_results['total_confidence']/custom_results['detections']:.2%}")
    print(f"   Avg Time: {custom_results['total_time']/len(test_images):.1f}ms")
    print(f"   Min Time: {min(custom_results['times']):.1f}ms")
    print(f"   Max Time: {max(custom_results['times']):.1f}ms")
    
    print("\n📊 COCO Model:")
    print(f"   Detections: {coco_results['detections']}/{len(test_images)} ({coco_results['detections']/len(test_images)*100:.1f}%)")
    if coco_results['detections'] > 0:
        print(f"   Avg Confidence: {coco_results['total_confidence']/coco_results['detections']:.2%}")
    print(f"   Avg Time: {coco_results['total_time']/len(test_images):.1f}ms")
    print(f"   Min Time: {min(coco_results['times']):.1f}ms")
    print(f"   Max Time: {max(coco_results['times']):.1f}ms")
    
    # Improvement analysis
    print("\n📈 Improvement:")
    detection_improvement = custom_results['detections'] - coco_results['detections']
    if detection_improvement > 0:
        print(f"   Detection Rate: +{detection_improvement} images ({detection_improvement/len(test_images)*100:.1f}% improvement)")
    elif detection_improvement < 0:
        print(f"   Detection Rate: {detection_improvement} images ({abs(detection_improvement)/len(test_images)*100:.1f}% worse)")
    else:
        print(f"   Detection Rate: Same")
    
    if custom_results['detections'] > 0 and coco_results['detections'] > 0:
        conf_improvement = (custom_results['total_confidence']/custom_results['detections']) - (coco_results['total_confidence']/coco_results['detections'])
        print(f"   Avg Confidence: {conf_improvement:+.2%}")
    
    time_diff = (custom_results['total_time']/len(test_images)) - (coco_results['total_time']/len(test_images))
    print(f"   Inference Time: {time_diff:+.1f}ms")


def benchmark_model(detector: ThreatDetector, iterations: int = 100):
    """
    Benchmark model performance.
    """
    print("="*60)
    print("MODEL BENCHMARKING")
    print("="*60)
    
    model_info = detector.get_model_info()
    print(f"\nModel: {model_info['model_type']} (class ID: {model_info['knife_class_id']})")
    print(f"Device: {model_info['device']}")
    print(f"Threshold: {model_info['confidence_threshold']}")
    
    # Create test image
    print(f"\n🔥 Warming up ({iterations//10} iterations)...")
    test_image_bytes = Path("tests/sample_images").glob("*.jpg").__next__()
    if test_image_bytes:
        with open(test_image_bytes, 'rb') as f:
            image_bytes = f.read()
    else:
        # Create random image
        from PIL import Image
        from io import BytesIO
        img = Image.fromarray(np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8))
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
    
    # Warmup
    for _ in range(iterations//10):
        detector.detect_threats(image_bytes)
    
    # Benchmark
    print(f"⏱️  Running benchmark ({iterations} iterations)...")
    times = []
    for _ in range(iterations):
        start = time.time()
        detector.detect_threats(image_bytes)
        times.append((time.time() - start) * 1000)
    
    # Statistics
    times = np.array(times)
    
    print("\n📈 Performance Statistics:")
    print(f"   Mean: {np.mean(times):.2f}ms")
    print(f"   Median: {np.median(times):.2f}ms")
    print(f"   Std Dev: {np.std(times):.2f}ms")
    print(f"   Min: {np.min(times):.2f}ms")
    print(f"   Max: {np.max(times):.2f}ms")
    print(f"   P95: {np.percentile(times, 95):.2f}ms")
    print(f"   P99: {np.percentile(times, 99):.2f}ms")
    
    # FPS calculation
    fps = 1000 / np.mean(times)
    print(f"\n🎬 Estimated FPS: {fps:.1f}")
    
    # Assessment
    print("\n🎯 Performance Assessment:")
    mean_time = np.mean(times)
    if mean_time < 50:
        print("   ✅ Excellent! (<50ms per frame)")
    elif mean_time < 100:
        print("   ✅ Good! (<100ms per frame)")
    elif mean_time < 200:
        print("   ⚠️  Acceptable, but slow (100-200ms)")
    else:
        print("   ❌ Too slow (>200ms). Consider GPU or smaller model.")


def main():
    parser = argparse.ArgumentParser(description="Test custom knife detection model")
    parser.add_argument(
        '--test-dir',
        type=str,
        default='tests/sample_images',
        help='Directory with test images'
    )
    parser.add_argument(
        '--benchmark-only',
        action='store_true',
        help='Only run benchmark, skip comparison'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of benchmark iterations'
    )
    
    args = parser.parse_args()
    
    test_dir = Path(args.test_dir)
    
    if args.benchmark_only:
        # Only benchmark custom model
        print("Loading custom model for benchmarking...")
        detector = ThreatDetector(
            confidence_threshold=0.90,
            custom_model_path=Path("app/models/custom_knife_model.pt"),
            device='cpu'
        )
        benchmark_model(detector, args.iterations)
    else:
        # Full comparison
        test_images = load_test_images(test_dir)
        if not test_images:
            print(f"\n⚠️  No test images found in {test_dir}")
            print("   Please add some knife images for testing")
            return
        
        compare_models(test_images)
        
        # Also run benchmark
        print("\n")
        detector = ThreatDetector(
            confidence_threshold=0.90,
            custom_model_path=Path("app/models/custom_knife_model.pt"),
            device='cpu'
        )
        benchmark_model(detector, args.iterations)


if __name__ == '__main__':
    main()

