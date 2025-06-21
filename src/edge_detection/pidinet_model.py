"""
Real PiDiNet Model Implementation
Adapted from: https://github.com/hellozhuo/pidinet

Author: ArtiTech Stage 1 Team
Date: December 2024
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import time
import os


# Pixel Difference Convolution Operations
class Conv2d(nn.Module):
    def __init__(
        self,
        pdc,
        in_channels,
        out_channels,
        kernel_size,
        stride=1,
        padding=0,
        dilation=1,
        groups=1,
        bias=False,
    ):
        super(Conv2d, self).__init__()
        if in_channels % groups != 0:
            raise ValueError("in_channels must be divisible by groups")
        if out_channels % groups != 0:
            raise ValueError("out_channels must be divisible by groups")
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.groups = groups
        self.weight = nn.Parameter(
            torch.Tensor(out_channels, in_channels // groups, kernel_size, kernel_size)
        )
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter("bias", None)
        self.reset_parameters()
        self.pdc = pdc

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in)
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, input):
        return self.pdc(
            input,
            self.weight,
            self.bias,
            self.stride,
            self.padding,
            self.dilation,
            self.groups,
        )


def createConvFunc(op_type):
    """Create convolution function based on operation type"""
    assert op_type in ["cv", "cd", "ad", "rd"], "unknown op type: %s" % str(op_type)
    if op_type == "cv":
        return F.conv2d

    if op_type == "cd":

        def func(x, weights, bias=None, stride=1, padding=0, dilation=1, groups=1):
            assert dilation in [1, 2], "dilation for cd_conv should be in 1 or 2"
            assert weights.size(2) == 3 and weights.size(3) == 3, (
                "kernel size for cd_conv should be 3x3"
            )
            assert padding == dilation, "padding for cd_conv set wrong"

            weights_c = weights.sum(dim=[2, 3], keepdim=True)
            yc = F.conv2d(x, weights_c, stride=stride, padding=0, groups=groups)
            y = F.conv2d(
                x,
                weights,
                bias,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
            )
            return y - yc

        return func
    elif op_type == "ad":

        def func(x, weights, bias=None, stride=1, padding=0, dilation=1, groups=1):
            assert dilation in [1, 2], "dilation for ad_conv should be in 1 or 2"
            assert weights.size(2) == 3 and weights.size(3) == 3, (
                "kernel size for ad_conv should be 3x3"
            )
            assert padding == dilation, "padding for ad_conv set wrong"

            shape = weights.shape
            weights = weights.view(shape[0], shape[1], -1)
            weights_conv = (weights - weights[:, :, [3, 0, 1, 6, 4, 2, 7, 8, 5]]).view(
                shape
            )  # clock-wise
            y = F.conv2d(
                x,
                weights_conv,
                bias,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
            )
            return y

        return func
    elif op_type == "rd":

        def func(x, weights, bias=None, stride=1, padding=0, dilation=1, groups=1):
            assert dilation in [1, 2], "dilation for rd_conv should be in 1 or 2"
            assert weights.size(2) == 3 and weights.size(3) == 3, (
                "kernel size for rd_conv should be 3x3"
            )
            padding = 2 * dilation

            shape = weights.shape
            # Create buffer on the same device as weights
            buffer = torch.zeros(
                shape[0], shape[1], 5 * 5, device=weights.device, dtype=weights.dtype
            )
            weights = weights.view(shape[0], shape[1], -1)
            buffer[:, :, [0, 2, 4, 10, 14, 20, 22, 24]] = weights[:, :, 1:]
            buffer[:, :, [6, 7, 8, 11, 13, 16, 17, 18]] = -weights[:, :, 1:]
            buffer[:, :, 12] = 0
            buffer = buffer.view(shape[0], shape[1], 5, 5)
            y = F.conv2d(
                x,
                buffer,
                bias,
                stride=stride,
                padding=padding,
                dilation=dilation,
                groups=groups,
            )
            return y

        return func


# PiDiNet Architecture Components
class CSAM(nn.Module):
    """Compact Spatial Attention Module"""

    def __init__(self, channels):
        super(CSAM, self).__init__()
        mid_channels = 4
        self.relu1 = nn.ReLU()
        self.conv1 = nn.Conv2d(channels, mid_channels, kernel_size=1, padding=0)
        self.conv2 = nn.Conv2d(mid_channels, 1, kernel_size=3, padding=1, bias=False)
        self.sigmoid = nn.Sigmoid()
        nn.init.constant_(self.conv1.bias, 0)

    def forward(self, x):
        y = self.relu1(x)
        y = self.conv1(y)
        y = self.conv2(y)
        y = self.sigmoid(y)
        return x * y


class CDCM(nn.Module):
    """Compact Dilation Convolution based Module"""

    def __init__(self, in_channels, out_channels):
        super(CDCM, self).__init__()
        self.relu1 = nn.ReLU()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, padding=0)
        self.conv2_1 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, dilation=5, padding=5, bias=False
        )
        self.conv2_2 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, dilation=7, padding=7, bias=False
        )
        self.conv2_3 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, dilation=9, padding=9, bias=False
        )
        self.conv2_4 = nn.Conv2d(
            out_channels,
            out_channels,
            kernel_size=3,
            dilation=11,
            padding=11,
            bias=False,
        )
        nn.init.constant_(self.conv1.bias, 0)

    def forward(self, x):
        x = self.relu1(x)
        x = self.conv1(x)
        x1 = self.conv2_1(x)
        x2 = self.conv2_2(x)
        x3 = self.conv2_3(x)
        x4 = self.conv2_4(x)
        return x1 + x2 + x3 + x4


class MapReduce(nn.Module):
    """Reduce feature maps into a single edge map"""

    def __init__(self, channels):
        super(MapReduce, self).__init__()
        self.conv = nn.Conv2d(channels, 1, kernel_size=1, padding=0)
        nn.init.constant_(self.conv.bias, 0)

    def forward(self, x):
        return self.conv(x)


class PDCBlock(nn.Module):
    def __init__(self, pdc, inplane, ouplane, stride=1):
        super(PDCBlock, self).__init__()
        self.stride = stride

        if self.stride > 1:
            self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
            self.shortcut = nn.Conv2d(inplane, ouplane, kernel_size=1, padding=0)
        self.conv1 = Conv2d(
            pdc, inplane, inplane, kernel_size=3, padding=1, groups=inplane, bias=False
        )
        self.relu2 = nn.ReLU()
        self.conv2 = nn.Conv2d(inplane, ouplane, kernel_size=1, padding=0, bias=False)

    def forward(self, x):
        if self.stride > 1:
            x = self.pool(x)
        y = self.conv1(x)
        y = self.relu2(y)
        y = self.conv2(y)
        if self.stride > 1:
            x = self.shortcut(x)
        y = y + x
        return y


class PDCBlock_converted(nn.Module):
    """CPDC, APDC can be converted to vanilla 3x3 convolution, RPDC to vanilla 5x5 convolution"""

    def __init__(self, pdc, inplane, ouplane, stride=1):
        super(PDCBlock_converted, self).__init__()
        self.stride = stride

        if self.stride > 1:
            self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
            self.shortcut = nn.Conv2d(inplane, ouplane, kernel_size=1, padding=0)
        if pdc == "rd":
            self.conv1 = nn.Conv2d(
                inplane, inplane, kernel_size=5, padding=2, groups=inplane, bias=False
            )
        else:
            self.conv1 = nn.Conv2d(
                inplane, inplane, kernel_size=3, padding=1, groups=inplane, bias=False
            )
        self.relu2 = nn.ReLU()
        self.conv2 = nn.Conv2d(inplane, ouplane, kernel_size=1, padding=0, bias=False)

    def forward(self, x):
        if self.stride > 1:
            x = self.pool(x)
        y = self.conv1(x)
        y = self.relu2(y)
        y = self.conv2(y)
        if self.stride > 1:
            x = self.shortcut(x)
        y = y + x
        return y


class PiDiNet(nn.Module):
    def __init__(self, inplane, pdcs, dil=None, sa=False, convert=False):
        super(PiDiNet, self).__init__()
        self.sa = sa
        if dil is not None:
            assert isinstance(dil, int), "dil should be an int"
        self.dil = dil

        self.fuseplanes = []
        self.inplane = inplane

        if convert:
            if pdcs[0] == "rd":
                init_kernel_size = 5
                init_padding = 2
            else:
                init_kernel_size = 3
                init_padding = 1
            self.init_block = nn.Conv2d(
                3,
                self.inplane,
                kernel_size=init_kernel_size,
                padding=init_padding,
                bias=False,
            )
            block_class = PDCBlock_converted
        else:
            self.init_block = Conv2d(pdcs[0], 3, self.inplane, kernel_size=3, padding=1)
            block_class = PDCBlock

        self.block1_1 = block_class(pdcs[1], self.inplane, self.inplane)
        self.block1_2 = block_class(pdcs[2], self.inplane, self.inplane)
        self.block1_3 = block_class(pdcs[3], self.inplane, self.inplane)
        self.fuseplanes.append(self.inplane)  # C

        inplane = self.inplane
        self.inplane = self.inplane * 2
        self.block2_1 = block_class(pdcs[4], inplane, self.inplane, stride=2)
        self.block2_2 = block_class(pdcs[5], self.inplane, self.inplane)
        self.block2_3 = block_class(pdcs[6], self.inplane, self.inplane)
        self.block2_4 = block_class(pdcs[7], self.inplane, self.inplane)
        self.fuseplanes.append(self.inplane)  # 2C

        inplane = self.inplane
        self.inplane = self.inplane * 2
        self.block3_1 = block_class(pdcs[8], inplane, self.inplane, stride=2)
        self.block3_2 = block_class(pdcs[9], self.inplane, self.inplane)
        self.block3_3 = block_class(pdcs[10], self.inplane, self.inplane)
        self.block3_4 = block_class(pdcs[11], self.inplane, self.inplane)
        self.fuseplanes.append(self.inplane)  # 4C

        self.block4_1 = block_class(pdcs[12], self.inplane, self.inplane, stride=2)
        self.block4_2 = block_class(pdcs[13], self.inplane, self.inplane)
        self.block4_3 = block_class(pdcs[14], self.inplane, self.inplane)
        self.block4_4 = block_class(pdcs[15], self.inplane, self.inplane)
        self.fuseplanes.append(self.inplane)  # 4C

        self.conv_reduces = nn.ModuleList()
        if self.sa and self.dil is not None:
            self.attentions = nn.ModuleList()
            self.dilations = nn.ModuleList()
            for i in range(4):
                self.dilations.append(CDCM(self.fuseplanes[i], self.dil))
                self.attentions.append(CSAM(self.dil))
                self.conv_reduces.append(MapReduce(self.dil))
        elif self.sa:
            self.attentions = nn.ModuleList()
            for i in range(4):
                self.attentions.append(CSAM(self.fuseplanes[i]))
                self.conv_reduces.append(MapReduce(self.fuseplanes[i]))
        elif self.dil is not None:
            self.dilations = nn.ModuleList()
            for i in range(4):
                self.dilations.append(CDCM(self.fuseplanes[i], self.dil))
                self.conv_reduces.append(MapReduce(self.dil))
        else:
            for i in range(4):
                self.conv_reduces.append(MapReduce(self.fuseplanes[i]))

        self.classifier = nn.Conv2d(4, 1, kernel_size=1)  # has bias
        nn.init.constant_(self.classifier.weight, 0.25)
        nn.init.constant_(self.classifier.bias, 0)

    def get_weights(self):
        conv_weights = []
        bn_weights = []
        relu_weights = []
        for pname, p in self.named_parameters():
            if "bn" in pname:
                bn_weights.append(p)
            elif "relu" in pname:
                relu_weights.append(p)
            else:
                conv_weights.append(p)

        return conv_weights, bn_weights, relu_weights

    def forward(self, x):
        H, W = x.size()[2:]

        x = self.init_block(x)

        x1 = self.block1_1(x)
        x1 = self.block1_2(x1)
        x1 = self.block1_3(x1)

        x2 = self.block2_1(x1)
        x2 = self.block2_2(x2)
        x2 = self.block2_3(x2)
        x2 = self.block2_4(x2)

        x3 = self.block3_1(x2)
        x3 = self.block3_2(x3)
        x3 = self.block3_3(x3)
        x3 = self.block3_4(x3)

        x4 = self.block4_1(x3)
        x4 = self.block4_2(x4)
        x4 = self.block4_3(x4)
        x4 = self.block4_4(x4)

        x_fuses = []
        if self.sa and self.dil is not None:
            for i, xi in enumerate([x1, x2, x3, x4]):
                x_fuses.append(self.attentions[i](self.dilations[i](xi)))
        elif self.sa:
            for i, xi in enumerate([x1, x2, x3, x4]):
                x_fuses.append(self.attentions[i](xi))
        elif self.dil is not None:
            for i, xi in enumerate([x1, x2, x3, x4]):
                x_fuses.append(self.dilations[i](xi))
        else:
            x_fuses = [x1, x2, x3, x4]

        e1 = self.conv_reduces[0](x_fuses[0])
        e1 = F.interpolate(e1, (H, W), mode="bilinear", align_corners=False)

        e2 = self.conv_reduces[1](x_fuses[1])
        e2 = F.interpolate(e2, (H, W), mode="bilinear", align_corners=False)

        e3 = self.conv_reduces[2](x_fuses[2])
        e3 = F.interpolate(e3, (H, W), mode="bilinear", align_corners=False)

        e4 = self.conv_reduces[3](x_fuses[3])
        e4 = F.interpolate(e4, (H, W), mode="bilinear", align_corners=False)

        outputs = [e1, e2, e3, e4]

        output = self.classifier(torch.cat(outputs, dim=1))
        if not self.training:
            return torch.sigmoid(output)

        outputs.append(output)
        outputs = [torch.sigmoid(r) for r in outputs]
        return outputs


# Configuration for carv4 (the main model variant)
CARV4_CONFIG = {
    "layer0": "cd",
    "layer1": "ad",
    "layer2": "rd",
    "layer3": "cv",
    "layer4": "cd",
    "layer5": "ad",
    "layer6": "rd",
    "layer7": "cv",
    "layer8": "cd",
    "layer9": "ad",
    "layer10": "rd",
    "layer11": "cv",
    "layer12": "cd",
    "layer13": "ad",
    "layer14": "rd",
    "layer15": "cv",
}


def config_model(model_config):
    """Configure model with PDC operations"""
    pdcs = []
    for i in range(16):
        layer_name = "layer%d" % i
        op = model_config[layer_name]
        pdcs.append(createConvFunc(op))
    return pdcs


def config_model_converted(model_config):
    """Configure converted model with operation names"""
    pdcs = []
    for i in range(16):
        layer_name = "layer%d" % i
        op = model_config[layer_name]
        pdcs.append(op)
    return pdcs


class PiDiNetModel:
    """
    PiDiNet Edge Detection Model

    High-performance edge detection using Pixel Difference Networks.
    Optimized for client-side inference with <30ms target latency.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "auto",
        use_converted: bool = True,
        use_sa: bool = True,
        use_dil: bool = True,
        dil_channels: int = 24,
        model_variant: str = "standard",  # Production default: highest quality
    ):
        """
        Initialize PiDiNet model

        Args:
            model_path: Path to pre-trained model weights
            device: Device to run inference on ('cpu', 'cuda', 'auto')
            use_converted: Use converted model for faster inference
            use_sa: Use spatial attention
            use_dil: Use dilated convolutions
            dil_channels: Number of dilation channels (deprecated, auto-set based on variant)
            model_variant: Model variant ('tiny', 'small', 'standard')
        """
        self.device = self._setup_device(device)
        self.use_converted = use_converted
        self.use_sa = use_sa
        self.use_dil = use_dil
        self.model_variant = model_variant

        # Model configuration
        self.input_size = (512, 512)  # Standard input size
        self.mean = [0.485, 0.456, 0.406]  # ImageNet normalization
        self.std = [0.229, 0.224, 0.225]

        # Initialize model
        self.model = self._build_model()

        # Load pre-trained weights if provided
        if model_path and os.path.exists(model_path):
            self.load_weights(model_path)
        else:
            print(f"Warning: Model weights not found at {model_path}")
            print("Using randomly initialized weights - performance will be poor!")

        self.model.eval()

        # Performance tracking
        self.inference_times = []

    def _setup_device(self, device: str) -> torch.device:
        """Setup computation device"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"  # Apple Silicon
            else:
                device = "cpu"

        torch_device = torch.device(device)
        print(f"Using device: {torch_device}")
        return torch_device

    def _build_model(self) -> PiDiNet:
        """Build PiDiNet model architecture"""
        # Configure PDC operations
        if self.use_converted:
            pdcs = config_model_converted(CARV4_CONFIG)
        else:
            pdcs = config_model(CARV4_CONFIG)

        # Set correct channel configuration based on model variant
        if hasattr(self, "model_variant"):
            variant = self.model_variant
        else:
            variant = "standard"  # Default

        if variant == "tiny":
            inplane = 20
            dil_channels = 8 if self.use_dil else None
        elif variant == "small":
            inplane = 30
            dil_channels = 12 if self.use_dil else None
        else:  # standard
            inplane = 60
            dil_channels = 24 if self.use_dil else None

        # Create model
        model = PiDiNet(
            inplane=inplane,
            pdcs=pdcs,
            dil=dil_channels,
            sa=self.use_sa,
            convert=self.use_converted,
        )

        return model.to(self.device)

    def load_weights(self, model_path: str):
        """Load pre-trained model weights"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)

            # Handle different checkpoint formats
            if "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint

            # Remove 'module.' prefix if present (from DataParallel)
            if any(key.startswith("module.") for key in state_dict.keys()):
                state_dict = {key[7:]: value for key, value in state_dict.items()}

            self.model.load_state_dict(state_dict, strict=False)
            print(f"Successfully loaded weights from {model_path}")

        except Exception as e:
            print(f"Error loading weights: {e}")
            raise

    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess input image for PiDiNet inference

        Args:
            image: Input image as numpy array (H, W, 3) in BGR format

        Returns:
            Preprocessed tensor ready for inference
        """
        # Convert BGR to RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize to model input size
        image = cv2.resize(image, self.input_size, interpolation=cv2.INTER_LINEAR)

        # Normalize to [0, 1]
        image = image.astype(np.float32) / 255.0

        # Apply ImageNet normalization
        for i in range(3):
            image[:, :, i] = (image[:, :, i] - self.mean[i]) / self.std[i]

        # Convert to tensor and add batch dimension
        tensor = torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0)

        return tensor.to(self.device)

    def postprocess(
        self, output: torch.Tensor, original_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Postprocess model output to edge map

        Args:
            output: Model output tensor
            original_shape: Original image shape (H, W)

        Returns:
            Edge map as numpy array (H, W) with values in [0, 255]
        """
        # Convert to numpy and remove batch dimension
        edge_map = output.squeeze().cpu().numpy()

        # Resize to original shape
        if edge_map.shape != original_shape:
            edge_map = cv2.resize(
                edge_map,
                (original_shape[1], original_shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )

        # Convert to uint8
        edge_map = (edge_map * 255).astype(np.uint8)

        return edge_map

    def predict(self, image: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
        """
        Perform edge detection on input image

        Args:
            image: Input image as numpy array
            threshold: Edge threshold (0.0 to 1.0)

        Returns:
            Dictionary containing edge map and metadata
        """
        start_time = time.time()

        original_shape = image.shape[:2]

        # Preprocess
        input_tensor = self.preprocess(image)

        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)

            # Handle different output formats
            if isinstance(output, list):
                output = output[-1]  # Use final output

        # Postprocess
        edge_map = self.postprocess(output, original_shape)

        # Apply threshold
        if threshold > 0:
            edge_map_thresh = (edge_map > int(threshold * 255)).astype(np.uint8) * 255
        else:
            edge_map_thresh = edge_map

        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        self.inference_times.append(inference_time)

        return {
            "edge_map": edge_map,
            "edge_map_thresh": edge_map_thresh,
            "inference_time_ms": inference_time,
            "threshold": threshold,
            "input_shape": original_shape,
            "model_config": {
                "use_converted": self.use_converted,
                "use_sa": self.use_sa,
                "use_dil": self.use_dil,
                "device": str(self.device),
            },
        }

    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
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

    def benchmark(self, image: np.ndarray, num_runs: int = 100) -> Dict[str, Any]:
        """
        Benchmark model performance

        Args:
            image: Test image
            num_runs: Number of benchmark runs

        Returns:
            Benchmark results
        """
        print(f"Running benchmark with {num_runs} iterations...")

        # Warm up
        for _ in range(5):
            self.predict(image)

        # Clear previous times
        self.inference_times.clear()

        # Benchmark runs
        for i in range(num_runs):
            self.predict(image)
            if (i + 1) % 20 == 0:
                print(f"Completed {i + 1}/{num_runs} runs")

        stats = self.get_performance_stats()

        # Check performance targets
        target_time_ms = 30.0  # Client-side target
        meets_target = stats["mean_time_ms"] <= target_time_ms

        print(f"\nBenchmark Results:")
        print(f"Mean inference time: {stats['mean_time_ms']:.2f}ms")
        print(
            f"Target: {target_time_ms}ms - {'✅ PASS' if meets_target else '❌ FAIL'}"
        )

        return {
            **stats,
            "target_time_ms": target_time_ms,
            "meets_target": meets_target,
            "num_runs": num_runs,
        }
