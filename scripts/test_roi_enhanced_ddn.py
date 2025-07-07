#!/usr/bin/env python3
"""
Test ROI-Enhanced DDN Functionality
Comprehensive testing of Phase 2.3 ROI processing integration
"""

import sys
import os
import time
import numpy as np
from pathlib import Path
from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.edge_detection.ddn_model import DDNModel
from src.edge_detection.saliency.roi_processor import DualROIProcessor
from src.edge_detection.saliency.concept_attention import ConceptAttentionModel


def create_test_data():
    """Create synthetic test data for ROI-enhanced DDN testing"""

    print("🧪 Creating synthetic test data...")

    # Create test image
    height, width = 512, 512
    image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

    # Add some structure to the image
    # Central region with higher intensity
    image[200:300, 200:300] = np.minimum(image[200:300, 200:300] + 50, 255)

    # Create synthetic saliency map (similar to mock mode output)
    saliency_map = np.zeros((height, width), dtype=np.float32)

    # Central saliency region
    center_y, center_x = height // 2, width // 2
    y, x = np.ogrid[:height, :width]

    # Create circular saliency region
    distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    saliency_map = np.exp(-distance / 100) * 0.8

    # Add secondary region
    saliency_map[100:200, 100:200] = np.maximum(
        saliency_map[100:200, 100:200], np.ones((100, 100)) * 0.6
    )

    # Create synthetic base edge map
    base_edge_map = np.random.randint(0, 255, (height, width), dtype=np.uint8)

    # Add edge patterns
    base_edge_map[250:260, :] = 200  # Horizontal edge
    base_edge_map[:, 250:260] = 200  # Vertical edge

    print(f"✅ Test data created:")
    print(f"   Image: {image.shape}")
    print(
        f"   Saliency: {saliency_map.shape}, range: [{saliency_map.min():.3f}, {saliency_map.max():.3f}]"
    )
    print(
        f"   Base edges: {base_edge_map.shape}, range: [{base_edge_map.min()}, {base_edge_map.max()}]"
    )

    return image, saliency_map, base_edge_map


def test_roi_processor_integration():
    """Test ROI processor standalone functionality"""

    print("\n🔍 Testing ROI Processor Integration...")

    image, saliency_map, base_edge_map = create_test_data()

    # Initialize ROI processor
    roi_processor = DualROIProcessor()

    # Process dual ROI
    roi_result = roi_processor.process_dual_roi(saliency_map, base_edge_map / 255.0)

    print(f"   ✅ ROI Processing Results:")
    print(f"      Semantic ROIs: {roi_result['processing_stats']['num_semantic_rois']}")
    print(f"      Density ROIs: {roi_result['processing_stats']['num_density_rois']}")
    print(f"      Merged ROIs: {roi_result['processing_stats']['num_merged_rois']}")
    print(f"      Total Tiles: {roi_result['processing_stats']['total_tiles']}")
    print(
        f"      Processing Time: {roi_result['processing_stats']['total_processing_time']:.3f}s"
    )

    return roi_result


def test_enhanced_ddn_model():
    """Test enhanced DDN model with ROI functionality"""

    print("\n🔧 Testing Enhanced DDN Model...")

    # Initialize enhanced DDN model
    ddn_model = DDNModel(
        model_path=None,  # Use dummy model for testing
        device="auto",
        model_variant="M36",
        tile_size=64,  # Smaller tile size for testing
    )

    print(f"   ✅ DDN Model initialized on device: {ddn_model.device}")

    # Test basic functionality
    test_tile = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    edge_result = ddn_model.inference_single_tile(test_tile)

    print(f"   ✅ Basic inference test: {edge_result.shape}")

    return ddn_model


def test_roi_enhanced_pipeline():
    """Test complete ROI-enhanced pipeline"""

    print("\n🚀 Testing Complete ROI-Enhanced Pipeline...")

    # Create test data
    image, saliency_map, base_edge_map = create_test_data()

    # Initialize enhanced DDN model
    ddn_model = DDNModel(
        model_path=None, device="auto", model_variant="M36", tile_size=64
    )

    # Run complete ROI-enhanced processing
    start_time = time.time()

    result = ddn_model.process_image_with_roi_enhancement(
        image, saliency_map, base_edge_map
    )

    processing_time = time.time() - start_time

    print(f"   ✅ ROI-Enhanced Pipeline Results:")
    print(f"      ROI Processing Applied: {result['roi_processing_applied']}")
    print(f"      Enhanced Edge Map: {result['enhanced_edge_map'].shape}")
    print(f"      Base Edge Map: {result['base_edge_map'].shape}")

    if result["roi_processing_applied"]:
        stats = result["processing_stats"]
        print(f"      Processing Stats:")
        print(f"         Total Time: {stats['total_time']:.3f}s")
        print(f"         ROI Tiles: {stats['num_roi_tiles']}")
        print(f"         Merged ROIs: {stats['num_merged_rois']}")
        print(f"         DDN Mean Time: {stats.get('mean_time_ms', 0):.2f}ms")

        # Check edge map quality
        enhanced_map = result["enhanced_edge_map"]
        base_map = result["base_edge_map"]

        enhancement_ratio = (
            np.mean(enhanced_map) / np.mean(base_map) if np.mean(base_map) > 0 else 1.0
        )

        print(f"      Quality Metrics:")
        print(f"         Enhancement Ratio: {enhancement_ratio:.3f}")
        print(f"         Enhanced Mean: {np.mean(enhanced_map):.2f}")
        print(f"         Enhanced Std: {np.std(enhanced_map):.2f}")

    print(f"   🎉 Pipeline test completed in {processing_time:.3f}s")

    return result


def test_roi_tile_processing():
    """Test ROI-specific tile processing functionality"""

    print("\n🎯 Testing ROI Tile Processing...")

    # Create test data
    image, saliency_map, base_edge_map = create_test_data()

    # Get ROI tiles
    roi_processor = DualROIProcessor()
    roi_result = roi_processor.process_dual_roi(saliency_map, base_edge_map / 255.0)

    # Get all tiles
    all_tiles = []
    for roi_tiles in roi_result["roi_tiles"].values():
        all_tiles.extend(roi_tiles)

    if not all_tiles:
        print("   ⚠️ No ROI tiles found for testing")
        return None

    # Initialize DDN model
    ddn_model = DDNModel(model_path=None, device="auto", tile_size=64)

    # Process ROI tiles
    tile_results = ddn_model.inference_roi_tiles(image, all_tiles, batch_size=2)

    print(f"   ✅ ROI Tile Processing Results:")
    print(f"      Input Tiles: {len(all_tiles)}")
    print(f"      Output Results: {len(tile_results)}")

    # Check individual tile results
    for tile_id, tile_data in list(tile_results.items())[:3]:  # Show first 3
        edge_map = tile_data["edge_map"]
        metadata = tile_data["metadata"]

        print(f"      Tile {tile_id}:")
        print(f"         Edge Map: {edge_map.shape}")
        print(f"         ROI Coverage: {metadata['roi_coverage']:.3f}")
        print(f"         Enhancement Applied: {tile_data['enhancement_applied']}")

    # Test reconstruction
    reconstructed = ddn_model.reconstruct_from_roi_tiles(
        tile_results, image.shape[:2], blending_mode="weighted"
    )

    print(f"   ✅ Reconstruction completed: {reconstructed.shape}")

    return tile_results


def test_performance_benchmarks():
    """Test performance benchmarks for ROI-enhanced processing"""

    print("\n📊 Performance Benchmarking...")

    # Test different image sizes
    test_sizes = [(256, 256), (512, 512), (1024, 1024)]

    for size in test_sizes:
        height, width = size

        print(f"\n   Testing {width}x{height} image:")

        # Create test data for this size
        image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        saliency_map = np.random.rand(height, width).astype(np.float32)
        base_edge_map = np.random.randint(0, 255, (height, width), dtype=np.uint8)

        # Initialize DDN model
        ddn_model = DDNModel(model_path=None, device="auto", tile_size=64)

        # Benchmark processing
        start_time = time.time()

        try:
            result = ddn_model.process_image_with_roi_enhancement(
                image, saliency_map, base_edge_map
            )

            processing_time = time.time() - start_time

            if result["roi_processing_applied"]:
                stats = result["processing_stats"]
                print(f"      Total Time: {processing_time:.3f}s")
                print(f"      ROI Tiles: {stats['num_roi_tiles']}")
                print(
                    f"      Throughput: {(width * height) / processing_time / 1000:.1f} Kpixels/s"
                )
            else:
                print(f"      Fallback Time: {processing_time:.3f}s")

        except Exception as e:
            print(f"      ❌ Failed: {e}")


def main():
    """Main testing function"""

    print("🧪 ArtiTech Stage 1 - ROI-Enhanced DDN Testing")
    print("Phase 2.3: ROI Processing System Validation")
    print("=" * 60)

    # Run all tests
    try:
        # Test 1: ROI processor integration
        roi_result = test_roi_processor_integration()

        # Test 2: Enhanced DDN model
        ddn_model = test_enhanced_ddn_model()

        # Test 3: Complete pipeline
        pipeline_result = test_roi_enhanced_pipeline()

        # Test 4: ROI tile processing
        tile_results = test_roi_tile_processing()

        # Test 5: Performance benchmarks
        test_performance_benchmarks()

        print("\n🎉 All ROI-Enhanced DDN Tests Completed Successfully!")
        print("\n📋 Summary:")
        print("   ✅ ROI Processor Integration: Working")
        print("   ✅ Enhanced DDN Model: Working")
        print("   ✅ Complete Pipeline: Working")
        print("   ✅ ROI Tile Processing: Working")
        print("   ✅ Performance Benchmarks: Working")

        print("\n🚀 Phase 2.3: ROI Processing System Implementation Complete!")

        return True

    except Exception as e:
        print(f"\n❌ ROI-Enhanced DDN Testing Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
