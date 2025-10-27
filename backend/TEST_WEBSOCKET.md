# Testing WebSocket Real-Time Streaming

Quick guide to test the new WebSocket streaming implementation.

## Prerequisites

- Backend server running
- Valid JWT token (from login)
- Python 3.11+ with websockets library

## Install WebSocket Client

```bash
pip install websockets pillow
```

## Test Script

Create `test_websocket_client.py`:

```python
#!/usr/bin/env python3
"""
Test WebSocket streaming client for Zook threat detection.

Usage:
    python test_websocket_client.py --token YOUR_JWT_TOKEN
```
import asyncio
import websockets
import argparse
import json
from pathlib import Path

async def test_connection(token: str):
    """Test WebSocket connection."""
    uri = f"ws://localhost:8000/ws/stream?token={token}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"\n📩 Welcome message:")
            print(json.dumps(welcome_data, indent=2))
            
            # Keep connection alive
            print("\n⏳ Connection established. Press Ctrl+C to close.")
            print("   (In real app, frontend would send frames here)")
            
            # Listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if 'threats' in data and data['threats']:
                        print(f"\n🚨 THREAT DETECTED!")
                        print(json.dumps(data, indent=2))
                    elif data.get('fps'):
                        print(f"📊 FPS: {data['fps']:.1f}, Queue: {data.get('queue_size', 0)}")
                    
                except websockets.ConnectionClosed:
                    print("\n❌ Connection closed by server")
                    break
                    
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Connection failed: {e}")
        print("   Check if token is valid and server is running")
    except Exception as e:
        print(f"\n❌ Error: {e}")

async def test_with_frames(token: str, test_image: str):
    """Test with actual image frames."""
    uri = f"ws://localhost:8000/ws/stream?token={token}"
    
    print(f"Connecting to {uri}...")
    
    try:
        # Load test image
        image_path = Path(test_image)
        if not image_path.exists():
            print(f"❌ Image not found: {test_image}")
            return
        
        with open(image_path, 'rb') as f:
            frame_bytes = f.read()
        
        print(f"✅ Loaded test image: {test_image} ({len(frame_bytes)} bytes)")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Receive welcome
            welcome = await websocket.recv()
            print(f"\n📩 {json.loads(welcome)['message']}")
            
            print("\n🎬 Sending test frames (simulating 15 FPS)...")
            
            for i in range(30):  # Send 30 frames (2 seconds at 15fps)
                # Send frame
                await websocket.send(frame_bytes)
                
                # Wait for result
                try:
                    result = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(result)
                    
                    if data.get('threats'):
                        print(f"  Frame {i+1}: 🚨 THREAT! Confidence: {data['threats'][0]['confidence']:.2%}")
                    else:
                        print(f"  Frame {i+1}: ✅ No threats (processing: {data.get('processing_time_ms', 0):.1f}ms)")
                    
                except asyncio.TimeoutError:
                    print(f"  Frame {i+1}: ⏱️  Timeout waiting for result")
                
                # Wait for next frame (15 FPS = 66ms between frames)
                await asyncio.sleep(0.066)
            
            print("\n✅ Test complete!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="Test WebSocket streaming")
    parser.add_argument('--token', required=True, help='JWT authentication token')
    parser.add_argument('--image', help='Test image path (optional)')
    
    args = parser.parse_args()
    
    if args.image:
        asyncio.run(test_with_frames(args.token, args.image))
    else:
        asyncio.run(test_connection(args.token))

if __name__ == '__main__':
    main()
```

## Get JWT Token

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"Brad","password":"12345678"}' | jq -r '.access_token'
```

Save the token output.

## Test 1: Basic Connection

```bash
python test_websocket_client.py --token YOUR_TOKEN_HERE
```

**Expected output:**
```
Connecting to ws://localhost:8000/ws/stream?token=...
✅ Connected!

📩 Welcome message:
{
  "type": "connected",
  "session_id": "uuid-here",
  "message": "Stream connected successfully",
  "target_fps": 15,
  "idle_timeout_minutes": 5.0
}

⏳ Connection established. Press Ctrl+C to close.
```

## Test 2: With Test Image

```bash
# Use a test knife image
python test_websocket_client.py --token YOUR_TOKEN_HERE --image backend/tests/sample_images/knife.jpg
```

**Expected output:**
```
✅ Loaded test image: knife.jpg (45678 bytes)
✅ Connected!

🎬 Sending test frames (simulating 15 FPS)...
  Frame 1: ✅ No threats (processing: 125.3ms)
  Frame 2: ✅ No threats (processing: 118.7ms)
  Frame 3: 🚨 THREAT! Confidence: 95.23%
  ...
✅ Test complete!
```

## Test 3: Check Service Health

```bash
curl http://localhost:8000/stream/health
```

## Test 4: Monitor Active Sessions

```bash
curl http://localhost:8000/stream/sessions
```

## Test 5: Idle Timeout

```bash
# Connect and wait 5 minutes without sending detections
# Server should auto-disconnect

python test_websocket_client.py --token YOUR_TOKEN_HERE
# Wait 5+ minutes...
# Connection should close automatically
```

## Troubleshooting

### "Connection failed: 403"
- Token is invalid or expired
- Get a new token by logging in again

### "Connection refused"
- Backend server not running
- Start with: `uvicorn app.main:app --reload --port 8000`

### "Module not found: websockets"
- Install: `pip install websockets`

### No detection results
- Check backend logs for errors
- Verify YOLOv11 model is loaded
- Try with a clear knife image

## Expected Backend Logs

When connection is established:
```
INFO: WebSocket connection attempt
INFO: WebSocket authenticated: user Brad (uuid)
INFO: WebSocket accepted for user Brad
INFO: Session created: uuid (total active: 1)
INFO: StreamProcessor created for session uuid
INFO: StreamProcessor started for session uuid
INFO: Processing loop started for session uuid
```

When frames are received:
```
INFO: Session uuid: Frame #100, FPS: 15.2, Detections: 3, Processing: 125.3ms
```

When idle timeout occurs:
```
WARNING: Session uuid: Idle timeout (5.1 min without detection)
INFO: Session removed: uuid (remaining: 0)
INFO: WebSocket cleanup complete
```

## Success Criteria

- [x] WebSocket connection establishes
- [x] Welcome message received
- [x] Frames can be sent
- [x] Detection results received
- [x] FPS tracking works
- [x] Idle timeout triggers
- [x] Graceful cleanup on disconnect

## Next Steps

After backend testing passes:
1. Update frontend to use WebSocket
2. Replace 5-second intervals with continuous streaming
3. Add recording indicator UI
4. Test end-to-end with real camera

