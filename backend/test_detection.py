#!/usr/bin/env python3
"""
Test script for YOLOv11 threat detection endpoint.

This script tests the /detect endpoint with sample images and provides
baseline accuracy metrics. It can be run locally or against a deployed service.

Usage:
    # Test against local server
    python test_detection.py
    
    # Test against remote server
    python test_detection.py --url https://your-server.com
    
    # Test specific image
    python test_detection.py --image tests/sample_images/knife.jpg
    
    # Use custom token
    python test_detection.py --token YOUR_JWT_TOKEN

Requirements:
    - Backend server running (default: http://localhost:8000)
    - Valid JWT token (will prompt for login if not provided)
    - Sample images in tests/sample_images/ directory
"""
import argparse
import requests
import json
from pathlib import Path
import sys
import time
from typing import Optional, List, Dict


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_colored(text: str, color: str):
    """Print colored text to terminal."""
    print(f"{color}{text}{Colors.END}")


def login(base_url: str, username: str, password: str) -> Optional[str]:
    """
    Login and get JWT token.
    
    Args:
        base_url: Base URL of the API
        username: Username
        password: Password
        
    Returns:
        JWT token string or None if login failed
    """
    try:
        response = requests.post(
            f"{base_url}/api/login",
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print_colored(f"Login failed: {response.status_code}", Colors.RED)
            print(response.text)
            return None
            
    except Exception as e:
        print_colored(f"Login error: {e}", Colors.RED)
        return None


def test_image(
    image_path: Path,
    base_url: str,
    token: str,
    verbose: bool = True
) -> Optional[Dict]:
    """
    Test detection on a single image.
    
    Args:
        image_path: Path to image file
        base_url: Base URL of the API
        token: JWT token
        verbose: Print detailed results
        
    Returns:
        Detection result dictionary or None if failed
    """
    if not image_path.exists():
        print_colored(f"Image not found: {image_path}", Colors.RED)
        return None
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': (image_path.name, f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {token}'}
            
            start_time = time.time()
            response = requests.post(
                f"{base_url}/detect",
                files=files,
                headers=headers
            )
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            result = response.json()
            
            if verbose:
                print_colored(f"\n{'='*60}", Colors.BLUE)
                print_colored(f"Image: {image_path.name}", Colors.BOLD)
                print(f"Processing time: {elapsed_time:.2f}ms")
                print(f"Server processing time: {result.get('processing_time_ms', 'N/A')}ms")
                
                threats = result.get('threats', [])
                if threats:
                    print_colored(f"\n⚠️  THREATS DETECTED: {len(threats)}", Colors.RED)
                    for i, threat in enumerate(threats, 1):
                        print(f"\n  Threat #{i}:")
                        print(f"    Type: {threat['type']}")
                        print(f"    Confidence: {threat['confidence']:.2%}")
                        if 'bbox' in threat and threat['bbox']:
                            bbox = threat['bbox']
                            print(f"    Bounding Box: ({bbox['x1']:.1f}, {bbox['y1']:.1f}) -> ({bbox['x2']:.1f}, {bbox['y2']:.1f})")
                else:
                    print_colored("\n✓ No threats detected", Colors.GREEN)
            
            return result
            
        elif response.status_code == 401:
            print_colored(f"Authentication failed for {image_path.name}", Colors.RED)
            print("Token may be expired. Please login again.")
            return None
        else:
            print_colored(f"Detection failed: {response.status_code}", Colors.RED)
            print(response.text)
            return None
            
    except Exception as e:
        print_colored(f"Error testing {image_path.name}: {e}", Colors.RED)
        return None


def test_directory(
    directory: Path,
    base_url: str,
    token: str
) -> List[Dict]:
    """
    Test all images in a directory.
    
    Args:
        directory: Directory containing test images
        base_url: Base URL of the API
        token: JWT token
        
    Returns:
        List of detection results
    """
    if not directory.exists():
        print_colored(f"Directory not found: {directory}", Colors.RED)
        return []
    
    # Get all image files
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.glob(f'*{ext}'))
        image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print_colored(f"No images found in {directory}", Colors.YELLOW)
        print("\nPlease add test images to tests/sample_images/")
        print("See tests/sample_images/README.md for instructions.")
        return []
    
    print_colored(f"\nTesting {len(image_files)} images from {directory}", Colors.BOLD)
    
    results = []
    for image_path in sorted(image_files):
        result = test_image(image_path, base_url, token, verbose=True)
        if result:
            results.append({
                'filename': image_path.name,
                'result': result
            })
    
    return results


def print_summary(results: List[Dict]):
    """Print summary statistics."""
    if not results:
        return
    
    print_colored(f"\n{'='*60}", Colors.BLUE)
    print_colored("SUMMARY", Colors.BOLD)
    print(f"Total images tested: {len(results)}")
    
    threats_detected = sum(1 for r in results if r['result'].get('threats'))
    print(f"Images with threats: {threats_detected}")
    print(f"Images without threats: {len(results) - threats_detected}")
    
    # Calculate average processing time
    processing_times = [r['result'].get('processing_time_ms', 0) for r in results]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
    max_time = max(processing_times) if processing_times else 0
    min_time = min(processing_times) if processing_times else 0
    
    print(f"\nProcessing times:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Min: {min_time:.2f}ms")
    print(f"  Max: {max_time:.2f}ms")
    
    # List images with detections
    if threats_detected > 0:
        print_colored("\nImages with threat detections:", Colors.YELLOW)
        for r in results:
            threats = r['result'].get('threats', [])
            if threats:
                confidence = max(t['confidence'] for t in threats)
                print(f"  • {r['filename']}: {len(threats)} threat(s), max confidence: {confidence:.2%}")


def check_health(base_url: str) -> bool:
    """Check if the detection service is healthy."""
    try:
        response = requests.get(f"{base_url}/detect/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print_colored("✓ Detection service is healthy", Colors.GREEN)
                print(f"  Model: {data.get('model_info', {}).get('architecture', 'Unknown')}")
                print(f"  Device: {data.get('model_info', {}).get('device', 'Unknown')}")
                print(f"  Threshold: {data.get('model_info', {}).get('confidence_threshold', 'Unknown')}")
                return True
        print_colored("⚠ Detection service is not healthy", Colors.YELLOW)
        return False
    except Exception as e:
        print_colored(f"✗ Cannot connect to detection service: {e}", Colors.RED)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test YOLOv11 threat detection endpoint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_detection.py
  python test_detection.py --url https://your-server.com
  python test_detection.py --image tests/sample_images/knife.jpg
  python test_detection.py --username Brad --password 12345678
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the API (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--token',
        help='JWT token (will prompt for login if not provided)'
    )
    parser.add_argument(
        '--username',
        default='Brad',
        help='Username for login (default: Brad)'
    )
    parser.add_argument(
        '--password',
        default='12345678',
        help='Password for login (default: 12345678)'
    )
    parser.add_argument(
        '--image',
        help='Test specific image file'
    )
    parser.add_argument(
        '--dir',
        default='tests/sample_images',
        help='Directory containing test images (default: tests/sample_images)'
    )
    
    args = parser.parse_args()
    
    print_colored("YOLOv11 Threat Detection Test Suite", Colors.BOLD)
    print(f"API URL: {args.url}\n")
    
    # Check service health
    if not check_health(args.url):
        print_colored("\nWarning: Service health check failed. Tests may not work.", Colors.YELLOW)
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Get JWT token
    token = args.token
    if not token:
        print_colored("\nLogging in...", Colors.BLUE)
        token = login(args.url, args.username, args.password)
        if not token:
            print_colored("Failed to obtain JWT token. Exiting.", Colors.RED)
            sys.exit(1)
        print_colored("✓ Login successful\n", Colors.GREEN)
    
    # Test specific image or directory
    if args.image:
        image_path = Path(args.image)
        result = test_image(image_path, args.url, token, verbose=True)
        if result:
            print_colored("\n✓ Test completed", Colors.GREEN)
        else:
            print_colored("\n✗ Test failed", Colors.RED)
            sys.exit(1)
    else:
        directory = Path(args.dir)
        results = test_directory(directory, args.url, token)
        print_summary(results)
        
        if results:
            print_colored("\n✓ All tests completed", Colors.GREEN)
        else:
            print_colored("\n⚠ No images tested", Colors.YELLOW)


if __name__ == '__main__':
    main()

