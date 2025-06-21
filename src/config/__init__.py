"""
ArtiTech Stage 1 Configuration Module
"""

from .system_defaults import (
    EDGE_DETECTION_DEFAULTS,
    MODEL_VARIANTS,
    THRESHOLD_GUIDE,
    ARCHITECTURE_CONFIG,
    PRODUCTION_CONFIG,
    get_default_config,
    get_model_path,
    validate_config,
)

__all__ = [
    "EDGE_DETECTION_DEFAULTS",
    "MODEL_VARIANTS",
    "THRESHOLD_GUIDE",
    "ARCHITECTURE_CONFIG",
    "PRODUCTION_CONFIG",
    "get_default_config",
    "get_model_path",
    "validate_config",
]
