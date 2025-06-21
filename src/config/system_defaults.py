"""
ArtiTech Stage 1 - System Configuration Defaults
Production-ready configuration for optimal quality and performance balance.

Author: ArtiTech Stage 1 Team
Date: December 2024
"""

# Edge Detection Model Configuration
EDGE_DETECTION_DEFAULTS = {
    # Primary model configuration
    "model_type": "pidinet",  # Primary edge detection model
    "model_variant": "standard",  # PiDiNet-Standard for highest quality
    "threshold": 0.5,  # Balanced edge detection threshold
    # Model parameters
    "use_sa": True,  # Spatial attention enabled
    "use_dil": True,  # Dilated convolutions enabled
    "use_converted": False,  # Use original model architecture
    # Performance targets
    "client_target_ms": 30.0,  # Client-side processing target
    "total_target_ms": 50.0,  # Total pipeline target
    # Device configuration
    "device": "auto",  # Auto-detect optimal device
    "fallback_device": "cpu",  # Fallback if GPU unavailable
}

# Model Variants Performance Profile
MODEL_VARIANTS = {
    "tiny": {
        "description": "Fastest variant with good quality",
        "typical_performance_ms": 40,
        "quality_level": "good",
        "recommended_for": "real-time applications, mobile deployment",
    },
    "small": {
        "description": "Balanced performance and quality",
        "typical_performance_ms": 53,
        "quality_level": "very good",
        "recommended_for": "balanced applications, web deployment",
    },
    "standard": {
        "description": "Highest quality variant (PRODUCTION DEFAULT)",
        "typical_performance_ms": 57,
        "quality_level": "excellent",
        "recommended_for": "production systems, highest quality output",
    },
}

# Threshold Configuration Guide
THRESHOLD_GUIDE = {
    0.3: "More detailed edges, captures fine textures and subtle features",
    0.5: "Balanced edge detection (PRODUCTION DEFAULT)",
    0.7: "Clean, strong edges only, filters out noise and weak edges",
}

# System Architecture Configuration
ARCHITECTURE_CONFIG = {
    "pipeline_type": "hybrid",  # PiDiNet + DDN hybrid approach
    "primary_model": "pidinet",  # Primary edge detection
    "secondary_model": "ddn",  # Secondary for fusion (future)
    "fallback_model": "canny",  # Fast fallback for performance issues
}

# Production Deployment Settings
PRODUCTION_CONFIG = {
    "model_variant": "standard",  # Highest quality for production
    "threshold": 0.5,  # Balanced threshold
    "enable_benchmarking": True,  # Performance monitoring
    "save_intermediate": False,  # Don't save intermediate results by default
    "verbose_logging": False,  # Minimal logging for production
}


def get_default_config():
    """Get the complete default configuration for ArtiTech Stage 1"""
    return {
        "edge_detection": EDGE_DETECTION_DEFAULTS,
        "model_variants": MODEL_VARIANTS,
        "threshold_guide": THRESHOLD_GUIDE,
        "architecture": ARCHITECTURE_CONFIG,
        "production": PRODUCTION_CONFIG,
    }


def get_model_path(variant: str = "standard") -> str:
    """Get the path to the specified model variant"""
    import os
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    model_dir = project_root / "models" / "pidinet"

    model_files = {
        "tiny": "table5_pidinet-tiny.pth",
        "small": "table5_pidinet-small.pth",
        "standard": "table5_pidinet.pth",
    }

    return str(model_dir / model_files.get(variant, model_files["standard"]))


def validate_config(config: dict) -> bool:
    """Validate system configuration"""
    required_keys = ["model_type", "model_variant", "threshold"]

    for key in required_keys:
        if key not in config.get("edge_detection", {}):
            return False

    # Validate threshold range
    threshold = config["edge_detection"].get("threshold", 0.5)
    if not 0.0 <= threshold <= 1.0:
        return False

    # Validate model variant
    variant = config["edge_detection"].get("model_variant", "standard")
    if variant not in MODEL_VARIANTS:
        return False

    return True
