"""
ConceptAttention Model Wrapper for Phase 2 Saliency Integration
Integrates ConceptAttentionFluxPipeline for zero-shot saliency detection
"""

import torch
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import logging
from dataclasses import dataclass
import cv2
from PIL import Image
import warnings
import time
from functools import lru_cache

# Import cache manager for SSD optimization
from src.config.cache_manager import setup_hf_cache_from_env

# Suppress warnings from ConceptAttention model
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


@dataclass
class SaliencyOutput:
    """Output from ConceptAttention saliency generation"""

    saliency_map: np.ndarray  # Combined saliency map (H, W) with values 0-1
    concept_maps: Dict[str, np.ndarray]  # Individual concept maps
    processing_time: float  # Time taken for processing
    confidence_score: float  # Overall confidence in saliency detection
    concepts_used: List[str]  # Concepts actually used for saliency


class ConceptAttentionModel:
    """
    Production-ready wrapper for ConceptAttention model
    Generates emotion-guided saliency maps for therapeutic art processing
    """

    def __init__(
        self,
        model_name: str = "flux-schnell",
        device: str = "auto",
        cache_size: int = 128,
        enable_optimization: bool = True,
        max_concepts: int = 8,
    ):
        """
        Initialize ConceptAttention model wrapper

        Args:
            model_name: ConceptAttention model to use ("flux-schnell" recommended)
            device: Device for inference ("auto", "cuda", "cpu", "mps")
            cache_size: Size of concept processing cache
            enable_optimization: Enable performance optimizations
            max_concepts: Maximum number of concepts to process simultaneously
        """
        # Setup logging FIRST
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Setup Hugging Face cache configuration for SSD optimization
        cache_info = setup_hf_cache_from_env()
        self.logger.info(f"Cache configured: {cache_info.get('hf_home', 'default')}")

        self.model_name = model_name
        self.device = self._setup_device(device)
        self.cache_size = cache_size
        self.enable_optimization = enable_optimization
        self.max_concepts = max_concepts

        # Initialize model and caches
        self.model = None
        self.concept_cache = {}
        self.processing_stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "total_time": 0.0,
            "average_time": 0.0,
        }

        # Initialize model
        self._initialize_model()

    def _setup_device(self, device: str) -> str:
        """Setup and validate device for inference"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        # Validate device availability
        if device == "cuda" and not torch.cuda.is_available():
            self.logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
        elif device == "mps" and (
            not hasattr(torch.backends, "mps") or not torch.backends.mps.is_available()
        ):
            self.logger.warning("MPS requested but not available, falling back to CPU")
            device = "cpu"

        self.logger.info(f"ConceptAttention initialized on device: {device}")
        return device

    def _initialize_model(self):
        """Initialize the ConceptAttention model with error handling"""
        # Check for mock mode first
        if self.model_name == "mock":
            self.logger.info("Using mock ConceptAttention for development")
            try:
                from external.concept_attention_minimal import (
                    ConceptAttentionFluxPipeline,
                )

                self.logger.info("Loading mock ConceptAttention model...")
                start_time = time.time()

                # Initialize with mock model
                self.model = ConceptAttentionFluxPipeline(
                    model_name="mock", device=self.device
                )

                load_time = time.time() - start_time
                self.logger.info(
                    f"Mock ConceptAttention model loaded in {load_time:.2f}s"
                )
                self.use_minimal = True
                return

            except Exception as mock_e:
                self.logger.error(
                    f"Failed to initialize mock ConceptAttention: {mock_e}"
                )
                raise RuntimeError(
                    f"Mock ConceptAttention initialization failed: {mock_e}"
                )

        # Try full package for non-mock models
        try:
            # Try to import full ConceptAttention package first
            from concept_attention import ConceptAttentionFluxPipeline

            self.logger.info(f"Loading ConceptAttention model: {self.model_name}")
            start_time = time.time()

            # Initialize the pipeline
            self.model = ConceptAttentionFluxPipeline(
                model_name=self.model_name, device=self.device
            )

            load_time = time.time() - start_time
            self.logger.info(f"ConceptAttention model loaded in {load_time:.2f}s")
            self.use_minimal = False

            # Warm up model with dummy input if optimization enabled
            if self.enable_optimization:
                self._warmup_model()

        except ImportError as e:
            self.logger.warning(f"Full ConceptAttention package not found: {e}")
            self.logger.info(
                "Falling back to minimal ConceptAttention implementation..."
            )

            try:
                # Try to use our minimal implementation
                from external.concept_attention_minimal import (
                    ConceptAttentionFluxPipeline,
                )

                self.logger.info(
                    f"Loading minimal ConceptAttention model: {self.model_name}"
                )
                start_time = time.time()

                # Initialize the minimal pipeline
                self.model = ConceptAttentionFluxPipeline(
                    model_name=self.model_name, device=self.device
                )

                load_time = time.time() - start_time
                self.logger.info(
                    f"Minimal ConceptAttention model loaded in {load_time:.2f}s"
                )
                self.use_minimal = True

                # Warm up model with dummy input if optimization enabled
                if self.enable_optimization:
                    self._warmup_model()

            except Exception as minimal_e:
                self.logger.error(
                    f"Failed to initialize minimal ConceptAttention: {minimal_e}"
                )
                self.logger.error(
                    "Both full and minimal ConceptAttention failed to load"
                )
                raise RuntimeError(
                    f"ConceptAttention initialization failed: {minimal_e}"
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize ConceptAttention model: {e}")
            raise RuntimeError(f"ConceptAttention initialization failed: {e}")

    def _warmup_model(self):
        """Warm up model with dummy input for better performance"""
        try:
            self.logger.info("Warming up ConceptAttention model...")
            # Create a small dummy image for warmup
            dummy_image = Image.new("RGB", (256, 256), color="white")
            dummy_concepts = ["object", "background"]

            # Run warmup inference
            _ = self.model.generate_image(
                prompt="A simple object",
                concepts=dummy_concepts,
                width=256,
                height=256,
                num_inference_steps=1,  # Minimal steps for warmup
            )

            self.logger.info("Model warmup completed")
        except Exception as e:
            self.logger.warning(f"Model warmup failed: {e}")

    @lru_cache(maxsize=128)
    def _generate_concept_heatmaps_cached(
        self, image_hash: str, concepts_tuple: Tuple[str, ...], width: int, height: int
    ) -> Tuple[Dict[str, np.ndarray], float]:
        """Cached concept heatmap generation for performance"""
        return self._generate_concept_heatmaps_impl(concepts_tuple, width, height)

    def _generate_concept_heatmaps_impl(
        self, concepts: Tuple[str, ...], width: int, height: int
    ) -> Tuple[Dict[str, np.ndarray], float]:
        """Internal implementation of concept heatmap generation"""
        start_time = time.time()

        # Create a neutral prompt for saliency detection
        prompt = f"An image containing {', '.join(concepts)}"

        # Generate concept attention maps
        pipeline_output = self.model.generate_image(
            prompt=prompt,
            concepts=list(concepts),
            width=width,
            height=height,
            num_inference_steps=4,  # Minimal steps for saliency
            guidance_scale=3.5,  # Lower guidance for better saliency
        )

        # Extract concept heatmaps
        concept_maps = {}
        for i, concept in enumerate(concepts):
            if i < len(pipeline_output.concept_heatmaps):
                # Convert PIL image to numpy array
                heatmap_pil = pipeline_output.concept_heatmaps[i]
                heatmap_np = np.array(heatmap_pil)

                # Convert to grayscale if RGB
                if len(heatmap_np.shape) == 3:
                    heatmap_np = cv2.cvtColor(heatmap_np, cv2.COLOR_RGB2GRAY)

                # Normalize to 0-1 range
                heatmap_np = heatmap_np.astype(np.float32) / 255.0

                concept_maps[concept] = heatmap_np

        processing_time = time.time() - start_time
        return concept_maps, processing_time

    def generate_saliency_map(
        self,
        image: Union[np.ndarray, Image.Image, torch.Tensor],
        concepts: List[str],
        combine_strategy: str = "weighted_max",
        concept_weights: Optional[Dict[str, float]] = None,
        saliency_threshold: float = 0.1,
        gaussian_blur: bool = True,
        blur_kernel: int = 5,
    ) -> SaliencyOutput:
        """
        Generate saliency map for given image and concepts

        Args:
            image: Input image (numpy array, PIL Image, or torch tensor)
            concepts: List of concepts to generate saliency for
            combine_strategy: How to combine multiple concept maps
            concept_weights: Optional weights for each concept
            saliency_threshold: Minimum saliency value to keep
            gaussian_blur: Whether to apply Gaussian blur for smoothing
            blur_kernel: Kernel size for Gaussian blur

        Returns:
            SaliencyOutput containing saliency map and metadata
        """
        start_time = time.time()

        # Update statistics
        self.processing_stats["total_calls"] += 1

        # Validate inputs
        if not concepts:
            raise ValueError("At least one concept must be provided")

        # Limit number of concepts for performance
        if len(concepts) > self.max_concepts:
            self.logger.warning(
                f"Too many concepts ({len(concepts)}), limiting to {self.max_concepts}"
            )
            concepts = concepts[: self.max_concepts]

        # Process input image
        image_array, width, height = self._preprocess_image(image)

        # Generate image hash for caching
        image_hash = self._compute_image_hash(image_array)
        concepts_tuple = tuple(sorted(concepts))

        # Try to get from cache
        try:
            concept_maps, cached_time = self._generate_concept_heatmaps_cached(
                image_hash, concepts_tuple, width, height
            )
            self.processing_stats["cache_hits"] += 1
            cache_hit = True
        except Exception as e:
            self.logger.warning(f"Cache miss or error: {e}")
            concept_maps, cached_time = self._generate_concept_heatmaps_impl(
                concepts_tuple, width, height
            )
            cache_hit = False

        # Combine concept maps into single saliency map
        combined_saliency = self._combine_concept_maps(
            concept_maps, combine_strategy, concept_weights
        )

        # Post-process saliency map
        processed_saliency = self._postprocess_saliency(
            combined_saliency, saliency_threshold, gaussian_blur, blur_kernel
        )

        # Resize to match input image dimensions
        if processed_saliency.shape != (height, width):
            processed_saliency = cv2.resize(
                processed_saliency, (width, height), interpolation=cv2.INTER_LINEAR
            )

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            processed_saliency, concept_maps
        )

        # Update processing statistics
        total_time = time.time() - start_time
        self.processing_stats["total_time"] += total_time
        self.processing_stats["average_time"] = (
            self.processing_stats["total_time"] / self.processing_stats["total_calls"]
        )

        # Log performance info
        self.logger.debug(f"Saliency generation: {total_time:.3f}s, Cache: {cache_hit}")

        return SaliencyOutput(
            saliency_map=processed_saliency,
            concept_maps=concept_maps,
            processing_time=total_time,
            confidence_score=confidence_score,
            concepts_used=concepts,
        )

    def _preprocess_image(
        self, image: Union[np.ndarray, Image.Image, torch.Tensor]
    ) -> Tuple[np.ndarray, int, int]:
        """Preprocess input image to standard format"""
        if isinstance(image, torch.Tensor):
            image = image.cpu().numpy()
            if image.ndim == 4:  # Batch dimension
                image = image[0]
            if image.shape[0] == 3:  # CHW format
                image = np.transpose(image, (1, 2, 0))

        elif isinstance(image, Image.Image):
            image = np.array(image)

        # Ensure image is in correct format
        if image.ndim == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:  # RGBA
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        height, width = image.shape[:2]

        # Normalize to 0-255 range if needed
        if image.dtype == np.float32 or image.dtype == np.float64:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)

        return image, width, height

    def _compute_image_hash(self, image: np.ndarray) -> str:
        """Compute hash for image caching"""
        # Simple hash based on image content
        return str(hash(image.tobytes()))

    def _combine_concept_maps(
        self,
        concept_maps: Dict[str, np.ndarray],
        strategy: str,
        weights: Optional[Dict[str, float]] = None,
    ) -> np.ndarray:
        """Combine multiple concept maps into single saliency map"""
        if not concept_maps:
            raise ValueError("No concept maps to combine")

        # Get common shape
        shapes = [map_array.shape for map_array in concept_maps.values()]
        if not all(shape == shapes[0] for shape in shapes):
            raise ValueError("All concept maps must have the same shape")

        height, width = shapes[0]

        if strategy == "weighted_max":
            # Weighted maximum combination
            combined = np.zeros((height, width), dtype=np.float32)
            for concept, concept_map in concept_maps.items():
                weight = weights.get(concept, 1.0) if weights else 1.0
                weighted_map = concept_map * weight
                combined = np.maximum(combined, weighted_map)

        elif strategy == "weighted_average":
            # Weighted average combination
            combined = np.zeros((height, width), dtype=np.float32)
            total_weight = 0.0
            for concept, concept_map in concept_maps.items():
                weight = weights.get(concept, 1.0) if weights else 1.0
                combined += concept_map * weight
                total_weight += weight

            if total_weight > 0:
                combined /= total_weight

        elif strategy == "multiplicative":
            # Multiplicative combination (intersection)
            combined = np.ones((height, width), dtype=np.float32)
            for concept, concept_map in concept_maps.items():
                weight = weights.get(concept, 1.0) if weights else 1.0
                # Apply weight as power
                weighted_map = np.power(concept_map, 1.0 / weight)
                combined *= weighted_map

        else:
            raise ValueError(f"Unknown combine strategy: {strategy}")

        return combined

    def _postprocess_saliency(
        self,
        saliency_map: np.ndarray,
        threshold: float,
        gaussian_blur: bool,
        blur_kernel: int,
    ) -> np.ndarray:
        """Post-process saliency map for better quality"""
        # Apply threshold
        saliency_map = np.where(saliency_map > threshold, saliency_map, 0)

        # Apply Gaussian blur for smoothing
        if gaussian_blur and blur_kernel > 1:
            saliency_map = cv2.GaussianBlur(saliency_map, (blur_kernel, blur_kernel), 0)

        # Normalize to 0-1 range
        if saliency_map.max() > 0:
            saliency_map = saliency_map / saliency_map.max()

        return saliency_map

    def _calculate_confidence_score(
        self, saliency_map: np.ndarray, concept_maps: Dict[str, np.ndarray]
    ) -> float:
        """Calculate confidence score for saliency detection"""
        # Calculate various confidence metrics

        # 1. Saliency concentration (higher is better)
        if saliency_map.max() > 0:
            concentration = np.std(saliency_map) / np.mean(saliency_map + 1e-8)
        else:
            concentration = 0.0

        # 2. Concept agreement (how well concepts agree)
        if len(concept_maps) > 1:
            map_values = list(concept_maps.values())
            correlations = []
            for i in range(len(map_values)):
                for j in range(i + 1, len(map_values)):
                    corr = np.corrcoef(
                        map_values[i].flatten(), map_values[j].flatten()
                    )[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)

            agreement = np.mean(correlations) if correlations else 0.0
        else:
            agreement = 1.0

        # 3. Saliency coverage (not too sparse, not too dense)
        coverage = np.mean(saliency_map > 0.1)
        optimal_coverage = 0.3  # 30% of image should be salient
        coverage_score = 1.0 - abs(coverage - optimal_coverage) / optimal_coverage

        # Combine confidence metrics
        confidence = concentration * 0.4 + agreement * 0.3 + coverage_score * 0.3

        return np.clip(confidence, 0.0, 1.0)

    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        stats["cache_hit_rate"] = (
            stats["cache_hits"] / max(stats["total_calls"], 1) * 100
        )
        return stats

    def clear_cache(self):
        """Clear processing cache"""
        self._generate_concept_heatmaps_cached.cache_clear()
        self.concept_cache.clear()
        self.logger.info("ConceptAttention cache cleared")

    def set_device(self, device: str):
        """Change device for inference"""
        new_device = self._setup_device(device)
        if new_device != self.device:
            self.device = new_device
            self.logger.info(f"Device changed to: {self.device}")
            # Re-initialize model on new device
            self._initialize_model()

    def __del__(self):
        """Cleanup when model is destroyed"""
        if hasattr(self, "model") and self.model is not None:
            try:
                # Clear CUDA cache if using GPU
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                self.logger.info("ConceptAttention model cleaned up")
            except:
                pass


# Convenience functions for easy integration
def create_concept_attention_model(
    model_name: str = "flux-schnell", device: str = "auto", **kwargs
) -> ConceptAttentionModel:
    """
    Convenience function to create ConceptAttention model
    """
    return ConceptAttentionModel(model_name=model_name, device=device, **kwargs)


def generate_emotion_saliency(
    image: Union[np.ndarray, Image.Image, torch.Tensor],
    concepts: List[str],
    model: Optional[ConceptAttentionModel] = None,
    **kwargs,
) -> SaliencyOutput:
    """
    Convenience function to generate emotion-based saliency
    """
    if model is None:
        model = create_concept_attention_model()

    return model.generate_saliency_map(image, concepts, **kwargs)
