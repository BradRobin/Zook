#!/usr/bin/env python3
"""
Dataset Preparation Script for Knife Detection Training

This script processes raw downloaded datasets and prepares them for YOLOv11 training:
- Merges multiple datasets
- Validates annotations
- Removes corrupted/duplicate images
- Splits into train/val/test sets
- Creates data.yaml configuration

Usage:
    python prepare_dataset.py
    python prepare_dataset.py --split 0.7 0.2 0.1
    python prepare_dataset.py --augment
"""

import argparse
import shutil
import random
from pathlib import Path
from collections import defaultdict
import yaml
from PIL import Image
import hashlib

# Paths
SCRIPT_DIR = Path(__file__).parent
AI_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = AI_DIR / "datasets" / "raw"
PROCESSED_DATA_DIR = AI_DIR / "datasets" / "processed"


class DatasetPreparator:
    """Prepare and validate datasets for training."""
    
    def __init__(self, raw_dir=RAW_DATA_DIR, processed_dir=PROCESSED_DATA_DIR):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.stats = defaultdict(int)
        
        print(f"📁 Raw data: {self.raw_dir}")
        print(f"📁 Processed data: {self.processed_dir}")
    
    def find_all_images(self):
        """Find all images in raw directory."""
        print("\n🔍 Scanning for images...")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        images = []
        
        for ext in image_extensions:
            images.extend(self.raw_dir.rglob(f"*{ext}"))
            images.extend(self.raw_dir.rglob(f"*{ext.upper()}"))
        
        print(f"   Found {len(images)} images")
        self.stats['total_images'] = len(images)
        return images
    
    def find_label_for_image(self, image_path):
        """Find corresponding YOLO label file for image."""
        # Try same directory with .txt extension
        label_path = image_path.with_suffix('.txt')
        if label_path.exists():
            return label_path
        
        # Try labels/ subdirectory
        labels_dir = image_path.parent.parent / "labels" / image_path.parent.name
        if labels_dir.exists():
            label_path = labels_dir / f"{image_path.stem}.txt"
            if label_path.exists():
                return label_path
        
        return None
    
    def validate_image(self, image_path):
        """Validate image can be opened and is not corrupted."""
        try:
            img = Image.open(image_path)
            img.verify()  # Verify it's a valid image
            
            # Check dimensions
            img = Image.open(image_path)  # Re-open after verify
            width, height = img.size
            
            if width < 32 or height < 32:
                return False, "Image too small"
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def validate_label(self, label_path):
        """Validate YOLO format label file."""
        try:
            with open(label_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return True, []  # Empty label (no objects) is valid
            
            annotations = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    return False, "Invalid annotation format"
                
                class_id, x_center, y_center, width, height = map(float, parts)
                
                # Validate coordinates are normalized (0-1)
                if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 
                       0 < width <= 1 and 0 < height <= 1):
                    return False, "Coordinates out of range"
                
                annotations.append({
                    'class_id': int(class_id),
                    'bbox': [x_center, y_center, width, height]
                })
            
            return True, annotations
        except Exception as e:
            return False, str(e)
    
    def compute_hash(self, file_path):
        """Compute MD5 hash of file to detect duplicates."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def process_and_merge_datasets(self):
        """Process all raw datasets and merge them."""
        print("\n📦 Processing and merging datasets...")
        
        images = self.find_all_images()
        
        if not images:
            print("❌ No images found in raw directory!")
            print("   Please download datasets first: python download_datasets.py")
            return []
        
        valid_pairs = []
        seen_hashes = set()
        
        for i, image_path in enumerate(images, 1):
            if i % 100 == 0:
                print(f"   Processing: {i}/{len(images)}...")
            
            # Validate image
            is_valid, error = self.validate_image(image_path)
            if not is_valid:
                self.stats['corrupted_images'] += 1
                continue
            
            # Check for duplicates
            img_hash = self.compute_hash(image_path)
            if img_hash in seen_hashes:
                self.stats['duplicate_images'] += 1
                continue
            seen_hashes.add(img_hash)
            
            # Find label
            label_path = self.find_label_for_image(image_path)
            if label_path is None:
                self.stats['missing_labels'] += 1
                continue
            
            # Validate label
            is_valid, annotations = self.validate_label(label_path)
            if not is_valid:
                self.stats['invalid_labels'] += 1
                continue
            
            # Check if label contains knife class (class_id = 0 for single-class)
            has_knife = any(ann['class_id'] == 0 for ann in annotations) if annotations else False
            
            valid_pairs.append({
                'image': image_path,
                'label': label_path,
                'annotations': annotations,
                'has_object': len(annotations) > 0,
                'has_knife': has_knife
            })
            
            self.stats['valid_pairs'] += 1
            if has_knife:
                self.stats['images_with_knives'] += 1
        
        print(f"\n✅ Processed {len(images)} images")
        print(f"   Valid pairs: {len(valid_pairs)}")
        print(f"   With objects: {sum(1 for p in valid_pairs if p['has_object'])}")
        print(f"   Corrupted: {self.stats['corrupted_images']}")
        print(f"   Duplicates: {self.stats['duplicate_images']}")
        print(f"   Missing labels: {self.stats['missing_labels']}")
        print(f"   Invalid labels: {self.stats['invalid_labels']}")
        
        return valid_pairs
    
    def split_dataset(self, pairs, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
        """Split dataset into train/val/test sets."""
        print(f"\n📊 Splitting dataset ({train_ratio}/{val_ratio}/{test_ratio})...")
        
        # Shuffle
        random.shuffle(pairs)
        
        total = len(pairs)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        splits = {
            'train': pairs[:train_end],
            'val': pairs[train_end:val_end],
            'test': pairs[val_end:]
        }
        
        for split_name, split_pairs in splits.items():
            print(f"   {split_name}: {len(split_pairs)} images")
        
        return splits
    
    def copy_to_processed(self, splits):
        """Copy files to processed directory structure."""
        print("\n📂 Copying files to processed directory...")
        
        # Clear processed directory
        if self.processed_dir.exists():
            shutil.rmtree(self.processed_dir)
        
        # Create structure
        for split in ['train', 'val', 'test']:
            (self.processed_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.processed_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)
        
        # Copy files
        for split_name, pairs in splits.items():
            print(f"   Copying {split_name} set...")
            
            for i, pair in enumerate(pairs):
                # Generate unique filename
                filename = f"{split_name}_{i:05d}{pair['image'].suffix}"
                
                # Copy image
                dst_image = self.processed_dir / 'images' / split_name / filename
                shutil.copy2(pair['image'], dst_image)
                
                # Copy label
                dst_label = self.processed_dir / 'labels' / split_name / f"{Path(filename).stem}.txt"
                shutil.copy2(pair['label'], dst_label)
        
        print("   ✅ Files copied successfully")
    
    def create_data_yaml(self):
        """Create data.yaml configuration file."""
        print("\n📝 Creating data.yaml...")
        
        data_yaml = {
            'path': str(self.processed_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': 1,  # number of classes
            'names': ['knife']  # class names
        }
        
        yaml_path = self.processed_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f, default_flow_style=False)
        
        print(f"   ✅ Created: {yaml_path}")
        return yaml_path
    
    def print_summary(self, splits):
        """Print dataset summary."""
        print("\n" + "="*60)
        print("Dataset Preparation Summary")
        print("="*60)
        
        print(f"\n📊 Statistics:")
        print(f"   Total images found: {self.stats['total_images']}")
        print(f"   Valid pairs: {self.stats['valid_pairs']}")
        print(f"   Images with knives: {self.stats['images_with_knives']}")
        print(f"   Corrupted images: {self.stats['corrupted_images']}")
        print(f"   Duplicate images: {self.stats['duplicate_images']}")
        print(f"   Missing labels: {self.stats['missing_labels']}")
        print(f"   Invalid labels: {self.stats['invalid_labels']}")
        
        print(f"\n📁 Dataset Split:")
        for split_name, pairs in splits.items():
            with_knives = sum(1 for p in pairs if p['has_knife'])
            print(f"   {split_name:5s}: {len(pairs):4d} images ({with_knives} with knives)")
        
        print(f"\n✅ Processed dataset ready at:")
        print(f"   {self.processed_dir}")
        
        print(f"\n📝 Configuration file:")
        print(f"   {self.processed_dir / 'data.yaml'}")
        
        print(f"\n🚀 Next steps:")
        print(f"   1. Review dataset quality")
        print(f"   2. Run training: python scripts/train.py")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare knife detection dataset for training"
    )
    
    parser.add_argument('--split', nargs=3, type=float, default=[0.7, 0.2, 0.1],
                       metavar=('TRAIN', 'VAL', 'TEST'),
                       help='Dataset split ratios (default: 0.7 0.2 0.1)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Validate split ratios
    if abs(sum(args.split) - 1.0) > 0.001:
        print(f"❌ Split ratios must sum to 1.0 (got {sum(args.split)})")
        return
    
    random.seed(args.seed)
    
    print("="*60)
    print("Knife Detection Dataset Preparation")
    print("="*60)
    
    preparator = DatasetPreparator()
    
    # Process datasets
    valid_pairs = preparator.process_and_merge_datasets()
    
    if len(valid_pairs) < 10:
        print("\n❌ Not enough valid image-label pairs!")
        print("   Need at least 10 pairs for training.")
        print("   Please check your raw data directory and download more datasets.")
        return
    
    # Split dataset
    splits = preparator.split_dataset(valid_pairs, *args.split)
    
    # Copy to processed directory
    preparator.copy_to_processed(splits)
    
    # Create data.yaml
    preparator.create_data_yaml()
    
    # Print summary
    preparator.print_summary(splits)
    
    print("\n" + "="*60)
    print("✅ Dataset preparation complete!")
    print("="*60)


if __name__ == "__main__":
    main()

