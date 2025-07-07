#!/usr/bin/env python3
"""
Dual-ROI Processor for ArtiTech Stage 1
Implements semantic + density ROI intersection logic for therapeutic edge detection
"""

import numpy as np
import torch
from typing import Tuple, List, Dict, Optional, Union
from dataclasses import dataclass
from PIL import Image, ImageDraw
import cv2
from scipy import ndimage
from scipy.ndimage import binary_erosion, binary_dilation, label
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ROIRegion:
    """Represents a Region of Interest with metadata"""

    mask: np.ndarray
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    area: float
    confidence: float
    roi_type: str  # 'semantic', 'density', 'merged'
    center: Tuple[float, float]


@dataclass
class ROIProcessingConfig:
    """Configuration for ROI processing parameters"""

    # Semantic ROI parameters
    saliency_threshold: float = 0.3
    min_semantic_area: float = 0.02  # Minimum 2% of image
    max_semantic_regions: int = 5
    semantic_erosion_size: int = 3
    semantic_dilation_size: int = 5

    # Density ROI parameters
    edge_density_threshold: float = 0.15
    density_window_size: int = 64
    min_density_area: float = 0.01  # Minimum 1% of image
    max_density_regions: int = 8

    # Intersection parameters
    intersection_overlap_threshold: float = 0.1  # 10% overlap minimum
    merged_roi_padding: int = 10

    # Tile processing parameters
    tile_size: int = 256
    tile_overlap: int = 32
    max_tiles_per_roi: int = 16


class DualROIProcessor:
    """
    Dual-ROI Processor: Semantic + Density ROI intersection logic

    Extracts meaningful regions from both saliency maps (semantic ROI) and
    edge density analysis (density ROI), then intelligently merges them for
    targeted processing in therapeutic applications.
    """

    def __init__(
        self, config: Optional[ROIProcessingConfig] = None, device: str = "auto"
    ):
        """
        Initialize DualROIProcessor

        Args:
            config: ROI processing configuration
            device: Processing device ('cpu', 'cuda', 'mps', or 'auto')
        """
        self.config = config or ROIProcessingConfig()
        self.device = self._setup_device(device)
        self.processing_stats = {}

        logger.info(f"DualROIProcessor initialized on device: {self.device}")

    def _setup_device(self, device: str) -> str:
        """Setup processing device"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device

    def extract_semantic_roi(self, saliency_map: np.ndarray) -> List[ROIRegion]:
        """
        Extract semantic ROI regions from saliency map

        Args:
            saliency_map: 2D numpy array with saliency values [0-1]

        Returns:
            List of semantic ROI regions
        """
        start_time = time.time()

        if saliency_map.ndim != 2:
            raise ValueError(f"Saliency map must be 2D, got shape {saliency_map.shape}")

        height, width = saliency_map.shape
        min_area_pixels = int(height * width * self.config.min_semantic_area)

        # Apply threshold to get binary mask
        binary_mask = saliency_map > self.config.saliency_threshold

        # Morphological operations to clean up the mask
        kernel_erosion = np.ones(
            (self.config.semantic_erosion_size, self.config.semantic_erosion_size),
            np.uint8,
        )
        kernel_dilation = np.ones(
            (self.config.semantic_dilation_size, self.config.semantic_dilation_size),
            np.uint8,
        )

        # Erode to remove noise, then dilate to restore size
        cleaned_mask = binary_erosion(binary_mask, kernel_erosion)
        cleaned_mask = binary_dilation(cleaned_mask, kernel_dilation)

        # Find connected components
        labeled_mask, num_regions = label(cleaned_mask)

        semantic_rois = []

        for region_id in range(1, num_regions + 1):
            region_mask = labeled_mask == region_id
            area = np.sum(region_mask)

            # Filter by minimum area
            if area < min_area_pixels:
                continue

            # Calculate bounding box
            y_coords, x_coords = np.where(region_mask)
            if len(y_coords) == 0:
                continue

            x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
            x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))

            # Calculate confidence as mean saliency in region
            region_saliency = saliency_map[region_mask]
            confidence = float(np.mean(region_saliency))

            # Calculate center
            center_x = float(np.mean(x_coords))
            center_y = float(np.mean(y_coords))

            roi_region = ROIRegion(
                mask=region_mask,
                bbox=(x1, y1, x2, y2),
                area=float(area) / (height * width),  # Normalized area
                confidence=confidence,
                roi_type="semantic",
                center=(center_x, center_y),
            )

            semantic_rois.append(roi_region)

        # Sort by confidence and limit to max regions
        semantic_rois.sort(key=lambda x: x.confidence, reverse=True)
        semantic_rois = semantic_rois[: self.config.max_semantic_regions]

        processing_time = time.time() - start_time
        self.processing_stats["semantic_extraction_time"] = processing_time

        logger.info(
            f"Extracted {len(semantic_rois)} semantic ROI regions in {processing_time:.3f}s"
        )

        return semantic_rois

    def extract_density_roi(self, edge_map: np.ndarray) -> List[ROIRegion]:
        """
        Extract density ROI regions from edge complexity analysis

        Args:
            edge_map: 2D numpy array with edge values [0-1]

        Returns:
            List of density ROI regions
        """
        start_time = time.time()

        if edge_map.ndim != 2:
            raise ValueError(f"Edge map must be 2D, got shape {edge_map.shape}")

        height, width = edge_map.shape
        min_area_pixels = int(height * width * self.config.min_density_area)
        window_size = self.config.density_window_size

        # Calculate edge density using sliding window
        density_map = self._calculate_edge_density(edge_map, window_size)

        # Apply threshold to get binary mask
        binary_mask = density_map > self.config.edge_density_threshold

        # Find connected components
        labeled_mask, num_regions = label(binary_mask)

        density_rois = []

        for region_id in range(1, num_regions + 1):
            region_mask = labeled_mask == region_id
            area = np.sum(region_mask)

            # Filter by minimum area
            if area < min_area_pixels:
                continue

            # Calculate bounding box
            y_coords, x_coords = np.where(region_mask)
            if len(y_coords) == 0:
                continue

            x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
            x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))

            # Calculate confidence as mean density in region
            region_density = density_map[region_mask]
            confidence = float(np.mean(region_density))

            # Calculate center
            center_x = float(np.mean(x_coords))
            center_y = float(np.mean(y_coords))

            roi_region = ROIRegion(
                mask=region_mask,
                bbox=(x1, y1, x2, y2),
                area=float(area) / (height * width),  # Normalized area
                confidence=confidence,
                roi_type="density",
                center=(center_x, center_y),
            )

            density_rois.append(roi_region)

        # Sort by confidence and limit to max regions
        density_rois.sort(key=lambda x: x.confidence, reverse=True)
        density_rois = density_rois[: self.config.max_density_regions]

        processing_time = time.time() - start_time
        self.processing_stats["density_extraction_time"] = processing_time

        logger.info(
            f"Extracted {len(density_rois)} density ROI regions in {processing_time:.3f}s"
        )

        return density_rois

    def _calculate_edge_density(
        self, edge_map: np.ndarray, window_size: int
    ) -> np.ndarray:
        """Calculate edge density using sliding window approach"""

        height, width = edge_map.shape
        density_map = np.zeros_like(edge_map)

        # Use convolution for efficient sliding window computation
        kernel = np.ones((window_size, window_size)) / (window_size * window_size)

        # Handle edge padding
        pad_size = window_size // 2
        padded_edge_map = np.pad(edge_map, pad_size, mode="reflect")

        # Convolve to get average edge density
        density_map = ndimage.convolve(padded_edge_map, kernel, mode="constant")[
            pad_size : pad_size + height, pad_size : pad_size + width
        ]

        return density_map

    def merge_rois(
        self,
        semantic_rois: List[ROIRegion],
        density_rois: List[ROIRegion],
        image_shape: Tuple[int, int],
    ) -> List[ROIRegion]:
        """
        Merge semantic and density ROIs using intersection logic

        Args:
            semantic_rois: List of semantic ROI regions
            density_rois: List of density ROI regions
            image_shape: (height, width) of the image

        Returns:
            List of merged ROI regions
        """
        start_time = time.time()

        height, width = image_shape
        merged_rois = []
        used_semantic = set()
        used_density = set()

        # Find overlapping ROIs and merge them
        for i, semantic_roi in enumerate(semantic_rois):
            for j, density_roi in enumerate(density_rois):
                if i in used_semantic or j in used_density:
                    continue

                # Calculate intersection
                intersection_mask = semantic_roi.mask & density_roi.mask
                intersection_area = np.sum(intersection_mask)

                # Calculate overlap ratio
                semantic_area = np.sum(semantic_roi.mask)
                density_area = np.sum(density_roi.mask)
                min_area = min(semantic_area, density_area)

                overlap_ratio = intersection_area / min_area if min_area > 0 else 0

                if overlap_ratio >= self.config.intersection_overlap_threshold:
                    # Merge the ROIs
                    merged_mask = semantic_roi.mask | density_roi.mask

                    # Calculate merged bounding box with padding
                    y_coords, x_coords = np.where(merged_mask)
                    if len(y_coords) == 0:
                        continue

                    x1 = max(0, int(np.min(x_coords)) - self.config.merged_roi_padding)
                    y1 = max(0, int(np.min(y_coords)) - self.config.merged_roi_padding)
                    x2 = min(
                        width, int(np.max(x_coords)) + self.config.merged_roi_padding
                    )
                    y2 = min(
                        height, int(np.max(y_coords)) + self.config.merged_roi_padding
                    )

                    # Calculate merged confidence (weighted average)
                    semantic_weight = semantic_roi.confidence * semantic_area
                    density_weight = density_roi.confidence * density_area
                    total_weight = semantic_area + density_area
                    merged_confidence = (
                        semantic_weight + density_weight
                    ) / total_weight

                    # Calculate center
                    center_x = float(np.mean(x_coords))
                    center_y = float(np.mean(y_coords))

                    merged_roi = ROIRegion(
                        mask=merged_mask,
                        bbox=(x1, y1, x2, y2),
                        area=float(np.sum(merged_mask)) / (height * width),
                        confidence=merged_confidence,
                        roi_type="merged",
                        center=(center_x, center_y),
                    )

                    merged_rois.append(merged_roi)
                    used_semantic.add(i)
                    used_density.add(j)

        # Add unmerged semantic ROIs
        for i, semantic_roi in enumerate(semantic_rois):
            if i not in used_semantic:
                merged_rois.append(semantic_roi)

        # Add unmerged density ROIs
        for j, density_roi in enumerate(density_rois):
            if j not in used_density:
                merged_rois.append(density_roi)

        # Sort by confidence
        merged_rois.sort(key=lambda x: x.confidence, reverse=True)

        processing_time = time.time() - start_time
        self.processing_stats["merge_time"] = processing_time

        logger.info(
            f"Merged ROIs: {len(semantic_rois)} semantic + {len(density_rois)} density → {len(merged_rois)} final ROIs in {processing_time:.3f}s"
        )

        return merged_rois

    def generate_tiles_for_roi(
        self, roi_region: ROIRegion, image_shape: Tuple[int, int]
    ) -> List[Dict]:
        """
        Generate tiles for memory-efficient processing of ROI

        Args:
            roi_region: ROI region to tile
            image_shape: (height, width) of the image

        Returns:
            List of tile dictionaries with coordinates and metadata
        """
        height, width = image_shape
        tile_size = self.config.tile_size
        overlap = self.config.tile_overlap

        x1, y1, x2, y2 = roi_region.bbox
        roi_width = x2 - x1
        roi_height = y2 - y1

        tiles = []

        # Calculate step size (tile_size - overlap)
        step_size = tile_size - overlap

        for y in range(y1, y2, step_size):
            for x in range(x1, x2, step_size):
                # Calculate tile boundaries
                tile_x1 = max(0, x)
                tile_y1 = max(0, y)
                tile_x2 = min(width, x + tile_size)
                tile_y2 = min(height, y + tile_size)

                # Skip if tile is too small
                if (tile_x2 - tile_x1) < tile_size // 2 or (
                    tile_y2 - tile_y1
                ) < tile_size // 2:
                    continue

                # Check if tile intersects with ROI mask
                tile_mask = roi_region.mask[tile_y1:tile_y2, tile_x1:tile_x2]
                if np.sum(tile_mask) == 0:
                    continue  # Skip tiles with no ROI content

                tile_dict = {
                    "bbox": (tile_x1, tile_y1, tile_x2, tile_y2),
                    "roi_coverage": float(np.sum(tile_mask)) / tile_mask.size,
                    "roi_region": roi_region,
                    "global_coords": (tile_x1, tile_y1, tile_x2, tile_y2),
                }

                tiles.append(tile_dict)

                # Limit number of tiles per ROI
                if len(tiles) >= self.config.max_tiles_per_roi:
                    break

        # Sort tiles by ROI coverage (most relevant first)
        tiles.sort(key=lambda x: x["roi_coverage"], reverse=True)

        logger.info(f"Generated {len(tiles)} tiles for {roi_region.roi_type} ROI")

        return tiles

    def process_dual_roi(self, saliency_map: np.ndarray, edge_map: np.ndarray) -> Dict:
        """
        Complete dual-ROI processing pipeline

        Args:
            saliency_map: 2D numpy array with saliency values [0-1]
            edge_map: 2D numpy array with edge values [0-1]

        Returns:
            Dictionary with processed ROI data
        """
        start_time = time.time()

        if saliency_map.shape != edge_map.shape:
            raise ValueError(
                f"Saliency and edge maps must have same shape: {saliency_map.shape} vs {edge_map.shape}"
            )

        image_shape = saliency_map.shape

        # Extract semantic ROIs
        semantic_rois = self.extract_semantic_roi(saliency_map)

        # Extract density ROIs
        density_rois = self.extract_density_roi(edge_map)

        # Merge ROIs
        merged_rois = self.merge_rois(semantic_rois, density_rois, image_shape)

        # Generate tiles for top ROIs
        roi_tiles = {}
        for i, roi in enumerate(merged_rois[:5]):  # Process top 5 ROIs
            tiles = self.generate_tiles_for_roi(roi, image_shape)
            roi_tiles[f"roi_{i}"] = tiles

        total_time = time.time() - start_time

        result = {
            "semantic_rois": semantic_rois,
            "density_rois": density_rois,
            "merged_rois": merged_rois,
            "roi_tiles": roi_tiles,
            "processing_stats": {
                **self.processing_stats,
                "total_processing_time": total_time,
                "num_semantic_rois": len(semantic_rois),
                "num_density_rois": len(density_rois),
                "num_merged_rois": len(merged_rois),
                "total_tiles": sum(len(tiles) for tiles in roi_tiles.values()),
            },
        }

        logger.info(
            f"Dual-ROI processing complete: {len(merged_rois)} ROIs, {result['processing_stats']['total_tiles']} tiles in {total_time:.3f}s"
        )

        return result

    def visualize_rois(
        self, image: np.ndarray, roi_result: Dict, save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Create visualization of ROI processing results

        Args:
            image: Original image as numpy array
            roi_result: Result from process_dual_roi
            save_path: Optional path to save visualization

        Returns:
            Visualization image as numpy array
        """
        if image.ndim == 3:
            vis_image = image.copy()
        else:
            vis_image = np.stack([image] * 3, axis=-1)

        height, width = vis_image.shape[:2]

        # Convert to PIL for drawing
        pil_image = Image.fromarray((vis_image * 255).astype(np.uint8))
        draw = ImageDraw.Draw(pil_image)

        # Color mapping for different ROI types
        colors = {
            "semantic": (255, 0, 0, 128),  # Red
            "density": (0, 255, 0, 128),  # Green
            "merged": (0, 0, 255, 128),  # Blue
        }

        # Draw ROI bounding boxes
        for roi in roi_result["merged_rois"]:
            color = colors.get(roi.roi_type, (255, 255, 0, 128))
            x1, y1, x2, y2 = roi.bbox

            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color[:3], width=2)

            # Draw center point
            cx, cy = roi.center
            draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color[:3])

            # Draw confidence text
            text = f"{roi.roi_type}: {roi.confidence:.2f}"
            draw.text((x1, y1 - 15), text, fill=color[:3])

        # Draw tiles for first ROI
        if roi_result["roi_tiles"]:
            first_roi_tiles = list(roi_result["roi_tiles"].values())[0]
            for tile in first_roi_tiles[:5]:  # Show first 5 tiles
                x1, y1, x2, y2 = tile["bbox"]
                draw.rectangle([x1, y1, x2, y2], outline=(255, 255, 0), width=1)

        result_image = np.array(pil_image)

        if save_path:
            pil_image.save(save_path)
            logger.info(f"ROI visualization saved to {save_path}")

        return result_image


# Example usage and testing functions
def test_dual_roi_processor():
    """Test function for DualROIProcessor"""

    print("🧪 Testing DualROIProcessor...")

    # Create synthetic test data
    height, width = 512, 512

    # Create synthetic saliency map with multiple regions
    saliency_map = np.zeros((height, width))
    # Central region
    saliency_map[200:300, 200:300] = 0.8
    # Upper left region
    saliency_map[50:150, 50:150] = 0.6
    # Add some noise
    saliency_map += np.random.normal(0, 0.1, (height, width))
    saliency_map = np.clip(saliency_map, 0, 1)

    # Create synthetic edge map
    edge_map = np.zeros((height, width))
    # Add edge patterns
    edge_map[150:350, 150:350] = 0.7  # Overlapping with central saliency
    edge_map[300:450, 300:450] = 0.5  # Additional edge region
    edge_map += np.random.normal(0, 0.05, (height, width))
    edge_map = np.clip(edge_map, 0, 1)

    # Initialize processor
    processor = DualROIProcessor()

    # Process dual ROI
    result = processor.process_dual_roi(saliency_map, edge_map)

    print(f"✅ Dual-ROI Processing Results:")
    print(f"   Semantic ROIs: {result['processing_stats']['num_semantic_rois']}")
    print(f"   Density ROIs: {result['processing_stats']['num_density_rois']}")
    print(f"   Merged ROIs: {result['processing_stats']['num_merged_rois']}")
    print(f"   Total Tiles: {result['processing_stats']['total_tiles']}")
    print(
        f"   Processing Time: {result['processing_stats']['total_processing_time']:.3f}s"
    )

    # Create visualization
    test_image = np.random.rand(height, width, 3)
    vis_image = processor.visualize_rois(test_image, result)

    print(f"   Visualization created: {vis_image.shape}")

    return result


if __name__ == "__main__":
    test_dual_roi_processor()
