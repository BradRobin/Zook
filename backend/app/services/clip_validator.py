"""
CLIP-based validation service for secondary threat verification.

Uses OpenAI's CLIP model to re-analyze detection frames and validate
whether they truly contain weapons/threats. Helps reduce false positives
by providing a secondary validation layer on top of YOLO detections.
"""
import logging
import asyncio
import os
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)


class CLIPValidator:
    """
    CLIP-based validator for threat detection verification.
    
    Uses zero-shot classification to determine if detected objects
    are actually weapons/threats or false positives.
    """
    
    _instance: Optional['CLIPValidator'] = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: str = 'cpu',
        confidence_threshold: float = 0.90
    ):
        """
        Initialize CLIP validator.
        
        Args:
            model_name: HuggingFace model name for CLIP
            device: Device to run inference on ('cpu', 'cuda', 'mps')
            confidence_threshold: Minimum confidence to consider valid threat
        """
        # Only initialize once (singleton)
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.model_name = model_name
        self.device = device
        self.confidence_threshold = confidence_threshold
        self._initialized = False
        
        try:
            logger.info(f"Loading CLIP model: {model_name}")
            self.model = CLIPModel.from_pretrained(model_name)
            self.processor = CLIPProcessor.from_pretrained(model_name)
            
            # Move model to device
            self.model.to(self.device)
            self.model.eval()
            
            # Define text prompts for classification
            self.threat_prompts = [
                "a photo of a knife weapon",
                "a photo of a sharp blade",
                "a photo of a dangerous weapon",
                "a photo of a threatening object"
            ]
            
            self.safe_prompts = [
                "a photo of a kitchen utensil",
                "a photo of a harmless object",
                "a photo of a person without weapons",
                "a photo of a safe scene"
            ]
            
            self._initialized = True
            logger.info(f"CLIP validator initialized successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CLIP validator: {e}", exc_info=True)
            raise
    
    def extract_frames_from_video(
        self,
        video_path: str,
        num_frames: int = 10
    ) -> List[Image.Image]:
        """
        Extract frames from video file for analysis.
        
        Args:
            video_path: Path to MP4 video file
            num_frames: Number of frames to extract (evenly spaced)
            
        Returns:
            List of PIL Images
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                logger.warning(f"Video has 0 frames: {video_path}")
                return frames
            
            # Calculate frame indices to extract (evenly spaced)
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    frames.append(pil_image)
                else:
                    logger.warning(f"Failed to read frame {idx} from {video_path}")
            
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            
        finally:
            cap.release()
        
        return frames
    
    def classify_image(
        self,
        image: Image.Image
    ) -> Tuple[float, str]:
        """
        Classify a single image as threat or safe.
        
        Args:
            image: PIL Image to classify
            
        Returns:
            Tuple of (confidence_score, label) where:
            - confidence_score: 0.0-1.0 (higher = more confident it's a threat)
            - label: 'threat' or 'safe'
        """
        try:
            # Combine all prompts
            all_prompts = self.threat_prompts + self.safe_prompts
            
            # Process inputs
            inputs = self.processor(
                text=all_prompts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Calculate threat probability (average of threat prompts)
            threat_probs = probs[0, :len(self.threat_prompts)]
            safe_probs = probs[0, len(self.threat_prompts):]
            
            threat_score = threat_probs.mean().item()
            safe_score = safe_probs.mean().item()
            
            # Normalize to get confidence
            total = threat_score + safe_score
            threat_confidence = threat_score / total if total > 0 else 0.5
            
            label = 'threat' if threat_confidence >= 0.5 else 'safe'
            
            return threat_confidence, label
            
        except Exception as e:
            logger.error(f"Image classification failed: {e}", exc_info=True)
            # Return neutral result on error
            return 0.5, 'unknown'
    
    def validate_video(
        self,
        video_path: str,
        num_frames: int = 10
    ) -> Tuple[float, int, int]:
        """
        Validate entire video by analyzing multiple frames.
        
        Args:
            video_path: Path to MP4 video file
            num_frames: Number of frames to analyze
            
        Returns:
            Tuple of (avg_confidence, threat_count, total_analyzed)
        """
        try:
            # Extract frames
            frames = self.extract_frames_from_video(video_path, num_frames)
            
            if not frames:
                logger.warning(f"No frames extracted from {video_path}")
                return 0.0, 0, 0
            
            # Classify each frame
            confidences = []
            threat_count = 0
            
            for i, frame in enumerate(frames):
                confidence, label = self.classify_image(frame)
                confidences.append(confidence)
                
                if label == 'threat':
                    threat_count += 1
                
                logger.debug(f"Frame {i}: confidence={confidence:.3f}, label={label}")
            
            # Calculate average confidence
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            logger.info(
                f"Video validation complete: {video_path} - "
                f"avg_confidence={avg_confidence:.3f}, "
                f"threat_frames={threat_count}/{len(frames)}"
            )
            
            return float(avg_confidence), threat_count, len(frames)
            
        except Exception as e:
            logger.error(f"Video validation failed for {video_path}: {e}", exc_info=True)
            return 0.0, 0, 0
    
    async def validate_video_async(
        self,
        video_path: str,
        num_frames: int = 10
    ) -> Tuple[float, int, int]:
        """
        Async wrapper for video validation.
        
        Runs validation in executor to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.validate_video,
            video_path,
            num_frames
        )
    
    def is_valid_threat(self, confidence: float) -> bool:
        """
        Determine if confidence score indicates a valid threat.
        
        Args:
            confidence: Confidence score from 0.0 to 1.0
            
        Returns:
            True if confidence >= threshold
        """
        return confidence >= self.confidence_threshold
    
    def get_validator_info(self) -> dict:
        """Get information about the validator."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "threat_prompts": self.threat_prompts,
            "safe_prompts": self.safe_prompts,
            "initialized": self._initialized
        }


# Singleton instance holder
_validator_instance: Optional[CLIPValidator] = None


def get_clip_validator(device: str = 'cpu') -> CLIPValidator:
    """
    Get or create the global CLIP validator instance.
    
    Args:
        device: Device to run inference on
        
    Returns:
        CLIPValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CLIPValidator(device=device)
    return _validator_instance

