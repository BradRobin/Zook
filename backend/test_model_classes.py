#!/usr/bin/env python3
"""
Test script to verify YOLO model classes and knife detection capability.
"""
from ultralytics import YOLO

print("="*60)
print("YOLOv11 Model Class Verification")
print("="*60)

# Load the model
print("\nLoading YOLOv11n model...")
model = YOLO('yolo11n.pt')

# Get class names
print(f"\n✓ Model loaded successfully!")
print(f"Total classes in model: {len(model.names)}")

# Find knife-related classes
print("\n" + "="*60)
print("SEARCHING FOR 'KNIFE' IN CLASS NAMES")
print("="*60)

knife_found = False
for class_id, class_name in model.names.items():
    if 'knife' in class_name.lower():
        print(f"✓ FOUND: Class ID {class_id}: '{class_name}'")
        knife_found = True

if not knife_found:
    print("✗ WARNING: No 'knife' class found in model!")

# Print kitchen/weapon related classes
print("\n" + "="*60)
print("KITCHEN & WEAPON RELATED CLASSES")
print("="*60)

kitchen_weapons = ['knife', 'fork', 'spoon', 'scissors', 'baseball', 'bat']
found_items = []
for class_id, class_name in model.names.items():
    if any(item in class_name.lower() for item in kitchen_weapons):
        found_items.append((class_id, class_name))
        print(f"Class ID {class_id:2d}: {class_name}")

if not found_items:
    print("No kitchen/weapon items found")

# Print FULL list
print("\n" + "="*60)
print("COMPLETE CLASS LIST (All 80 COCO classes)")
print("="*60)

for class_id in range(len(model.names)):
    class_name = model.names[class_id]
    marker = " ← KNIFE!" if 'knife' in class_name.lower() else ""
    print(f"{class_id:2d}: {class_name}{marker}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Total classes: {len(model.names)}")
print(f"Knife class found: {'YES' if knife_found else 'NO'}")
print(f"Kitchen/weapon items found: {len(found_items)}")

if knife_found:
    print("\n✓ The model DOES include knife detection capability!")
else:
    print("\n✗ WARNING: The model may NOT include knife detection!")
    print("   You may need to train a custom model.")

print("="*60)

