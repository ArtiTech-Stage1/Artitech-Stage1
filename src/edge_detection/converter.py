"""
ONNX Converter Module
Implementation for ArtiTech Stage 1 - PyTorch to ONNX conversion with quantization
"""

import torch
import onnx
import onnxruntime as ort
import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ONNXConverter:
    """Convert PyTorch models to ONNX with optimization"""

    def __init__(self):
        # Determine best execution providers for the platform
        self.providers = ["CPUExecutionProvider"]

        # Check for Apple Silicon optimization
        if torch.backends.mps.is_available():
            available_providers = ort.get_available_providers()
            if "CoreMLExecutionProvider" in available_providers:
                self.providers.insert(0, "CoreMLExecutionProvider")
                logger.info("CoreML execution provider available")

        logger.info(f"ONNX providers: {self.providers}")

    def convert_pidinet_to_onnx(
        self,
        pytorch_model: torch.nn.Module,
        output_path: str,
        input_shape: Tuple[int, int, int, int] = (1, 3, 512, 512),
        opset_version: int = 11,
    ) -> bool:
        """Convert PiDiNet PyTorch model to ONNX"""
        try:
            # Ensure model is in eval mode
            pytorch_model.eval()

            # Create dummy input
            dummy_input = torch.randn(*input_shape)
            logger.info(f"Converting model with input shape: {input_shape}")

            # Export to ONNX
            torch.onnx.export(
                pytorch_model,
                dummy_input,
                output_path,
                export_params=True,
                opset_version=opset_version,
                do_constant_folding=True,
                input_names=["input"],
                output_names=["edge_map"],
                dynamic_axes={
                    "input": {0: "batch_size"},
                    "edge_map": {0: "batch_size"},
                },
                verbose=False,
            )

            # Verify ONNX model
            onnx_model = onnx.load(output_path)
            onnx.checker.check_model(onnx_model)

            logger.info(f"Successfully converted PyTorch model to ONNX: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to convert model to ONNX: {e}")
            return False

    def quantize_to_int8(
        self,
        onnx_model_path: str,
        quantized_output_path: str,
        calibration_data: List[np.ndarray],
    ) -> bool:
        """Quantize ONNX model to INT8 for faster inference"""
        try:
            from onnxruntime.quantization import quantize_static, CalibrationDataReader

            class CalibrationDataset(CalibrationDataReader):
                def __init__(self, data: List[np.ndarray]):
                    self.data = data
                    self.current = 0

                def get_next(self):
                    if self.current >= len(self.data):
                        return None

                    input_data = {"input": self.data[self.current]}
                    self.current += 1
                    return input_data

            calibration_dataset = CalibrationDataset(calibration_data)

            logger.info(
                f"Quantizing model with {len(calibration_data)} calibration samples"
            )

            quantize_static(
                onnx_model_path,
                quantized_output_path,
                calibration_dataset,
                quant_format="QOperator",  # Use QOperator for better compatibility
                activation_type="int8",
                weight_type="int8",
            )

            logger.info(
                f"Successfully quantized model to INT8: {quantized_output_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to quantize model: {e}")
            return False

    def create_onnx_session(
        self, model_path: str, session_options: Optional[ort.SessionOptions] = None
    ) -> ort.InferenceSession:
        """Create ONNX Runtime inference session with optimizations"""
        try:
            # Create session options if not provided
            if session_options is None:
                session_options = ort.SessionOptions()
                session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                session_options.graph_optimization_level = (
                    ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                )
                session_options.inter_op_num_threads = (
                    1  # Single thread for better latency
                )
                session_options.intra_op_num_threads = 1

            # Create session
            session = ort.InferenceSession(
                model_path, providers=self.providers, sess_options=session_options
            )

            logger.info(f"Created ONNX session for {model_path}")
            logger.info(
                f"Input info: {[(inp.name, inp.shape, inp.type) for inp in session.get_inputs()]}"
            )
            logger.info(
                f"Output info: {[(out.name, out.shape, out.type) for out in session.get_outputs()]}"
            )

            return session

        except Exception as e:
            logger.error(f"Failed to create ONNX session: {e}")
            raise

    def benchmark_model(
        self, session: ort.InferenceSession, input_data: np.ndarray, num_runs: int = 100
    ) -> Dict[str, float]:
        """Benchmark ONNX model performance"""
        import time
        import statistics

        # Warm up
        for _ in range(10):
            _ = session.run(None, {"input": input_data})

        # Benchmark
        times = []
        for _ in range(num_runs):
            start_time = time.perf_counter()
            _ = session.run(None, {"input": input_data})
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to ms

        stats = {
            "mean_ms": statistics.mean(times),
            "median_ms": statistics.median(times),
            "min_ms": min(times),
            "max_ms": max(times),
            "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
            "p95_ms": statistics.quantiles(times, n=20)[18]
            if len(times) >= 20
            else max(times),
            "p99_ms": statistics.quantiles(times, n=100)[98]
            if len(times) >= 100
            else max(times),
        }

        logger.info(f"Benchmark results: {stats}")
        return stats

    def generate_calibration_data(
        self,
        images: List[np.ndarray],
        input_shape: Tuple[int, int, int, int] = (1, 3, 512, 512),
    ) -> List[np.ndarray]:
        """Generate calibration data for quantization"""
        calibration_data = []

        for img in images:
            # Preprocess image
            if len(img.shape) == 3:
                img = cv2.resize(img, (input_shape[3], input_shape[2]))
                img = img.astype(np.float32) / 255.0
                img = img.transpose(2, 0, 1)  # HWC to CHW
                img = np.expand_dims(img, axis=0)  # Add batch dimension
            else:
                # Already preprocessed
                img = img.astype(np.float32)

            calibration_data.append(img)

        logger.info(f"Generated {len(calibration_data)} calibration samples")
        return calibration_data

    def validate_conversion(
        self,
        pytorch_model: torch.nn.Module,
        onnx_session: ort.InferenceSession,
        test_input: np.ndarray,
        tolerance: float = 1e-5,
    ) -> bool:
        """Validate that ONNX model produces similar results to PyTorch"""
        try:
            # PyTorch inference
            pytorch_model.eval()
            with torch.no_grad():
                torch_input = torch.from_numpy(test_input)
                torch_output = pytorch_model(torch_input).cpu().numpy()

            # ONNX inference
            onnx_output = onnx_session.run(None, {"input": test_input})[0]

            # Compare outputs
            diff = np.abs(torch_output - onnx_output)
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)

            is_valid = max_diff < tolerance

            logger.info(f"Validation results:")
            logger.info(f"  Max difference: {max_diff:.8f}")
            logger.info(f"  Mean difference: {mean_diff:.8f}")
            logger.info(f"  Tolerance: {tolerance}")
            logger.info(f"  Valid: {is_valid}")

            return is_valid

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False

    def optimize_for_mobile(
        self, onnx_model_path: str, optimized_output_path: str
    ) -> bool:
        """Apply mobile-specific optimizations"""
        try:
            # Load and optimize the model
            onnx_model = onnx.load(onnx_model_path)

            # Apply optimizations
            from onnxoptimizer import optimize

            optimized_model = optimize(
                onnx_model,
                passes=[
                    "eliminate_deadend",
                    "eliminate_identity",
                    "eliminate_nop_dropout",
                    "eliminate_nop_pad",
                    "extract_constant_to_initializer",
                    "fuse_add_bias_into_conv",
                    "fuse_consecutive_squeezes",
                    "fuse_consecutive_transposes",
                    "fuse_matmul_add_bias_into_gemm",
                    "fuse_pad_into_conv",
                    "fuse_transpose_into_gemm",
                ],
            )

            # Save optimized model
            onnx.save(optimized_model, optimized_output_path)

            logger.info(f"Mobile optimization completed: {optimized_output_path}")
            return True

        except ImportError:
            logger.warning("onnxoptimizer not available, skipping mobile optimization")
            return False
        except Exception as e:
            logger.error(f"Mobile optimization failed: {e}")
            return False
