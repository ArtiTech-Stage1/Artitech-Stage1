"""
ArtiTech Stage 1 - Saliency Processing Module
Enhanced therapeutic edge detection with saliency-guided ROI processing
"""

from .roi_processor import DualROIProcessor
from .concept_attention import ConceptAttentionModel

__all__ = [
    "DualROIProcessor",
    "ConceptAttentionModel",
]

__version__ = "2.3.0"
