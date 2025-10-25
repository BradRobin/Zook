"""
YOLOv11-based threat detection service for real-time knife detection.

This module provides a singleton ThreatDetector class that uses YOLOv11n model
for efficient real-time object detection. The detector is optimized for speed
(<30ms per frame on mid-tier GPU) while maintaining high accuracy (>90% confidence).

Model Information:
- Default: YOLOv11n (nano) pretrained on COCO dataset
- Knife class ID: 43 in COCO dataset
- Custom models can be loaded by placing them in app/models/ directory
"""
import logging
from typing import List, Optional, Tuple
from pathlib import Path
from io import BytesIO
import time

from PIL import Image
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class ThreatDetection:
    """
    Data class for a single threat detection result.
    
    Attributes:
        type: Type of threat detected (e.g., 'knife')
        confidence: Detection confidence score (0.0 to 1.0)
        bbox: Bounding box coordinates [x1, y1, x2, y2] in pixels (optional)
    """
    def __init__(
        self, 
        threat_type: str, 
        confidence: float,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ):
        self.type = threat_type
        self.confidence = confidence
        self.bbox = bbox
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": self.type,
            "confidence": round(self.confidence, 4)
        }
        if self.bbox:
            result["bbox"] = {
                "x1": round(self.bbox[0], 2),
                "y1": round(self.bbox[1], 2),
                "x2": round(self.bbox[2], 2),
                "y2": round(self.bbox[3], 2)
            }
        return result


class ThreatDetector:
    """
    Singleton YOLOv11 threat detector for real-time knife detection.
    
    The detector uses YOLOv11n (nano variant) for fast inference while maintaining
    high accuracy. It filters detections to only return threats with confidence
    above the specified threshold.
    
    Custom Training:
        To use a custom-trained model for improved accuracy:
        1. Train your model: yolo train data=knife_data.yaml model=yolo11n.pt epochs=100
        2. Place trained model in backend/app/models/custom_knife_model.pt
        3. Update CUSTOM_MODEL_PATH or pass custom_model_path in __init__
        4. Aim for >95% mAP on validation set
    
    Performance:
        - Target: <30ms per frame on mid-tier GPU (GTX 1660, RTX 3060)
        - Input: 640x640 RGB images
        - Output: Filtered detections with confidence >= threshold
    """
    
    _instance: Optional['ThreatDetector'] = None
    
    # COCO dataset class IDs
    KNIFE_CLASS_ID = 43  # 'knife' in COCO dataset
    COCO_CLASSES = {
        43: 'knife'
    }
    
    # Model paths
    CUSTOM_MODEL_PATH = Path(__file__).parent.parent / "models" / "custom_knife_model.pt"
    
    def __new__(cls, confidence_threshold=0.90, custom_model_path=None, device='cpu'):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ThreatDetector, cls).__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        confidence_threshold: float = 0.90,
        custom_model_path: Optional[Path] = None,
        device: str = 'cpu'
    ):
        """
        Initialize the threat detector with YOLOv11 model.
        
        Args:
            confidence_threshold: Minimum confidence score to report detection (default: 0.90)
            custom_model_path: Optional path to custom trained model
            device: Device to run inference on ('cpu', 'cuda', 'mps')
        """
        # Only initialize once (singleton)
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.confidence_threshold = confidence_threshold
        self.device = device
        self._initialized = False
        
        # Determine which model to use
        model_path = custom_model_path or self.CUSTOM_MODEL_PATH
        
        if model_path and model_path.exists():
            logger.info(f"Loading custom trained model from {model_path}")
            self.model_type = "custom"
            self.model = YOLO(str(model_path))
        else:
            logger.info("Loading pretrained YOLOv11n model from Ultralytics")
            self.model_type = "pretrained"
            # YOLOv11n will be downloaded automatically on first use
            self.model = YOLO('yolo11n.pt')
        
        # Move model to specified device
        self.model.to(self.device)
        logger.info(f"Model loaded on device: {self.device}")
        
        # Warmup: run a dummy inference to initialize CUDA/model
        self._warmup()
        
        self._initialized = True
        logger.info(f"ThreatDetector initialized (threshold: {confidence_threshold})")
    
    def _warmup(self):
        """
        Perform warmup inference to initialize model and CUDA kernels.
        This ensures consistent performance on first real inference.
        """
        logger.info("Warming up model...")
        dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
        try:
            _ = self.model.predict(
                dummy_image,
                conf=self.confidence_threshold,
                verbose=False,
                imgsz=640
            )
            logger.info("Model warmup completed")
        except Exception as e:
            logger.warning(f"Warmup failed (non-critical): {e}")
    
    def detect_threats(
        self,
        image_bytes: bytes,
        return_bbox: bool = True
    ) -> List[ThreatDetection]:
        """
        Detect knife threats in an image.
        
        Args:
            image_bytes: Raw image bytes (JPEG format)
            return_bbox: Whether to include bounding box coordinates in results
            
        Returns:
            List of ThreatDetection objects for knives detected with confidence >= threshold
            
        Raises:
            ValueError: If image cannot be decoded or processed
            RuntimeError: If model inference fails
        """
        start_time = time.time()
        
        try:
            # Load and preprocess image
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed (handle RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to YOLO input size (640x640)
            # YOLO will handle this internally, but we do it for consistency
            image = image.resize((640, 640), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            image_array = np.array(image)
            
            logger.info(f"Image preprocessed: shape={image_array.shape}, dtype={image_array.dtype}")
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ValueError(f"Invalid image data: {str(e)}")
        
        try:
            # Run inference
            # TEMPORARY DEBUG MODE: Detect ALL classes to see what model finds
            results = self.model.predict(
                image_array,
                conf=0.25,  # Lower threshold to 25% for debugging
                # classes=[self.KNIFE_CLASS_ID],  # COMMENTED OUT - detect all classes for now
                verbose=False,
                imgsz=640
            )
            
            logger.info(f"[DEBUG MODE] Detecting ALL classes with 25% confidence threshold")
            
            inference_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Inference completed in {inference_time:.2f}ms")
            
            # Parse results
            threats = []
            
            if len(results) > 0:
                result = results[0]  # Single image inference
                
                # Extract detections
                boxes = result.boxes
                
                if boxes is not None and len(boxes) > 0:
                    logger.info(f"YOLO detected {len(boxes)} object(s) in frame")
                    for box in boxes:
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        # Get class name from model
                        class_name = self.model.names.get(class_id, f"unknown_{class_id}")
                        
                        # Log ALL detections for debugging
                        logger.info(f"Detection: class_id={class_id} ({class_name}), confidence={confidence:.2%}")
                        
                        # Double-check it's a knife (should always be true due to classes filter)
                        if class_id == self.KNIFE_CLASS_ID and confidence >= self.confidence_threshold:
                            bbox = None
                            if return_bbox:
                                # Get bounding box in xyxy format
                                xyxy = box.xyxy[0].cpu().numpy()
                                bbox = tuple(map(float, xyxy))
                            
                            threat = ThreatDetection(
                                threat_type='knife',
                                confidence=confidence,
                                bbox=bbox
                            )
                            threats.append(threat)
                            
                            logger.info(f"✓ Knife detected with {confidence:.2%} confidence (ABOVE threshold)")
                        else:
                            if class_id == self.KNIFE_CLASS_ID:
                                logger.info(f"✗ Knife detected with {confidence:.2%} confidence (BELOW 90% threshold)")
                else:
                    logger.info("YOLO returned 0 detections for this frame")
            
            if threats:
                logger.warning(f"THREAT ALERT: {len(threats)} knife(s) detected")
            else:
                logger.info("No threats detected (confidence below 90% or no knife in frame)")
            
            return threats
            
        except Exception as e:
            logger.error(f"Model inference failed: {e}", exc_info=True)
            raise RuntimeError(f"Detection failed: {str(e)}")
    
    def update_threshold(self, new_threshold: float):
        """
        Update the confidence threshold dynamically.
        
        Args:
            new_threshold: New confidence threshold (0.0 to 1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        old_threshold = self.confidence_threshold
        self.confidence_threshold = new_threshold
        logger.info(f"Confidence threshold updated: {old_threshold} -> {new_threshold}")
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_type": self.model_type,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "target_classes": ["knife"],
            "input_size": "640x640",
            "architecture": "YOLOv11n"
        }


# Singleton instance holder
_detector_instance: Optional[ThreatDetector] = None


def get_detector(
    confidence_threshold: float = 0.90,
    device: str = 'cpu'
) -> ThreatDetector:
    """
    Get or create the singleton ThreatDetector instance.
    
    This function ensures only one detector instance exists throughout
    the application lifecycle, avoiding multiple model loads.
    
    Args:
        confidence_threshold: Minimum confidence for detections (default: 0.90)
        device: Device for inference ('cpu', 'cuda', 'mps')
        
    Returns:
        ThreatDetector singleton instance
    """
    global _detector_instance
    
    if _detector_instance is None:
        logger.info("Creating new ThreatDetector instance")
        _detector_instance = ThreatDetector(
            confidence_threshold=confidence_threshold,
            device=device
        )
    
    return _detector_instance

