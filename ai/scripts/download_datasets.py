#!/usr/bin/env python3
"""
Dataset Download Script for Knife Detection Training

This script downloads and extracts knife detection datasets from various sources:
- Roboflow Universe
- Kaggle
- Open Images Dataset
- Custom sources

Usage:
    python download_datasets.py --source roboflow --api-key YOUR_KEY
    python download_datasets.py --source kaggle --dataset DATASET_NAME
    python download_datasets.py --source all
"""

import argparse
import os
import sys
import zipfile
import requests
from pathlib import Path
import json
import shutil

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = AI_DIR / "datasets" / "raw"


class DatasetDownloader:
    """Download datasets from various sources."""
    
    def __init__(self, output_dir=RAW_DATA_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {self.output_dir}")
    
    def download_roboflow(self, workspace, project, version, api_key, format="yolov11"):
        """
        Download dataset from Roboflow Universe.
        
        Args:
            workspace: Roboflow workspace name
            project: Project name
            version: Dataset version
            api_key: Roboflow API key
            format: Export format (yolov11, yolov5, coco, etc.)
        
        Example:
            downloader.download_roboflow(
                workspace="your-workspace",
                project="knife-detection",
                version=1,
                api_key="your_api_key"
            )
        """
        print(f"\n🔽 Downloading from Roboflow...")
        print(f"   Workspace: {workspace}")
        print(f"   Project: {project}")
        print(f"   Version: {version}")
        
        try:
            from roboflow import Roboflow
            
            rf = Roboflow(api_key=api_key)
            project_obj = rf.workspace(workspace).project(project)
            dataset = project_obj.version(version).download(format, location=str(self.output_dir / "roboflow"))
            
            print(f"✅ Roboflow dataset downloaded to: {dataset.location}")
            return dataset.location
            
        except ImportError:
            print("❌ Roboflow library not installed. Install with: pip install roboflow")
            print("   Or download manually from: https://universe.roboflow.com/")
            return None
        except Exception as e:
            print(f"❌ Error downloading from Roboflow: {e}")
            return None
    
    def download_kaggle(self, dataset_name, unzip=True):
        """
        Download dataset from Kaggle.
        
        Args:
            dataset_name: Kaggle dataset name (format: username/dataset-name)
            unzip: Whether to unzip the downloaded file
        
        Example:
            downloader.download_kaggle("username/knife-detection-dataset")
        
        Prerequisites:
            - Kaggle API credentials configured (~/.kaggle/kaggle.json)
            - Install: pip install kaggle
        """
        print(f"\n🔽 Downloading from Kaggle...")
        print(f"   Dataset: {dataset_name}")
        
        try:
            import kaggle
            
            output_path = self.output_dir / "kaggle" / dataset_name.split('/')[-1]
            output_path.mkdir(parents=True, exist_ok=True)
            
            kaggle.api.dataset_download_files(
                dataset_name,
                path=str(output_path),
                unzip=unzip
            )
            
            print(f"✅ Kaggle dataset downloaded to: {output_path}")
            return str(output_path)
            
        except ImportError:
            print("❌ Kaggle library not installed. Install with: pip install kaggle")
            print("   Configure API credentials: https://www.kaggle.com/docs/api")
            return None
        except Exception as e:
            print(f"❌ Error downloading from Kaggle: {e}")
            return None
    
    def download_url(self, url, filename=None):
        """
        Download file from direct URL.
        
        Args:
            url: Direct download URL
            filename: Optional custom filename
        """
        print(f"\n🔽 Downloading from URL...")
        print(f"   URL: {url}")
        
        try:
            if filename is None:
                filename = url.split("/")[-1]
            
            output_path = self.output_dir / "custom" / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(block_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end='')
            
            print(f"\n✅ Downloaded to: {output_path}")
            
            # Auto-extract if zip
            if output_path.suffix == '.zip':
                print("   Extracting...")
                with zipfile.ZipFile(output_path, 'r') as zip_ref:
                    extract_dir = output_path.parent / output_path.stem
                    zip_ref.extractall(extract_dir)
                print(f"   ✅ Extracted to: {extract_dir}")
                return str(extract_dir)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error downloading from URL: {e}")
            return None
    
    def list_downloaded(self):
        """List all downloaded datasets."""
        print("\n📋 Downloaded Datasets:")
        
        if not self.output_dir.exists() or not any(self.output_dir.iterdir()):
            print("   No datasets downloaded yet.")
            return
        
        for source_dir in self.output_dir.iterdir():
            if source_dir.is_dir():
                print(f"\n   📁 {source_dir.name}/")
                for dataset in source_dir.iterdir():
                    if dataset.is_dir():
                        # Count images
                        image_count = sum(1 for _ in dataset.rglob("*.jpg")) + sum(1 for _ in dataset.rglob("*.png"))
                        print(f"      - {dataset.name} ({image_count} images)")


def main():
    parser = argparse.ArgumentParser(
        description="Download knife detection datasets from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from Roboflow
  python download_datasets.py --source roboflow --workspace "your-workspace" --project "knife-detection" --version 1 --api-key "YOUR_API_KEY"
  
  # Download from Kaggle
  python download_datasets.py --source kaggle --dataset "username/knife-detection"
  
  # Download from URL
  python download_datasets.py --source url --url "https://example.com/dataset.zip"
  
  # List downloaded datasets
  python download_datasets.py --list
        """
    )
    
    parser.add_argument('--source', choices=['roboflow', 'kaggle', 'url', 'all'], help='Dataset source')
    parser.add_argument('--list', action='store_true', help='List downloaded datasets')
    
    # Roboflow args
    parser.add_argument('--workspace', help='Roboflow workspace name')
    parser.add_argument('--project', help='Roboflow project name')
    parser.add_argument('--version', type=int, default=1, help='Roboflow dataset version')
    parser.add_argument('--api-key', help='Roboflow API key')
    
    # Kaggle args
    parser.add_argument('--dataset', help='Kaggle dataset name (format: username/dataset-name)')
    
    # URL args
    parser.add_argument('--url', help='Direct download URL')
    parser.add_argument('--filename', help='Custom filename for URL download')
    
    args = parser.parse_args()
    
    downloader = DatasetDownloader()
    
    if args.list:
        downloader.list_downloaded()
        return
    
    if not args.source:
        parser.print_help()
        print("\n❌ Please specify a source (--source) or use --list to see downloaded datasets")
        return
    
    print("="*60)
    print("Knife Detection Dataset Downloader")
    print("="*60)
    
    if args.source == 'roboflow':
        if not all([args.workspace, args.project, args.api_key]):
            print("❌ Roboflow requires: --workspace, --project, --api-key")
            return
        downloader.download_roboflow(args.workspace, args.project, args.version, args.api_key)
    
    elif args.source == 'kaggle':
        if not args.dataset:
            print("❌ Kaggle requires: --dataset")
            return
        downloader.download_kaggle(args.dataset)
    
    elif args.source == 'url':
        if not args.url:
            print("❌ URL download requires: --url")
            return
        downloader.download_url(args.url, args.filename)
    
    elif args.source == 'all':
        print("\n📦 Downloading from all sources...")
        print("\n⚠️  This requires configuration:")
        print("   1. Set ROBOFLOW_API_KEY environment variable")
        print("   2. Configure Kaggle API credentials")
        print("   3. Add dataset URLs to the script")
        print("\nPlease download datasets individually using specific source flags.")
    
    print("\n" + "="*60)
    print("✅ Download complete!")
    print("="*60)
    print(f"\nDatasets saved to: {RAW_DATA_DIR}")
    print("\nNext steps:")
    print("  1. Verify downloaded data quality")
    print("  2. Run: python prepare_dataset.py")


if __name__ == "__main__":
    main()

