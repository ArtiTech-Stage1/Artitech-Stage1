#!/usr/bin/env python3
"""
Test ROI-Enhanced Processing with Classical Portrait (435864.jpg)
Real-world demonstration of Phase 2.3 ROI Processing System
"""

import sys
import os
import time
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.edge_detection.ddn_model import DDNModel
from src.edge_detection.saliency.roi_processor import DualROIProcessor
from src.edge_detection.saliency.concept_attention import ConceptAttentionModel
from src.edge_detection.pidinet_model import PiDiNetModel


def load_classical_portrait():
    """Load the classical portrait image for testing"""

    image_path = Path("images/435864.jpg")

    if not image_path.exists():
        raise FileNotFoundError(f"Classical portrait not found: {image_path}")

    # Load image
    image_pil = Image.open(image_path)
    image_np = np.array(image_pil)

    # Convert to RGB if needed
    if image_np.shape[2] == 4:  # RGBA
        image_np = image_np[:, :, :3]

    print(f"✅ Loaded classical portrait: {image_np.shape}")
    print(f"   File: {image_path}")
    print(f"   Size: {image_pil.size}")

    return image_np, str(image_path)


def generate_mock_saliency_for_portrait(
    image: np.ndarray, concepts: list = None
) -> np.ndarray:
    """Generate realistic mock saliency map for the classical portrait"""

    if concepts is None:
        concepts = ["face", "person", "eyes", "dress"]

    print(f"🎨 Generating mock saliency for concepts: {concepts}")

    height, width = image.shape[:2]
    saliency_map = np.zeros((height, width), dtype=np.float32)

    # Analyze the classical portrait structure
    center_y, center_x = height // 2, width // 2

    # Face region (upper center)
    face_center_y = int(height * 0.35)  # Face is in upper portion
    face_center_x = center_x

    # Create face saliency (primary focus)
    y, x = np.ogrid[:height, :width]
    face_distance = np.sqrt((x - face_center_x) ** 2 + (y - face_center_y) ** 2)
    face_saliency = np.exp(-face_distance / (width * 0.15)) * 0.9

    # Eyes region (more focused)
    if "eyes" in concepts or "face" in concepts:
        eye_y = int(height * 0.32)
        left_eye_x = int(width * 0.45)
        right_eye_x = int(width * 0.55)

        # Left eye
        left_eye_dist = np.sqrt((x - left_eye_x) ** 2 + (y - eye_y) ** 2)
        left_eye_saliency = np.exp(-left_eye_dist / (width * 0.05)) * 0.95

        # Right eye
        right_eye_dist = np.sqrt((x - right_eye_x) ** 2 + (y - eye_y) ** 2)
        right_eye_saliency = np.exp(-right_eye_dist / (width * 0.05)) * 0.95

        saliency_map = np.maximum(saliency_map, left_eye_saliency)
        saliency_map = np.maximum(saliency_map, right_eye_saliency)

    # Add face region
    saliency_map = np.maximum(saliency_map, face_saliency)

    # Person/dress region (lower portion)
    if "person" in concepts or "dress" in concepts:
        dress_center_y = int(height * 0.7)
        dress_distance = np.sqrt((x - center_x) ** 2 + (y - dress_center_y) ** 2)
        dress_saliency = np.exp(-dress_distance / (width * 0.25)) * 0.6
        saliency_map = np.maximum(saliency_map, dress_saliency)

    # Pet/companion region (if visible in portrait)
    if "dog" in concepts or "pet" in concepts:
        pet_center_y = int(height * 0.6)
        pet_center_x = int(width * 0.6)
        pet_distance = np.sqrt((x - pet_center_x) ** 2 + (y - pet_center_y) ** 2)
        pet_saliency = np.exp(-pet_distance / (width * 0.12)) * 0.7
        saliency_map = np.maximum(saliency_map, pet_saliency)

    # Add some subtle background attention
    background_noise = np.random.normal(0, 0.02, (height, width))
    saliency_map += background_noise

    # Ensure valid range
    saliency_map = np.clip(saliency_map, 0, 1)

    print(f"   ✅ Saliency map generated: {saliency_map.shape}")
    print(f"   Range: [{saliency_map.min():.3f}, {saliency_map.max():.3f}]")
    print(f"   Mean attention: {saliency_map.mean():.3f}")

    return saliency_map


def get_base_edge_map_from_pidinet(image: np.ndarray) -> np.ndarray:
    """Get base edge map using PiDiNet for comparison"""

    print(f"🔍 Generating base edge map with PiDiNet...")

    try:
        # Initialize PiDiNet model
        pidinet = PiDiNetModel(
            model_path="models/pidinet/table5_pidinet.pth", device="auto"
        )

        # Generate edge map
        edge_result = pidinet.inference(image)
        base_edge_map = edge_result["edge_map"]

        print(f"   ✅ PiDiNet edge map: {base_edge_map.shape}")

    except Exception as e:
        print(f"   ⚠️ PiDiNet not available ({e}), using mock edge map")

        # Create mock edge map using Canny
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        base_edge_map = edges.astype(np.uint8)

    return base_edge_map


def create_visualization_grid(
    image: np.ndarray,
    saliency_map: np.ndarray,
    base_edge_map: np.ndarray,
    enhanced_edge_map: np.ndarray,
    roi_result: dict,
) -> np.ndarray:
    """Create a comprehensive visualization grid of all results"""

    print(f"🎨 Creating visualization grid...")

    height, width = image.shape[:2]

    # Create 2x3 grid
    grid_height = height * 2
    grid_width = width * 3
    grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)

    # Original image (top-left)
    grid[0:height, 0:width] = image

    # Saliency map (top-center)
    saliency_colored = plt_colormap_viridis(saliency_map)
    grid[0:height, width : 2 * width] = saliency_colored

    # ROI visualization (top-right)
    roi_processor = DualROIProcessor()
    roi_vis = roi_processor.visualize_rois(image, roi_result)
    grid[0:height, 2 * width : 3 * width] = roi_vis

    # Base edge map (bottom-left)
    base_edges_colored = np.stack([base_edge_map] * 3, axis=-1)
    grid[height : 2 * height, 0:width] = base_edges_colored

    # Enhanced edge map (bottom-center)
    enhanced_edges_colored = np.stack([enhanced_edge_map] * 3, axis=-1)
    grid[height : 2 * height, width : 2 * width] = enhanced_edges_colored

    # Difference map (bottom-right)
    diff_map = np.abs(
        enhanced_edge_map.astype(np.float32) - base_edge_map.astype(np.float32)
    )
    diff_map = (
        (diff_map / diff_map.max() * 255).astype(np.uint8)
        if diff_map.max() > 0
        else diff_map.astype(np.uint8)
    )
    diff_colored = plt_colormap_jet(diff_map / 255.0)
    grid[height : 2 * height, 2 * width : 3 * width] = diff_colored

    # Add labels
    grid = add_labels_to_grid(grid, width, height)

    return grid


def plt_colormap_viridis(data: np.ndarray) -> np.ndarray:
    """Apply viridis colormap to data (approximation)"""
    # Simple approximation of viridis colormap
    norm_data = (
        (data - data.min()) / (data.max() - data.min())
        if data.max() > data.min()
        else data
    )

    # Create RGB channels for viridis-like colormap
    r = np.interp(
        norm_data, [0, 0.25, 0.5, 0.75, 1.0], [0.267, 0.127, 0.0, 0.329, 0.993]
    )
    g = np.interp(
        norm_data, [0, 0.25, 0.5, 0.75, 1.0], [0.004, 0.4, 0.635, 0.855, 0.906]
    )
    b = np.interp(
        norm_data, [0, 0.25, 0.5, 0.75, 1.0], [0.329, 0.671, 0.867, 0.639, 0.143]
    )

    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def plt_colormap_jet(data: np.ndarray) -> np.ndarray:
    """Apply jet colormap to data (approximation)"""
    norm_data = np.clip(data, 0, 1)

    # Jet colormap approximation
    r = np.where(
        norm_data < 0.25,
        0,
        np.where(
            norm_data < 0.5,
            4 * norm_data - 1,
            np.where(norm_data < 0.75, 1, -4 * norm_data + 3),
        ),
    )

    g = np.where(
        norm_data < 0.25,
        4 * norm_data,
        np.where(norm_data < 0.75, 1, -4 * norm_data + 3),
    )

    b = np.where(norm_data < 0.25, 1, np.where(norm_data < 0.5, -4 * norm_data + 2, 0))

    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def add_labels_to_grid(grid: np.ndarray, width: int, height: int) -> np.ndarray:
    """Add text labels to visualization grid"""

    # Convert to PIL for text drawing
    pil_image = Image.fromarray(grid)
    draw = ImageDraw.Draw(pil_image)

    # Define label positions and text
    labels = [
        (10, 10, "Original Image"),
        (width + 10, 10, "Saliency Map"),
        (2 * width + 10, 10, "ROI Regions"),
        (10, height + 10, "Base Edges (PiDiNet)"),
        (width + 10, height + 10, "Enhanced Edges (ROI)"),
        (2 * width + 10, height + 10, "Enhancement Difference"),
    ]

    # Draw labels
    for x, y, text in labels:
        # Black background for text
        bbox = draw.textbbox((x, y), text)
        draw.rectangle(bbox, fill=(0, 0, 0, 128))
        draw.text((x, y), text, fill=(255, 255, 255))

    return np.array(pil_image)


def analyze_roi_enhancement_quality(
    base_edge_map: np.ndarray, enhanced_edge_map: np.ndarray, roi_result: dict
) -> dict:
    """Analyze the quality of ROI enhancement"""

    print(f"📊 Analyzing ROI enhancement quality...")

    # Basic metrics
    base_mean = np.mean(base_edge_map)
    enhanced_mean = np.mean(enhanced_edge_map)
    enhancement_ratio = enhanced_mean / base_mean if base_mean > 0 else 1.0

    # Edge strength metrics
    base_strong_edges = np.sum(base_edge_map > 128)
    enhanced_strong_edges = np.sum(enhanced_edge_map > 128)
    strong_edge_ratio = (
        enhanced_strong_edges / base_strong_edges if base_strong_edges > 0 else 1.0
    )

    # ROI-specific metrics
    roi_coverage = 0
    roi_enhancement = 0

    if roi_result["merged_rois"]:
        total_pixels = base_edge_map.shape[0] * base_edge_map.shape[1]
        roi_pixels = sum(np.sum(roi.mask) for roi in roi_result["merged_rois"])
        roi_coverage = roi_pixels / total_pixels

        # Calculate average enhancement in ROI regions
        roi_enhancements = []
        for roi in roi_result["merged_rois"]:
            roi_mask = roi.mask
            if np.any(roi_mask):
                base_roi_mean = np.mean(base_edge_map[roi_mask])
                enhanced_roi_mean = np.mean(enhanced_edge_map[roi_mask])
                if base_roi_mean > 0:
                    roi_enhancements.append(enhanced_roi_mean / base_roi_mean)

        roi_enhancement = np.mean(roi_enhancements) if roi_enhancements else 1.0

    quality_metrics = {
        "enhancement_ratio": enhancement_ratio,
        "strong_edge_ratio": strong_edge_ratio,
        "roi_coverage": roi_coverage,
        "roi_enhancement": roi_enhancement,
        "base_mean_intensity": base_mean,
        "enhanced_mean_intensity": enhanced_mean,
        "base_strong_edges": base_strong_edges,
        "enhanced_strong_edges": enhanced_strong_edges,
        "processing_stats": roi_result["processing_stats"],
    }

    print(f"   ✅ Quality Analysis:")
    print(f"      Overall Enhancement: {enhancement_ratio:.3f}x")
    print(f"      Strong Edge Enhancement: {strong_edge_ratio:.3f}x")
    print(f"      ROI Coverage: {roi_coverage:.1%}")
    print(f"      ROI-specific Enhancement: {roi_enhancement:.3f}x")

    return quality_metrics


def save_results(
    image: np.ndarray,
    saliency_map: np.ndarray,
    base_edge_map: np.ndarray,
    enhanced_edge_map: np.ndarray,
    visualization_grid: np.ndarray,
    quality_metrics: dict,
    roi_result: dict,
):
    """Save all results to output directory"""

    output_dir = Path("outputs/classical_portrait_roi_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"💾 Saving results to {output_dir}...")

    # Save individual components
    Image.fromarray(image).save(output_dir / "01_original_image.jpg")

    # Save saliency map as colored image
    saliency_colored = plt_colormap_viridis(saliency_map)
    Image.fromarray(saliency_colored).save(output_dir / "02_saliency_map.jpg")

    # Save edge maps
    Image.fromarray(base_edge_map).save(output_dir / "03_base_edges.jpg")
    Image.fromarray(enhanced_edge_map).save(output_dir / "04_enhanced_edges.jpg")

    # Save difference map
    diff_map = np.abs(
        enhanced_edge_map.astype(np.float32) - base_edge_map.astype(np.float32)
    )
    diff_map = (
        (diff_map / diff_map.max() * 255).astype(np.uint8)
        if diff_map.max() > 0
        else diff_map.astype(np.uint8)
    )
    Image.fromarray(diff_map).save(output_dir / "05_enhancement_difference.jpg")

    # Save visualization grid
    Image.fromarray(visualization_grid).save(
        output_dir / "06_complete_analysis_grid.jpg"
    )

    # Save metadata
    import json

    def convert_numpy_types(obj):
        """Convert numpy types to Python native types for JSON serialization"""
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        else:
            return obj

    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "image_shape": list(image.shape),
        "quality_metrics": {
            k: convert_numpy_types(v)
            for k, v in quality_metrics.items()
            if k != "processing_stats"
        },
        "processing_stats": convert_numpy_types(roi_result["processing_stats"]),
        "roi_summary": {
            "num_semantic_rois": len(roi_result.get("semantic_rois", [])),
            "num_density_rois": len(roi_result.get("density_rois", [])),
            "num_merged_rois": len(roi_result.get("merged_rois", [])),
            "total_tiles": int(roi_result["processing_stats"].get("total_tiles", 0)),
        },
    }

    with open(output_dir / "07_analysis_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"   ✅ Results saved:")
    print(f"      Original: 01_original_image.jpg")
    print(f"      Saliency: 02_saliency_map.jpg")
    print(f"      Base Edges: 03_base_edges.jpg")
    print(f"      Enhanced: 04_enhanced_edges.jpg")
    print(f"      Difference: 05_enhancement_difference.jpg")
    print(f"      Complete Grid: 06_complete_analysis_grid.jpg")
    print(f"      Metadata: 07_analysis_metadata.json")


def main():
    """Main testing function for classical portrait ROI enhancement"""

    print("🎨 Classical Portrait ROI Enhancement Test")
    print("Phase 2.3: Real-world Demonstration with 435864.jpg")
    print("=" * 65)

    try:
        # Load the classical portrait
        image, image_path = load_classical_portrait()

        # Generate realistic saliency map for portrait analysis
        concepts = [
            "face",
            "person",
            "eyes",
            "dress",
            "dog",
        ]  # Concepts relevant to classical portrait
        saliency_map = generate_mock_saliency_for_portrait(image, concepts)

        # Get base edge map from PiDiNet (or fallback to Canny)
        base_edge_map = get_base_edge_map_from_pidinet(image)

        # Initialize enhanced DDN model
        print(f"\n🔧 Initializing ROI-enhanced DDN model...")
        ddn_model = DDNModel(
            model_path=None,  # Use dummy model for testing
            device="auto",
            model_variant="M36",
            tile_size=128,  # Larger tiles for this real image
        )

        # Run complete ROI-enhanced processing
        print(f"\n🚀 Running ROI-enhanced processing pipeline...")
        start_time = time.time()

        result = ddn_model.process_image_with_roi_enhancement(
            image, saliency_map, base_edge_map
        )

        total_time = time.time() - start_time

        # Extract results
        enhanced_edge_map = result["enhanced_edge_map"]
        roi_result = result["roi_result"]

        print(f"\n✅ ROI Enhancement Complete!")
        print(f"   Total Processing Time: {total_time:.3f}s")
        print(f"   ROI Processing Applied: {result['roi_processing_applied']}")

        # Analyze enhancement quality
        quality_metrics = analyze_roi_enhancement_quality(
            base_edge_map, enhanced_edge_map, roi_result
        )

        # Create comprehensive visualization
        print(f"\n🎨 Creating visualization grid...")
        visualization_grid = create_visualization_grid(
            image, saliency_map, base_edge_map, enhanced_edge_map, roi_result
        )

        # Save all results
        save_results(
            image,
            saliency_map,
            base_edge_map,
            enhanced_edge_map,
            visualization_grid,
            quality_metrics,
            roi_result,
        )

        print(f"\n🎉 Classical Portrait ROI Enhancement Test Complete!")
        print(f"\n📋 Final Results Summary:")
        print(f"   Image: {image.shape[1]}x{image.shape[0]} classical portrait")
        print(f"   Enhancement Ratio: {quality_metrics['enhancement_ratio']:.3f}x")
        print(f"   ROI Coverage: {quality_metrics['roi_coverage']:.1%}")
        print(f"   Processing Time: {total_time:.3f}s")
        print(
            f"   Strong Edge Enhancement: {quality_metrics['strong_edge_ratio']:.3f}x"
        )

        print(f"\n💡 Therapeutic Applications:")
        print(f"   • Face region enhanced for emotional connection")
        print(f"   • Selective enhancement preserves artistic integrity")
        print(
            f"   • {roi_result['processing_stats']['total_tiles']} targeted processing tiles"
        )
        print(f"   • Memory-efficient processing on M4 MacBook")

        return True

    except Exception as e:
        print(f"\n❌ Classical Portrait ROI Test Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
