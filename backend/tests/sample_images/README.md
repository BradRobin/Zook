# Sample Knife Images for Testing

This directory should contain sample knife images for testing the YOLOv11 detection endpoint.

## Obtaining Test Images

You can obtain test images from:

1. **COCO Dataset**: Download images with knife annotations from the COCO dataset
   - Visit: https://cocodataset.org/
   - Search for images with 'knife' class (class ID 43)

2. **Create Your Own**: Take photos of knives in various contexts
   - Different lighting conditions
   - Various backgrounds
   - Different knife types (kitchen knife, pocket knife, etc.)
   - Different angles and distances

3. **Public Datasets**: Search for object detection datasets with knife annotations
   - ImageNet
   - Open Images Dataset
   - Roboflow Universe

## Recommended Test Cases

Place 3-5 test images with the following characteristics:

1. **clear_knife.jpg**: High confidence scenario (knife clearly visible, good lighting)
2. **obscured_knife.jpg**: Medium confidence (knife partially obscured)
3. **no_knife.jpg**: Negative test case (no knife present)
4. **multiple_knives.jpg**: Multiple knife detection test
5. **edge_case.jpg**: Low lighting or difficult angle

## Image Specifications

- Format: JPEG
- Recommended resolution: 640x640 or similar
- File size: <2MB per image

## Usage

Once you have sample images in this directory, use the test script:

```bash
cd backend
python test_detection.py
```

The script will test all images in this directory and report detection results.

## Legal Notice

Ensure all test images are either:
- Your own original photos
- From public datasets with appropriate licenses
- Properly attributed if required by license

Do not use copyrighted images without permission.

