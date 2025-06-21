"""
Edge Fusion Module
Implementation for ArtiTech Stage 1 - Fusion of PiDiNet + DDN edge maps
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class EdgeFusion:
    """Fusion of PiDiNet and DDN edge detection results"""

    def __init__(self, beta: float = 0.6):
        self.beta = beta  # DDN confidence weight
        logger.info(f"EdgeFusion initialized with beta={beta}")

    def fuse_edges(
        self,
        p_pidi: np.ndarray,
        p_ddn_tiles: List[np.ndarray],
        tile_positions: List[Tuple[int, int]],
        tile_size: int = 16,
    ) -> np.ndarray:
        """Fuse PiDiNet and DDN edge maps using max() fusion"""
        h, w = p_pidi.shape
        fused_map = p_pidi.copy().astype(np.float32)

        logger.info(f"Fusing {len(p_ddn_tiles)} DDN tiles with PiDiNet base map")

        for ddn_tile, (x, y) in zip(p_ddn_tiles, tile_positions):
            try:
                # Ensure DDN tile is the right size
                if ddn_tile.shape != (tile_size, tile_size):
                    ddn_tile = cv2.resize(ddn_tile, (tile_size, tile_size))

                # Calculate actual tile bounds (handle edge cases)
                y_end = min(y + tile_size, h)
                x_end = min(x + tile_size, w)
                actual_h = y_end - y
                actual_w = x_end - x

                # Extract ROI from fused map
                roi = fused_map[y:y_end, x:x_end]

                # Resize DDN tile to match actual ROI size if needed
                if ddn_tile.shape != (actual_h, actual_w):
                    ddn_tile = cv2.resize(ddn_tile, (actual_w, actual_h))

                # Apply fusion using max() operation
                # max(P_pidi, β·P_ddn)
                enhanced_roi = np.maximum(roi, self.beta * ddn_tile.astype(np.float32))
                fused_map[y:y_end, x:x_end] = enhanced_roi

            except Exception as e:
                logger.warning(f"Failed to fuse tile at ({x}, {y}): {e}")
                continue

        # Convert back to uint8 range
        fused_map = np.clip(fused_map, 0, 255).astype(np.uint8)

        logger.info("Edge fusion completed successfully")
        return fused_map

    def apply_morphological_ops(self, edge_map: np.ndarray) -> np.ndarray:
        """Apply morphological operations for cleaner edges"""
        # Create elliptical kernel for smoother operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Remove noise (opening operation)
        edge_map = cv2.morphologyEx(edge_map, cv2.MORPH_OPEN, kernel)

        # Fill small gaps (closing operation)
        edge_map = cv2.morphologyEx(edge_map, cv2.MORPH_CLOSE, kernel)

        logger.debug("Applied morphological operations")
        return edge_map

    def apply_gaussian_blur(
        self, edge_map: np.ndarray, kernel_size: int = 3, sigma: float = 0.5
    ) -> np.ndarray:
        """Apply slight Gaussian blur for smoother edges"""
        blurred = cv2.GaussianBlur(edge_map, (kernel_size, kernel_size), sigma)
        logger.debug(f"Applied Gaussian blur with kernel={kernel_size}, sigma={sigma}")
        return blurred

    def enhance_contrast(
        self, edge_map: np.ndarray, alpha: float = 1.1, beta: int = 0
    ) -> np.ndarray:
        """Enhance edge contrast"""
        enhanced = cv2.convertScaleAbs(edge_map, alpha=alpha, beta=beta)
        logger.debug(f"Enhanced contrast with alpha={alpha}, beta={beta}")
        return enhanced

    def post_process_edges(
        self,
        edge_map: np.ndarray,
        apply_morphology: bool = True,
        apply_blur: bool = True,
        enhance_contrast: bool = True,
    ) -> np.ndarray:
        """Complete post-processing pipeline"""
        processed = edge_map.copy()

        if apply_morphology:
            processed = self.apply_morphological_ops(processed)

        if apply_blur:
            processed = self.apply_gaussian_blur(processed)

        if enhance_contrast:
            processed = self.enhance_contrast(processed)

        logger.info("Post-processing completed")
        return processed

    def create_edge_statistics(self, p_pidi: np.ndarray, fused_map: np.ndarray) -> dict:
        """Generate statistics about the fusion process"""
        pidi_edges = np.sum(p_pidi > 0)
        fused_edges = np.sum(fused_map > 0)
        improvement = fused_edges - pidi_edges

        stats = {
            "pidi_edge_pixels": int(pidi_edges),
            "fused_edge_pixels": int(fused_edges),
            "improvement_pixels": int(improvement),
            "improvement_percent": float(improvement / max(pidi_edges, 1) * 100),
            "fusion_beta": self.beta,
        }

        logger.info(f"Fusion stats: {stats}")
        return stats

    def visualize_fusion(
        self,
        p_pidi: np.ndarray,
        fused_map: np.ndarray,
        tile_positions: List[Tuple[int, int]],
        tile_size: int = 16,
    ) -> np.ndarray:
        """Create visualization showing fusion regions"""
        # Create 3-channel visualization
        vis = np.zeros((p_pidi.shape[0], p_pidi.shape[1], 3), dtype=np.uint8)

        # PiDiNet edges in blue
        vis[p_pidi > 0] = [255, 0, 0]

        # Fused edges in green
        vis[fused_map > 0] = [0, 255, 0]

        # Enhanced regions in red
        enhanced_pixels = fused_map > p_pidi
        vis[enhanced_pixels] = [0, 0, 255]

        # Draw tile boundaries
        for x, y in tile_positions:
            cv2.rectangle(
                vis, (x, y), (x + tile_size, y + tile_size), (255, 255, 255), 1
            )

        return vis
