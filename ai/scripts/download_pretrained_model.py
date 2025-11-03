#!/usr/bin/env python3
"""
Download pre-trained knife/weapon detection models.

This script helps download publicly available YOLOv11/v8 models
trained for weapon/knife detection, avoiding the need to train from scratch.

Usage:
    python download_pretrained_model.py --list
    python download_pretrained_model.py --source roboflow --dataset weapon-detection-pgqnr
    python download_pretrained_model.py --url https://example.com/model.pt
    python download_pretrained_model.py --auto
"""

import argparse
import requests
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
MODELS_DIR = AI_DIR / "models"

# Known public models (examples - users should verify and update)
PUBLIC_MODELS = {
    'example_weapons': {
        'name': 'Example Weapons Detection YOLOv8',
        'url': 'https://github.com/example/weapon-detection/releases/download/v1.0/best.pt',
        'description': 'Pre-trained on 1000+ weapon images including knives',
        'accuracy': '~85% mAP@0.5',
        'classes': ['knife', 'gun', 'scissors'],
        'verified': False
    },
}


def list_available_models():
    """List known public models."""
    print("="*70)
    print("Available Pre-trained Models")
    print("="*70)
    print("\n⚠️  Note: These are examples. You should:")
    print("   1. Search Roboflow Universe for 'knife detection' models")
    print("   2. Check Ultralytics Hub (hub.ultralytics.com)")
    print("   3. Search GitHub for 'yolo weapon detection model'")
    print("\n" + "="*70)
    
    for key, model in PUBLIC_MODELS.items():
        verified = "✅" if model['verified'] else "⚠️ "
        print(f"\n{verified} {model['name']}")
        print(f"   Description: {model['description']}")
        print(f"   Accuracy: {model['accuracy']}")
        print(f"   Classes: {', '.join(model['classes'])}")
        print(f"   URL: {model['url']}")
        print(f"   Download: python download_pretrained_model.py --model {key}")


def download_from_url(url: str, output_path: Path) -> bool:
    """
    Download model from direct URL.
    
    Args:
        url: Direct download URL
        output_path: Where to save the model
        
    Returns:
        True if successful
    """
    print(f"\n📥 Downloading model from URL...")
    print(f"   URL: {url}")
    print(f"   Saving to: {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total_size) * 100
                    print(f"\r   Progress: {progress:.1f}%", end='', flush=True)
        
        print("\n✅ Download complete!")
        print(f"   File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return False


def download_from_roboflow_trained(workspace: str, project: str, version: int, api_key: str) -> bool:
    """
    Download trained model from Roboflow if available.
    
    Note: This requires the project to have a trained model available.
    Not all Roboflow projects provide downloadable trained models.
    """
    print(f"\n📥 Attempting to download from Roboflow...")
    print(f"   Workspace: {workspace}")
    print(f"   Project: {project}")
    print(f"   Version: {version}")
    
    try:
        from roboflow import Roboflow
        
        rf = Roboflow(api_key=api_key)
        project_obj = rf.workspace(workspace).project(project)
        version_obj = project_obj.version(version)
        
        # Try to download trained model
        # Note: Not all projects have this available
        print("\n⚠️  Roboflow API doesn't directly support downloading trained models.")
        print("   Please download manually from the Roboflow web interface:")
        print(f"   1. Go to: https://universe.roboflow.com/{workspace}/{project}/dataset/{version}")
        print("   2. Click 'Train' or 'Deploy' tab")
        print("   3. Download the trained model (.pt file)")
        print("   4. Save to: ai/models/best.pt")
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def auto_search_models():
    """
    Provide instructions for finding models automatically.
    """
    print("="*70)
    print("How to Find Pre-trained Models")
    print("="*70)
    
    print("\n🔍 Method 1: Roboflow Universe")
    print("   1. Go to: https://universe.roboflow.com")
    print("   2. Search: 'knife detection' or 'weapon detection'")
    print("   3. Click on a dataset")
    print("   4. Look for 'Train' or 'Deploy' tab")
    print("   5. If available, download the trained model (.pt file)")
    
    print("\n🔍 Method 2: Ultralytics Hub")
    print("   1. Go to: https://hub.ultralytics.com")
    print("   2. Browse 'Models' section")
    print("   3. Search for 'weapon' or 'knife'")
    print("   4. Download YOLOv11 or YOLOv8 model")
    
    print("\n🔍 Method 3: GitHub")
    print("   1. Search GitHub: 'yolo weapon detection model'")
    print("   2. Look for repositories with releases")
    print("   3. Download .pt files from releases")
    print("   4. Popular repos often have:")
    print("      - yolov8-weapon-detection")
    print("      - knife-detection-yolo")
    
    print("\n🔍 Method 4: Your Roboflow Dataset")
    print("   Dataset: weapon-detection-pgqnr")
    print("   1. Go to: https://universe.roboflow.com/weapon-rcjrw/weapon-detection-pgqnr/dataset/8")
    print("   2. Check if 'Train' tab shows a trained model")
    print("   3. If yes, download the .pt file")
    print("   4. If no, use another method")
    
    print("\n💡 After downloading:")
    print("   1. Save model to: ai/models/best.pt")
    print("   2. Run: python scripts/deploy_model.py --model models/best.pt")
    print("   3. Restart backend and test!")
    
    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Download pre-trained knife/weapon detection models"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available pre-trained models'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Download specific model by key (use --list to see options)'
    )
    parser.add_argument(
        '--url',
        type=str,
        help='Download from direct URL'
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['roboflow', 'github', 'ultralytics'],
        help='Download source'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        help='Dataset name (for Roboflow)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key (for Roboflow)'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Show auto-search instructions'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='models/downloaded_model.pt',
        help='Output path for downloaded model'
    )
    
    args = parser.parse_args()
    
    # Ensure models directory exists
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.list:
        list_available_models()
        return
    
    if args.auto:
        auto_search_models()
        return
    
    output_path = AI_DIR / args.output
    
    if args.url:
        success = download_from_url(args.url, output_path)
        if success:
            print(f"\n✅ Model downloaded to: {output_path}")
            print("\nNext steps:")
            print(f"   1. Deploy: python scripts/deploy_model.py --model {args.output}")
            print("   2. Restart backend")
            print("   3. Test detection!")
        return
    
    if args.model:
        if args.model not in PUBLIC_MODELS:
            print(f"❌ Unknown model: {args.model}")
            print("   Use --list to see available models")
            return
        
        model_info = PUBLIC_MODELS[args.model]
        success = download_from_url(model_info['url'], output_path)
        if success:
            print(f"\n✅ Downloaded: {model_info['name']}")
            print(f"   Accuracy: {model_info['accuracy']}")
            print(f"   Classes: {', '.join(model_info['classes'])}")
        return
    
    # Default: show search instructions
    print("No download method specified.")
    print("Use one of these options:\n")
    print("  --list          : List known models")
    print("  --auto          : Show how to find models")
    print("  --url <URL>     : Download from direct URL")
    print("  --model <key>   : Download known model")
    print("\nFor help: python download_pretrained_model.py --help")


if __name__ == '__main__':
    main()


