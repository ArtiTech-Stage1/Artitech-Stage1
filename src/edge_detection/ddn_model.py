"""
DDN Model Implementation
Doubly Decoupled Network for Edge Detection Integration

Author: ArtiTech Stage 1 Team
Date: December 2024
"""

import sys
import os
import time
import torch
import torch.nn as nn
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import yaml

# DDN 모델 import를 위한 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
DDN_PATH = PROJECT_ROOT / "external" / "DDN"
sys.path.insert(0, str(DDN_PATH))

try:
    from model.sigma_logit_unet import Mymodel

    print(f"✅ DDN Mymodel imported successfully from {DDN_PATH}")
except ImportError as e:
    print(f"❌ DDN import failed: {e}")
    raise

# Import ROI processor for enhanced functionality
try:
    from .saliency.roi_processor import DualROIProcessor, ROIRegion

    ROI_PROCESSING_AVAILABLE = True
except ImportError:
    print("⚠️ ROI processor not available, using standard tile processing only")
    ROI_PROCESSING_AVAILABLE = False


class DDNConfig:
    """DDN 모델 설정 클래스"""

    def __init__(self, config_dict: Dict = None):
        # 기본 설정값
        self.defaults = {
            "encoder": "DDN-M36",
            "distribution": "gs",
            "sampling": 1,  # 추론 시에는 1로 설정
            "noise_rate": 0.0,  # 추론 시에는 노이즈 없음
            "kl_weight": 1e-2,
            "Dulbrn": 16,
            "model": "model.sigma_logit_unet",
        }

        # 사용자 설정으로 업데이트
        if config_dict:
            self.defaults.update(config_dict)

    def get(self, key: str, default=None):
        """설정값 가져오기"""
        return self.defaults.get(key, default)

    def __getattr__(self, name):
        return self.defaults.get(name)

    def __getitem__(self, key):
        """딕셔너리 스타일 접근 지원"""
        return self.defaults.get(key)

    def __setitem__(self, key, value):
        """딕셔너리 스타일 설정 지원"""
        self.defaults[key] = value


class DDNArgs:
    """DDN 모델 초기화를 위한 arguments 클래스"""

    def __init__(self, config: DDNConfig):
        self.encoder = config.get("encoder", "DDN-M36")
        self.distribution = config.get("distribution", "gs")
        self.sampling = config.get("sampling", 1)
        self.noise_rate = config.get("noise_rate", 0.0)
        self.kl_weight = config.get("kl_weight", 1e-2)
        self.cfg = config
        self.model = config.get("model", "model.sigma_logit_unet")
        self.mode = "test"  # 추론 모드
        self.Dulbrn = config.get("Dulbrn", 16)  # 추가된 필드


class DDNModel:
    """
    DDN (Doubly Decoupled Network) 모델 래퍼
    PiDiNet과의 Hybrid Fusion을 위한 통합 인터페이스
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        config_path: Optional[str] = None,
        model_variant: str = "M36",  # M36, S18, B36
        tile_size: int = 16,
    ):
        """
        DDN 모델 초기화

        Args:
            model_path: DDN 모델 가중치 경로
            device: 연산 디바이스 ('auto', 'cuda', 'mps', 'cpu')
            config_path: DDN 설정 파일 경로
            model_variant: 모델 변형 (M36, S18, B36)
            tile_size: 타일 크기 (기본 16x16)
        """
        self.model_path = model_path
        self.device = self._setup_device(device)
        self.model_variant = model_variant
        self.tile_size = tile_size
        self.inference_times = []

        print(f"🔧 Initializing DDN-{model_variant} model...")
        print(f"💻 Device: {self.device}")

        # 설정 로드
        self.config = self._load_config(config_path)

        # 모델 초기화
        self.model = self._build_model()

        # 가중치 로드
        if model_path:
            self.load_weights(model_path)

        self.model.eval()
        print(f"✅ DDN model initialized successfully")

    def _setup_device(self, device: str) -> torch.device:
        """디바이스 설정"""
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif torch.backends.mps.is_available():
                return torch.device("mps")
            else:
                return torch.device("cpu")
        else:
            return torch.device(device)

    def _load_config(self, config_path: Optional[str]) -> DDNConfig:
        """DDN 설정 로드"""
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_dict = yaml.safe_load(f)
            print(f"📁 Loaded config from: {config_path}")
        else:
            # 기본 설정 사용
            config_dict = {
                "encoder": f"DDN-{self.model_variant}",
                "distribution": "gs",
                "sampling": 1,
                "noise_rate": 0.0,
                "Dulbrn": 16,
                "ckpt": {
                    "caformer_s18": None,
                    "caformer_m36": None,
                    "caformer_b36": None,
                },
            }
            print(f"⚙️ Using default DDN-{self.model_variant} config")

        return DDNConfig(config_dict)

    def _create_dummy_ddn_model(self) -> nn.Module:
        """테스트용 더미 DDN 모델 생성"""

        class DummyDDN(nn.Module):
            def __init__(self, tile_size=16):
                super().__init__()
                self.tile_size = tile_size
                # 간단한 CNN 구조
                self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
                self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
                self.conv3 = nn.Conv2d(64, 1, 3, padding=1)
                self.sigmoid = nn.Sigmoid()

            def forward(self, x):
                x = torch.relu(self.conv1(x))
                x = torch.relu(self.conv2(x))
                x = self.conv3(x)
                return self.sigmoid(x)  # 단일 출력 반환

        return DummyDDN(self.tile_size)

    def _build_model(self) -> nn.Module:
        """DDN 모델 아키텍처 구성"""
        try:
            # DDNArgs 객체 생성
            args = DDNArgs(self.config)

            # 테스트를 위해 간단한 dummy 모델 생성
            if not self.model_path:
                print(
                    "⚠️ No model weights provided, creating dummy DDN model for testing"
                )
                model = self._create_dummy_ddn_model()
            else:
                # DDN 모델 생성
                model = Mymodel(args, classes=1, gaauss=True)

            model = model.to(self.device)

            print(f"🏗️ DDN-{self.model_variant} architecture built")
            return model

        except Exception as e:
            print(f"❌ Failed to build DDN model: {e}")
            print("🔧 Creating fallback dummy model for testing...")
            return self._create_dummy_ddn_model().to(self.device)

    def load_weights(self, model_path: str):
        """DDN 모델 가중치 로드"""
        try:
            if not os.path.exists(model_path):
                print(f"⚠️ Model weights not found: {model_path}")
                print(f"📋 DDN model initialized without pre-trained weights")
                return

            checkpoint = torch.load(model_path, map_location=self.device)

            # 체크포인트 형식 확인
            if "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint

            # 모델에 가중치 로드
            self.model.load_state_dict(state_dict, strict=False)
            print(f"✅ Successfully loaded DDN weights from {model_path}")

        except Exception as e:
            print(f"❌ Failed to load DDN weights: {e}")
            print(f"📋 Continuing with randomly initialized weights")

    def preprocess_tile(self, tile: np.ndarray) -> torch.Tensor:
        """
        타일 이미지 전처리

        Args:
            tile: 입력 타일 (H, W, 3) BGR format

        Returns:
            전처리된 텐서 (1, 3, H, W)
        """
        # BGR → RGB 변환
        if len(tile.shape) == 3 and tile.shape[2] == 3:
            tile = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB)

        # 타일 크기 조정 (DDN은 다양한 크기 지원)
        if tile.shape[:2] != (self.tile_size, self.tile_size):
            tile = cv2.resize(tile, (self.tile_size, self.tile_size))

        # [0, 255] → [0, 1] 정규화
        tile = tile.astype(np.float32) / 255.0

        # ImageNet 정규화 적용
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])

        for i in range(3):
            tile[:, :, i] = (tile[:, :, i] - mean[i]) / std[i]

        # numpy → tensor 변환
        tensor = torch.from_numpy(tile.transpose(2, 0, 1)).unsqueeze(0)
        return tensor.to(self.device)

    def postprocess_tile(self, output: torch.Tensor) -> np.ndarray:
        """
        타일 출력 후처리

        Args:
            output: 모델 출력 텐서

        Returns:
            후처리된 엣지 맵 (H, W) [0, 255]
        """
        # 텐서 → numpy 변환
        if isinstance(output, (list, tuple)):
            # DDN은 여러 출력을 반환할 수 있음
            output = output[-1]  # 마지막 출력 사용

        edge_map = output.squeeze().cpu().numpy()

        # 시그모이드 적용 (필요한 경우)
        if edge_map.max() > 1.0 or edge_map.min() < 0.0:
            edge_map = torch.sigmoid(torch.from_numpy(edge_map)).numpy()

        # [0, 1] → [0, 255] 변환
        edge_map = np.clip(edge_map * 255, 0, 255).astype(np.uint8)

        return edge_map

    def inference_single_tile(self, tile: np.ndarray) -> np.ndarray:
        """
        단일 타일 추론

        Args:
            tile: 입력 타일 이미지 (H, W, 3)

        Returns:
            엣지 맵 (H, W) [0, 255]
        """
        start_time = time.time()

        # 전처리
        input_tensor = self.preprocess_tile(tile)

        # 추론
        with torch.no_grad():
            output = self.model(input_tensor)

        # 후처리
        edge_map = self.postprocess_tile(output)

        # 성능 기록
        inference_time = (time.time() - start_time) * 1000
        self.inference_times.append(inference_time)

        return edge_map

    def inference_batch(
        self, tiles: List[np.ndarray], batch_size: int = 8
    ) -> List[np.ndarray]:
        """
        타일 배치 추론 (효율성 향상)

        Args:
            tiles: 타일 이미지 리스트
            batch_size: 배치 크기

        Returns:
            엣지 맵 리스트
        """
        results = []

        for i in range(0, len(tiles), batch_size):
            batch_tiles = tiles[i : i + batch_size]

            # 배치 전처리
            batch_tensors = [self.preprocess_tile(tile) for tile in batch_tiles]
            batch_input = torch.cat(batch_tensors, dim=0)

            # 배치 추론
            with torch.no_grad():
                batch_output = self.model(batch_input)

            # 배치 후처리
            if isinstance(batch_output, (list, tuple)):
                batch_output = batch_output[-1]

            for j in range(batch_output.shape[0]):
                tile_output = batch_output[j : j + 1]
                edge_map = self.postprocess_tile(tile_output)
                results.append(edge_map)

        return results

    def get_performance_stats(self) -> Dict[str, float]:
        """성능 통계 반환"""
        if not self.inference_times:
            return {}

        times = np.array(self.inference_times)
        return {
            "mean_time_ms": float(np.mean(times)),
            "median_time_ms": float(np.median(times)),
            "min_time_ms": float(np.min(times)),
            "max_time_ms": float(np.max(times)),
            "std_time_ms": float(np.std(times)),
            "total_inferences": len(times),
        }

    # ===== ROI-SPECIFIC ENHANCEMENT METHODS =====

    def inference_roi_tiles(
        self, image: np.ndarray, roi_tiles: List[Dict], batch_size: int = 4
    ) -> Dict[str, np.ndarray]:
        """
        ROI-specific tile processing for enhanced edge detection

        Args:
            image: Original image (H, W, 3)
            roi_tiles: List of ROI tile dictionaries from DualROIProcessor
            batch_size: Number of tiles to process in each batch

        Returns:
            Dictionary mapping tile IDs to enhanced edge maps
        """
        if not ROI_PROCESSING_AVAILABLE:
            raise RuntimeError("ROI processing not available. Install saliency module.")

        start_time = time.time()

        print(f"🎯 Processing {len(roi_tiles)} ROI tiles with DDN enhancement...")

        tile_results = {}
        processed_tiles = []
        tile_metadata = []

        # Extract tiles from image
        for i, tile_info in enumerate(roi_tiles):
            x1, y1, x2, y2 = tile_info["bbox"]

            # Extract tile from image
            tile_image = image[y1:y2, x1:x2].copy()

            # Resize to model's expected tile size if needed
            if tile_image.shape[:2] != (self.tile_size, self.tile_size):
                tile_image = cv2.resize(tile_image, (self.tile_size, self.tile_size))

            processed_tiles.append(tile_image)
            tile_metadata.append(
                {
                    "id": f"roi_tile_{i}",
                    "bbox": tile_info["bbox"],
                    "roi_coverage": tile_info["roi_coverage"],
                    "original_size": (x2 - x1, y2 - y1),
                    "roi_region": tile_info.get("roi_region", None),
                }
            )

        # Batch inference on ROI tiles
        edge_maps = self.inference_batch(processed_tiles, batch_size=batch_size)

        # Process results with ROI-specific enhancements
        for i, (edge_map, metadata) in enumerate(zip(edge_maps, tile_metadata)):
            # Apply ROI-specific enhancement based on ROI type and coverage
            enhanced_edge_map = self._enhance_roi_edges(
                edge_map, metadata["roi_coverage"], metadata.get("roi_region", None)
            )

            # Resize back to original tile size if needed
            if metadata["original_size"] != (self.tile_size, self.tile_size):
                target_h, target_w = metadata["original_size"]
                enhanced_edge_map = cv2.resize(enhanced_edge_map, (target_w, target_h))

            tile_results[metadata["id"]] = {
                "edge_map": enhanced_edge_map,
                "metadata": metadata,
                "enhancement_applied": True,
            }

        processing_time = time.time() - start_time

        print(
            f"✅ ROI tile processing complete: {len(tile_results)} tiles in {processing_time:.3f}s"
        )

        return tile_results

    def _enhance_roi_edges(
        self,
        edge_map: np.ndarray,
        roi_coverage: float,
        roi_region: Optional["ROIRegion"] = None,
    ) -> np.ndarray:
        """
        Apply ROI-specific enhancements to edge maps

        Args:
            edge_map: Base edge map from DDN (H, W) [0, 255]
            roi_coverage: Percentage of tile covered by ROI [0, 1]
            roi_region: ROI region metadata for context-aware enhancement

        Returns:
            Enhanced edge map (H, W) [0, 255]
        """
        enhanced = edge_map.copy().astype(np.float32)

        # ROI coverage-based enhancement
        if roi_coverage > 0.7:
            # High ROI coverage: Strong enhancement
            enhancement_factor = 1.3
            contrast_boost = 1.2
        elif roi_coverage > 0.3:
            # Medium ROI coverage: Moderate enhancement
            enhancement_factor = 1.15
            contrast_boost = 1.1
        else:
            # Low ROI coverage: Minimal enhancement
            enhancement_factor = 1.05
            contrast_boost = 1.02

        # Apply enhancement
        enhanced = enhanced * enhancement_factor

        # ROI type-specific enhancements
        if roi_region and hasattr(roi_region, "roi_type"):
            if roi_region.roi_type == "semantic":
                # Semantic ROI: Emphasize strong edges, smooth weak ones
                strong_edges = enhanced > 128
                enhanced[strong_edges] = np.minimum(enhanced[strong_edges] * 1.2, 255)
                enhanced[~strong_edges] = enhanced[~strong_edges] * 0.9

            elif roi_region.roi_type == "density":
                # Density ROI: Preserve fine details
                enhanced = self._preserve_fine_details(enhanced)

            elif roi_region.roi_type == "merged":
                # Merged ROI: Balanced enhancement
                enhanced = self._balanced_enhancement(enhanced, roi_region.confidence)

        # Contrast adjustment
        enhanced = self._adjust_contrast(enhanced, contrast_boost)

        # Ensure valid range
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

        return enhanced

    def _preserve_fine_details(self, edge_map: np.ndarray) -> np.ndarray:
        """Preserve fine details in density ROIs"""
        # Apply gentle Gaussian blur to reduce noise while preserving details
        blurred = cv2.GaussianBlur(edge_map, (3, 3), 0.5)

        # Combine original and blurred using weighted average
        preserved = 0.7 * edge_map + 0.3 * blurred

        return preserved

    def _balanced_enhancement(
        self, edge_map: np.ndarray, confidence: float
    ) -> np.ndarray:
        """Apply balanced enhancement for merged ROIs"""
        # Confidence-based enhancement strength
        strength = 0.9 + (confidence * 0.3)  # Range: 0.9 to 1.2

        # Apply adaptive histogram equalization for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(edge_map.astype(np.uint8)).astype(np.float32)

        # Apply confidence-based scaling
        enhanced = enhanced * strength

        return enhanced

    def _adjust_contrast(
        self, edge_map: np.ndarray, contrast_factor: float
    ) -> np.ndarray:
        """Adjust contrast of edge map"""
        # Apply contrast adjustment using power function
        normalized = edge_map / 255.0
        adjusted = np.power(normalized, 1.0 / contrast_factor)
        return adjusted * 255.0

    def reconstruct_from_roi_tiles(
        self,
        tile_results: Dict[str, np.ndarray],
        image_shape: Tuple[int, int],
        blending_mode: str = "weighted",
    ) -> np.ndarray:
        """
        Reconstruct full edge map from ROI tile results

        Args:
            tile_results: Results from inference_roi_tiles
            image_shape: (height, width) of target image
            blending_mode: Tile blending strategy ('weighted', 'max', 'average')

        Returns:
            Reconstructed edge map (H, W) [0, 255]
        """
        height, width = image_shape
        reconstruction = np.zeros((height, width), dtype=np.float32)
        weight_map = np.zeros((height, width), dtype=np.float32)

        print(f"🔄 Reconstructing full edge map from {len(tile_results)} ROI tiles...")

        for tile_id, tile_data in tile_results.items():
            edge_map = tile_data["edge_map"]
            metadata = tile_data["metadata"]
            x1, y1, x2, y2 = metadata["bbox"]

            # Calculate expected tile dimensions
            expected_height = y2 - y1
            expected_width = x2 - x1

            # Ensure edge_map matches expected dimensions
            if edge_map.shape != (expected_height, expected_width):
                # Resize edge_map to match expected tile size
                edge_map = cv2.resize(edge_map, (expected_width, expected_height))

            # Calculate blending weights based on ROI coverage
            roi_coverage = metadata["roi_coverage"]
            base_weight = 0.5 + (roi_coverage * 0.5)  # Range: 0.5 to 1.0

            if blending_mode == "weighted":
                # Distance-based weight tapering from tile center
                tile_h, tile_w = edge_map.shape
                center_y, center_x = tile_h // 2, tile_w // 2

                y_coords, x_coords = np.ogrid[:tile_h, :tile_w]
                distance_from_center = np.sqrt(
                    (x_coords - center_x) ** 2 + (y_coords - center_y) ** 2
                )
                max_distance = np.sqrt(center_x**2 + center_y**2)

                # Create weight mask: stronger at center, weaker at edges
                weight_mask = base_weight * (
                    1.0 - (distance_from_center / max_distance) * 0.5
                )
                weight_mask = np.clip(weight_mask, 0.1, 1.0)

            elif blending_mode == "max":
                weight_mask = np.ones_like(edge_map) * base_weight

            else:  # average
                weight_mask = np.ones_like(edge_map) * base_weight

            # Apply weighted blending
            reconstruction[y1:y2, x1:x2] += edge_map.astype(np.float32) * weight_mask
            weight_map[y1:y2, x1:x2] += weight_mask

        # Normalize by weight map to handle overlapping regions
        valid_regions = weight_map > 0
        reconstruction[valid_regions] /= weight_map[valid_regions]

        # Fill empty regions with zero or interpolation
        empty_regions = weight_map == 0
        if np.any(empty_regions):
            print(f"⚠️ Filling {np.sum(empty_regions)} empty pixels with interpolation")
            # Simple nearest neighbor interpolation for empty regions
            from scipy.ndimage import binary_dilation

            # Expand valid regions slightly and use for interpolation
            expanded_valid = binary_dilation(valid_regions, iterations=3)
            if np.any(expanded_valid & empty_regions):
                # Use nearest valid value for empty pixels
                from scipy.ndimage import distance_transform_edt

                indices = distance_transform_edt(empty_regions, return_indices=True)[1]
                # Fix the indexing issue - handle 2D indices properly
                y_indices, x_indices = indices
                reconstruction[empty_regions] = reconstruction[
                    y_indices[empty_regions], x_indices[empty_regions]
                ]

        result = np.clip(reconstruction, 0, 255).astype(np.uint8)

        print(f"✅ Reconstruction complete: {image_shape} edge map")

        return result

    def process_image_with_roi_enhancement(
        self, image: np.ndarray, saliency_map: np.ndarray, base_edge_map: np.ndarray
    ) -> Dict[str, Any]:
        """
        Complete ROI-enhanced edge detection pipeline

        Args:
            image: Input image (H, W, 3)
            saliency_map: Saliency map from ConceptAttention (H, W) [0, 1]
            base_edge_map: Base edge map from PiDiNet (H, W) [0, 255]

        Returns:
            Dictionary with enhanced edge maps and processing metadata
        """
        if not ROI_PROCESSING_AVAILABLE:
            print("⚠️ ROI processing not available, returning base edge map")
            return {
                "enhanced_edge_map": base_edge_map,
                "base_edge_map": base_edge_map,
                "roi_processing_applied": False,
            }

        start_time = time.time()

        print(f"🚀 Starting ROI-enhanced DDN processing...")

        # Initialize ROI processor
        roi_processor = DualROIProcessor()

        # Process dual ROI
        roi_result = roi_processor.process_dual_roi(saliency_map, base_edge_map / 255.0)

        # Get all ROI tiles
        all_tiles = []
        for roi_tiles in roi_result["roi_tiles"].values():
            all_tiles.extend(roi_tiles)

        if not all_tiles:
            print("⚠️ No ROI tiles found, returning base edge map")
            return {
                "enhanced_edge_map": base_edge_map,
                "base_edge_map": base_edge_map,
                "roi_processing_applied": False,
                "roi_result": roi_result,
            }

        # Process ROI tiles with DDN enhancement
        tile_results = self.inference_roi_tiles(image, all_tiles)

        # Reconstruct enhanced edge map
        enhanced_edge_map = self.reconstruct_from_roi_tiles(
            tile_results, image.shape[:2], blending_mode="weighted"
        )

        # Combine with base edge map for full coverage
        final_edge_map = self._combine_enhanced_with_base(
            enhanced_edge_map, base_edge_map, roi_result["merged_rois"]
        )

        total_time = time.time() - start_time

        result = {
            "enhanced_edge_map": final_edge_map,
            "base_edge_map": base_edge_map,
            "roi_enhanced_map": enhanced_edge_map,
            "roi_processing_applied": True,
            "roi_result": roi_result,
            "tile_results": tile_results,
            "processing_stats": {
                "total_time": total_time,
                "num_roi_tiles": len(all_tiles),
                "num_merged_rois": len(roi_result["merged_rois"]),
                **self.get_performance_stats(),
            },
        }

        print(f"🎉 ROI-enhanced processing complete in {total_time:.3f}s")

        return result

    def _combine_enhanced_with_base(
        self,
        enhanced_map: np.ndarray,
        base_map: np.ndarray,
        roi_regions: List["ROIRegion"],
    ) -> np.ndarray:
        """
        Combine ROI-enhanced regions with base edge map

        Args:
            enhanced_map: ROI-enhanced edge map
            base_map: Base edge map
            roi_regions: List of ROI regions for blending

        Returns:
            Combined edge map
        """
        result = base_map.copy().astype(np.float32)
        enhanced = enhanced_map.astype(np.float32)

        # Create blending mask from ROI regions
        blend_mask = np.zeros(base_map.shape, dtype=np.float32)

        for roi in roi_regions:
            # Use ROI mask for blending
            roi_mask = roi.mask.astype(np.float32)

            # Smooth the mask edges for seamless blending
            roi_mask = cv2.GaussianBlur(roi_mask, (5, 5), 1.0)

            # Weight by ROI confidence
            weighted_mask = roi_mask * roi.confidence

            blend_mask = np.maximum(blend_mask, weighted_mask)

        # Ensure blend mask is in [0, 1] range
        if np.max(blend_mask) > 0:
            blend_mask = np.clip(blend_mask, 0, 1)

        # Blend enhanced and base maps
        result = (1.0 - blend_mask) * result + blend_mask * enhanced

        return np.clip(result, 0, 255).astype(np.uint8)


# 테스트 함수
def test_ddn_model():
    """DDN 모델 래퍼 테스트"""
    try:
        print("🧪 Testing DDN Model Wrapper...")

        # 모델 초기화
        ddn = DDNModel(
            model_path=None,  # 가중치 없이 테스트
            device="auto",
            model_variant="M36",
        )

        # 더미 타일로 테스트
        dummy_tile = np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8)

        # 단일 추론 테스트
        result = ddn.inference_single_tile(dummy_tile)
        print(f"✅ Single inference test: output shape {result.shape}")

        # 배치 추론 테스트
        dummy_tiles = [dummy_tile for _ in range(4)]
        batch_results = ddn.inference_batch(dummy_tiles, batch_size=2)
        print(f"✅ Batch inference test: {len(batch_results)} results")

        # 성능 통계
        stats = ddn.get_performance_stats()
        print(f"📊 Performance stats: {stats}")

        print("🎉 DDN Model Wrapper test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ DDN Model test failed: {e}")
        return False


if __name__ == "__main__":
    test_ddn_model()
