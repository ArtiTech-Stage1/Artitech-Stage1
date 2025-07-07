"""
Therapeutic Masking System for Phase 2 Saliency Integration
Implements emotion-based masking strategies for partial outline generation
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import cv2
from scipy.ndimage import distance_transform_edt, gaussian_filter
from skimage.measure import label, regionprops
from skimage.morphology import remove_small_objects, binary_erosion, binary_dilation

from ..config.emotion_configs import EmotionConfig, MaskingStrategy


class MaskQuality(Enum):
    """Quality levels for mask validation"""

    EXCELLENT = "excellent"  # >80% structural coherence, good completion potential
    GOOD = "good"  # 60-80% coherence, adequate completion
    FAIR = "fair"  # 40-60% coherence, challenging but doable
    POOR = "poor"  # <40% coherence, likely frustrating


@dataclass
class MaskMetrics:
    """Metrics for evaluating mask quality"""

    structural_coherence: float  # 0-1, how much structure is preserved
    completion_feasibility: float  # 0-1, how completable the gaps are
    therapeutic_gap_ratio: float  # 0-1, ratio of meaningful gaps
    fragmentation_score: float  # 0-1, how fragmented the result is (lower is better)
    overall_quality: MaskQuality


class TherapeuticMasker:
    """
    Implements therapeutic masking strategies for emotion-based partial outline generation
    """

    def __init__(self, device: str = "auto"):
        self.device = device
        self.mask_cache = {}  # Cache for performance optimization

        # Default parameters for each masking strategy
        self.default_params = {
            MaskingStrategy.SOFT_MASK: {
                "min_alpha": 0.15,  # Minimum visibility (never completely invisible)
                "alpha_curve": "linear",  # linear, quadratic, cubic
                "saliency_power": 0.8,  # How much saliency affects alpha
            },
            MaskingStrategy.GRADIENT: {
                "fade_distance": 25,  # Pixels for gradient fade
                "fade_curve": "exponential",  # linear, exponential, gaussian
                "boundary_blur": 3,  # Gaussian blur for smooth boundaries
                "min_alpha": 0.1,
            },
            MaskingStrategy.INVERT: {
                "saliency_threshold": 0.4,  # Threshold for binary masking
                "min_region_size": 150,  # Minimum region size to keep
                "erosion_iterations": 1,  # Morphological erosion to clean edges
                "dilation_iterations": 2,  # Morphological dilation to restore size
            },
            MaskingStrategy.SELECTIVE: {
                "concept_threshold_base": 0.3,  # Base threshold for concept masking
                "weight_sensitivity": 0.5,  # How much concept weights affect masking
                "min_concept_area": 100,  # Minimum area for concept-based masking
                "overlap_handling": "union",  # union, intersection, weighted
            },
        }

    def apply_therapeutic_mask(
        self,
        edge_map: np.ndarray,
        saliency_map: np.ndarray,
        emotion_config: EmotionConfig,
        custom_params: Optional[Dict] = None,
    ) -> Tuple[np.ndarray, MaskMetrics]:
        """
        Apply therapeutic masking based on emotion configuration

        Args:
            edge_map: Input edge map (H, W) with values 0-255
            saliency_map: Saliency map (H, W) with values 0-1
            emotion_config: Emotion configuration with masking strategy
            custom_params: Custom parameters to override defaults

        Returns:
            Tuple of (masked_edge_map, quality_metrics)
        """
        # Get parameters for this masking strategy
        params = self.default_params[emotion_config.masking_strategy].copy()
        if custom_params:
            params.update(custom_params)

        # Apply intensity multiplier from emotion config
        if hasattr(emotion_config, "intensity_multiplier"):
            params = self._apply_intensity_scaling(
                params, emotion_config.intensity_multiplier
            )

        # Apply appropriate masking strategy
        if emotion_config.masking_strategy == MaskingStrategy.SOFT_MASK:
            masked_edges = self._apply_soft_mask(edge_map, saliency_map, params)
        elif emotion_config.masking_strategy == MaskingStrategy.GRADIENT:
            masked_edges = self._apply_gradient_mask(edge_map, saliency_map, params)
        elif emotion_config.masking_strategy == MaskingStrategy.INVERT:
            masked_edges = self._apply_invert_mask(edge_map, saliency_map, params)
        elif emotion_config.masking_strategy == MaskingStrategy.SELECTIVE:
            masked_edges = self._apply_selective_mask(
                edge_map, saliency_map, emotion_config, params
            )
        else:
            raise ValueError(
                f"Unsupported masking strategy: {emotion_config.masking_strategy}"
            )

        # Validate mask quality
        metrics = self._evaluate_mask_quality(edge_map, masked_edges, saliency_map)

        # Apply post-processing if quality is poor
        if metrics.overall_quality == MaskQuality.POOR:
            masked_edges = self._improve_mask_quality(
                edge_map, masked_edges, saliency_map, params
            )
            metrics = self._evaluate_mask_quality(edge_map, masked_edges, saliency_map)

        return masked_edges, metrics

    def _apply_soft_mask(
        self, edge_map: np.ndarray, saliency_map: np.ndarray, params: Dict
    ) -> np.ndarray:
        """Apply soft masking with partial transparency"""
        min_alpha = params["min_alpha"]
        saliency_power = params["saliency_power"]
        alpha_curve = params["alpha_curve"]

        # Normalize inputs
        edge_map_norm = edge_map.astype(np.float32) / 255.0
        saliency_norm = np.clip(saliency_map, 0, 1)

        # Create alpha mask (inverted saliency - high saliency = low alpha)
        alpha_raw = 1.0 - (saliency_norm * saliency_power)

        # Apply curve transformation
        if alpha_curve == "quadratic":
            alpha_mask = alpha_raw**2
        elif alpha_curve == "cubic":
            alpha_mask = alpha_raw**3
        else:  # linear
            alpha_mask = alpha_raw

        # Ensure minimum visibility
        alpha_mask = np.clip(alpha_mask, min_alpha, 1.0)

        # Apply masking
        masked_edges = edge_map_norm * alpha_mask

        return (masked_edges * 255).astype(np.uint8)

    def _apply_gradient_mask(
        self, edge_map: np.ndarray, saliency_map: np.ndarray, params: Dict
    ) -> np.ndarray:
        """Apply gradient masking with smooth transitions"""
        fade_distance = params["fade_distance"]
        fade_curve = params["fade_curve"]
        boundary_blur = params["boundary_blur"]
        min_alpha = params["min_alpha"]

        # Create binary mask from saliency (areas to fade out)
        saliency_threshold = np.mean(saliency_map) + 0.5 * np.std(saliency_map)
        binary_mask = saliency_map > saliency_threshold

        # Blur boundaries for smoother transitions
        if boundary_blur > 0:
            binary_mask = (
                gaussian_filter(binary_mask.astype(float), boundary_blur) > 0.5
            )

        # Compute distance transform from mask boundaries
        distances = distance_transform_edt(~binary_mask)

        # Normalize distances and create gradient
        max_distance = min(fade_distance, np.max(distances))
        if max_distance > 0:
            gradient_alpha = distances / max_distance
        else:
            gradient_alpha = np.ones_like(distances)

        # Apply curve transformation
        if fade_curve == "exponential":
            gradient_alpha = 1.0 - np.exp(-2 * gradient_alpha)
        elif fade_curve == "gaussian":
            gradient_alpha = 1.0 - np.exp(-0.5 * (gradient_alpha * 2) ** 2)
        # else: linear (no transformation needed)

        # Ensure minimum alpha and clip
        gradient_alpha = np.clip(gradient_alpha, min_alpha, 1.0)

        # Apply gradient masking
        edge_map_norm = edge_map.astype(np.float32) / 255.0
        masked_edges = edge_map_norm * gradient_alpha

        return (masked_edges * 255).astype(np.uint8)

    def _apply_invert_mask(
        self, edge_map: np.ndarray, saliency_map: np.ndarray, params: Dict
    ) -> np.ndarray:
        """Apply invert masking with structural preservation"""
        threshold = params["saliency_threshold"]
        min_region_size = params["min_region_size"]
        erosion_iter = params["erosion_iterations"]
        dilation_iter = params["dilation_iterations"]

        # Create binary mask (keep areas with low saliency)
        keep_mask = saliency_map < threshold

        # Apply morphological operations to clean up mask
        if erosion_iter > 0:
            keep_mask = binary_erosion(keep_mask, iterations=erosion_iter)
        if dilation_iter > 0:
            keep_mask = binary_dilation(keep_mask, iterations=dilation_iter)

        # Remove small disconnected regions
        labeled_mask = label(keep_mask)
        cleaned_mask = remove_small_objects(labeled_mask, min_size=min_region_size)
        final_mask = cleaned_mask > 0

        # Apply masking
        masked_edges = edge_map.copy()
        masked_edges[~final_mask] = 0

        return masked_edges

    def _apply_selective_mask(
        self,
        edge_map: np.ndarray,
        saliency_map: np.ndarray,
        emotion_config: EmotionConfig,
        params: Dict,
    ) -> np.ndarray:
        """Apply selective masking based on concept weights"""
        # For now, use weighted saliency approach
        # In full implementation, this would require concept-specific saliency maps

        concept_weights = emotion_config.concept_weights or {}
        if not concept_weights:
            # Fallback to soft masking if no concept weights
            return self._apply_soft_mask(
                edge_map, saliency_map, self.default_params[MaskingStrategy.SOFT_MASK]
            )

        # Calculate weighted saliency threshold
        avg_weight = np.mean(list(concept_weights.values()))
        weighted_threshold = params["concept_threshold_base"] / max(avg_weight, 0.5)

        # Apply threshold-based masking
        keep_mask = saliency_map < weighted_threshold

        # Clean up mask
        labeled_mask = label(keep_mask)
        cleaned_mask = remove_small_objects(
            labeled_mask, min_size=params["min_concept_area"]
        )
        final_mask = cleaned_mask > 0

        # Apply masking
        masked_edges = edge_map.copy()
        masked_edges[~final_mask] = 0

        return masked_edges

    def _apply_intensity_scaling(
        self, params: Dict, intensity_multiplier: float
    ) -> Dict:
        """Scale parameters based on emotion intensity"""
        scaled_params = params.copy()

        # Parameters that should scale with intensity
        intensity_sensitive = ["fade_distance", "min_region_size", "saliency_threshold"]

        for param_name in intensity_sensitive:
            if param_name in scaled_params:
                if param_name == "saliency_threshold":
                    # Lower threshold = more aggressive masking
                    scaled_params[param_name] = (
                        params[param_name] / intensity_multiplier
                    )
                else:
                    # Scale directly with intensity
                    scaled_params[param_name] = int(
                        params[param_name] * intensity_multiplier
                    )

        return scaled_params

    def _evaluate_mask_quality(
        self,
        original_edges: np.ndarray,
        masked_edges: np.ndarray,
        saliency_map: np.ndarray,
    ) -> MaskMetrics:
        """Evaluate the quality of the therapeutic mask"""

        # 1. Structural Coherence: How much structure is preserved
        original_pixels = np.sum(original_edges > 0)
        preserved_pixels = np.sum(masked_edges > 0)
        structural_coherence = preserved_pixels / max(original_pixels, 1)

        # 2. Fragmentation Score: Count connected components
        labeled_original = label(original_edges > 0)
        labeled_masked = label(masked_edges > 0)

        original_components = np.max(labeled_original)
        masked_components = np.max(labeled_masked)

        # Lower fragmentation is better
        fragmentation_score = (
            min(masked_components / max(original_components, 1), 2.0) / 2.0
        )

        # 3. Therapeutic Gap Ratio: Meaningful gaps in salient areas
        high_saliency_mask = saliency_map > 0.6
        gaps_in_salient = np.sum(
            (original_edges > 0) & high_saliency_mask & (masked_edges == 0)
        )
        total_salient_edges = np.sum((original_edges > 0) & high_saliency_mask)

        therapeutic_gap_ratio = gaps_in_salient / max(total_salient_edges, 1)

        # 4. Completion Feasibility: Are remaining structures completable?
        # Check for isolated small regions (harder to complete)
        masked_regions = regionprops(labeled_masked)
        small_regions = sum(1 for region in masked_regions if region.area < 50)
        total_regions = len(masked_regions)

        completion_feasibility = 1.0 - (small_regions / max(total_regions, 1))

        # 5. Overall Quality Assessment
        quality_score = (
            structural_coherence * 0.3
            + (1.0 - fragmentation_score) * 0.2
            + therapeutic_gap_ratio * 0.3
            + completion_feasibility * 0.2
        )

        if quality_score >= 0.8:
            overall_quality = MaskQuality.EXCELLENT
        elif quality_score >= 0.6:
            overall_quality = MaskQuality.GOOD
        elif quality_score >= 0.4:
            overall_quality = MaskQuality.FAIR
        else:
            overall_quality = MaskQuality.POOR

        return MaskMetrics(
            structural_coherence=structural_coherence,
            completion_feasibility=completion_feasibility,
            therapeutic_gap_ratio=therapeutic_gap_ratio,
            fragmentation_score=fragmentation_score,
            overall_quality=overall_quality,
        )

    def _improve_mask_quality(
        self,
        original_edges: np.ndarray,
        poor_mask: np.ndarray,
        saliency_map: np.ndarray,
        params: Dict,
    ) -> np.ndarray:
        """Attempt to improve poor quality masks"""

        # Strategy 1: If too fragmented, use more conservative masking
        labeled_mask = label(poor_mask > 0)
        num_components = np.max(labeled_mask)

        if num_components > 10:  # Too fragmented
            # Fall back to soft masking with higher minimum alpha
            conservative_params = self.default_params[MaskingStrategy.SOFT_MASK].copy()
            conservative_params["min_alpha"] = 0.4  # More conservative
            return self._apply_soft_mask(
                original_edges, saliency_map, conservative_params
            )

        # Strategy 2: If too little structure preserved, reduce masking intensity
        preserved_ratio = np.sum(poor_mask > 0) / np.sum(original_edges > 0)
        if preserved_ratio < 0.3:  # Too aggressive
            # Use gradient masking with larger fade distance
            conservative_params = self.default_params[MaskingStrategy.GRADIENT].copy()
            conservative_params["fade_distance"] = 40  # Larger fade
            conservative_params["min_alpha"] = 0.3  # Higher minimum
            return self._apply_gradient_mask(
                original_edges, saliency_map, conservative_params
            )

        # If no specific issues detected, return original
        return poor_mask

    def get_optimal_parameters(
        self,
        edge_map: np.ndarray,
        saliency_map: np.ndarray,
        emotion_config: EmotionConfig,
    ) -> Dict:
        """
        Automatically determine optimal parameters for given inputs
        """
        # Analyze input characteristics
        edge_density = np.sum(edge_map > 0) / edge_map.size
        saliency_concentration = np.std(saliency_map)

        # Get base parameters
        base_params = self.default_params[emotion_config.masking_strategy].copy()

        # Adjust based on input characteristics
        if emotion_config.masking_strategy == MaskingStrategy.GRADIENT:
            # Adjust fade distance based on edge density
            if edge_density > 0.1:  # Dense edges
                base_params["fade_distance"] = int(base_params["fade_distance"] * 1.5)
            elif edge_density < 0.05:  # Sparse edges
                base_params["fade_distance"] = int(base_params["fade_distance"] * 0.7)

        elif emotion_config.masking_strategy == MaskingStrategy.INVERT:
            # Adjust threshold based on saliency concentration
            if saliency_concentration > 0.3:  # High variation
                base_params["saliency_threshold"] *= 1.2
            elif saliency_concentration < 0.15:  # Low variation
                base_params["saliency_threshold"] *= 0.8

        return base_params


# Convenience functions for easy integration
def create_therapeutic_outline(
    edge_map: np.ndarray,
    saliency_map: np.ndarray,
    emotion_config: EmotionConfig,
    custom_params: Optional[Dict] = None,
) -> Tuple[np.ndarray, MaskMetrics]:
    """
    Convenience function to create therapeutic outline with quality metrics
    """
    masker = TherapeuticMasker()
    return masker.apply_therapeutic_mask(
        edge_map, saliency_map, emotion_config, custom_params
    )


def validate_therapeutic_effectiveness(
    original_edges: np.ndarray, masked_edges: np.ndarray, saliency_map: np.ndarray
) -> MaskMetrics:
    """
    Convenience function to validate therapeutic effectiveness
    """
    masker = TherapeuticMasker()
    return masker._evaluate_mask_quality(original_edges, masked_edges, saliency_map)
