"""
Emotion Configuration System for Phase 2 Saliency Integration
Provides emotion-to-concept mapping, therapeutic goals, and processing parameters
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class ROIStrategy(Enum):
    """ROI processing strategies"""

    SEMANTIC_PRIORITY = "semantic_priority"  # Prioritize emotional concepts
    DENSITY_PRIORITY = "density_priority"  # Prioritize edge complexity
    BALANCED = "balanced"  # Equal weight to both
    ADAPTIVE = "adaptive"  # Dynamic based on image content


class MaskingStrategy(Enum):
    """Therapeutic masking approaches"""

    INVERT = "invert"  # Remove salient areas completely
    GRADIENT = "gradient"  # Gradual fade of salient areas
    SOFT_MASK = "soft_mask"  # Partial transparency
    SELECTIVE = "selective"  # Remove specific concept types


class TherapeuticGoal(Enum):
    """Therapeutic objectives for different emotions"""

    EMOTIONAL_EXPRESSION = "emotional_expression"
    POSITIVE_CREATION = "positive_creation"
    ANXIETY_REDUCTION = "anxiety_reduction"
    SELF_REFLECTION = "self_reflection"
    SOCIAL_CONNECTION = "social_connection"
    EMPOWERMENT = "empowerment"


@dataclass
class EmotionConfig:
    """Configuration for a specific emotion"""

    name: str
    concepts: List[str]
    saliency_threshold: float
    roi_strategy: ROIStrategy
    masking_strategy: MaskingStrategy
    therapeutic_goal: TherapeuticGoal
    intensity_multiplier: float = 1.0
    concept_weights: Optional[Dict[str, float]] = None
    fallback_concepts: Optional[List[str]] = None
    description: Optional[str] = None


# Core emotion configurations
EMOTION_CONFIGS: Dict[str, EmotionConfig] = {
    "sadness": EmotionConfig(
        name="sadness",
        concepts=["face", "figure", "eyes", "hands", "person", "portrait"],
        saliency_threshold=0.35,
        roi_strategy=ROIStrategy.SEMANTIC_PRIORITY,
        masking_strategy=MaskingStrategy.SOFT_MASK,
        therapeutic_goal=TherapeuticGoal.EMOTIONAL_EXPRESSION,
        intensity_multiplier=1.2,
        concept_weights={"face": 1.5, "eyes": 1.3, "hands": 1.1},
        fallback_concepts=["silhouette", "shadow"],
        description="Focus on human elements for emotional expression therapy",
    ),
    "joy": EmotionConfig(
        name="joy",
        concepts=["sun", "sky", "flowers", "children", "celebration", "bright colors"],
        saliency_threshold=0.45,
        roi_strategy=ROIStrategy.BALANCED,
        masking_strategy=MaskingStrategy.GRADIENT,
        therapeutic_goal=TherapeuticGoal.POSITIVE_CREATION,
        intensity_multiplier=0.9,
        concept_weights={"sun": 1.4, "flowers": 1.2, "bright colors": 1.1},
        fallback_concepts=["light", "open space"],
        description="Emphasize positive elements for uplifting therapy",
    ),
    "anxiety": EmotionConfig(
        name="anxiety",
        concepts=["crowds", "confined spaces", "sharp objects", "clutter", "darkness"],
        saliency_threshold=0.25,
        roi_strategy=ROIStrategy.SEMANTIC_PRIORITY,
        masking_strategy=MaskingStrategy.INVERT,
        therapeutic_goal=TherapeuticGoal.ANXIETY_REDUCTION,
        intensity_multiplier=1.1,
        concept_weights={"crowds": 1.3, "confined spaces": 1.2, "sharp objects": 1.4},
        fallback_concepts=["busy patterns", "angular shapes"],
        description="Remove anxiety-triggering elements for calming therapy",
    ),
    "loneliness": EmotionConfig(
        name="loneliness",
        concepts=[
            "single person",
            "empty spaces",
            "solitary figures",
            "windows",
            "distance",
        ],
        saliency_threshold=0.4,
        roi_strategy=ROIStrategy.SEMANTIC_PRIORITY,
        masking_strategy=MaskingStrategy.SELECTIVE,
        therapeutic_goal=TherapeuticGoal.SOCIAL_CONNECTION,
        intensity_multiplier=1.0,
        concept_weights={"single person": 1.3, "empty spaces": 1.1, "windows": 1.2},
        fallback_concepts=["isolation", "separation"],
        description="Highlight connection opportunities for social therapy",
    ),
    "anger": EmotionConfig(
        name="anger",
        concepts=[
            "clenched fists",
            "aggressive postures",
            "red colors",
            "sharp angles",
            "confrontation",
        ],
        saliency_threshold=0.3,
        roi_strategy=ROIStrategy.ADAPTIVE,
        masking_strategy=MaskingStrategy.GRADIENT,
        therapeutic_goal=TherapeuticGoal.EMOTIONAL_EXPRESSION,
        intensity_multiplier=1.1,
        concept_weights={
            "clenched fists": 1.4,
            "aggressive postures": 1.2,
            "red colors": 1.0,
        },
        fallback_concepts=["tension", "intensity"],
        description="Channel anger constructively through controlled expression",
    ),
    "fear": EmotionConfig(
        name="fear",
        concepts=[
            "shadows",
            "darkness",
            "hiding figures",
            "threatening objects",
            "enclosed spaces",
        ],
        saliency_threshold=0.2,
        roi_strategy=ROIStrategy.SEMANTIC_PRIORITY,
        masking_strategy=MaskingStrategy.INVERT,
        therapeutic_goal=TherapeuticGoal.EMPOWERMENT,
        intensity_multiplier=1.3,
        concept_weights={"shadows": 1.2, "darkness": 1.1, "threatening objects": 1.4},
        fallback_concepts=["unknown", "mystery"],
        description="Remove fear elements to build confidence and control",
    ),
}

# Composite emotion configurations
COMPOSITE_EMOTIONS: Dict[str, Dict[str, float]] = {
    "melancholy": {"sadness": 0.7, "loneliness": 0.3},
    "overwhelmed": {"anxiety": 0.6, "fear": 0.4},
    "frustrated": {"anger": 0.5, "sadness": 0.3, "anxiety": 0.2},
    "hopeful": {
        "joy": 0.8,
        "loneliness": -0.3,
    },  # Negative weight reduces loneliness concepts
    "content": {"joy": 0.6, "sadness": -0.2, "anxiety": -0.2},
    "excited": {"joy": 0.9, "anxiety": 0.1},  # Positive anxiety for excitement
}

# Intensity modifiers for emotion strength
INTENSITY_MODIFIERS = {"mild": 0.7, "moderate": 1.0, "strong": 1.3, "intense": 1.6}


class EmotionConfigManager:
    """Manages emotion configurations and provides lookup functionality"""

    def __init__(self, config_path: Optional[str] = None):
        self.configs = EMOTION_CONFIGS.copy()
        self.composite_emotions = COMPOSITE_EMOTIONS.copy()
        self.concept_cache = {}

        if config_path:
            self.load_custom_config(config_path)

    def get_emotion_config(
        self, emotion: str, intensity: str = "moderate"
    ) -> EmotionConfig:
        """Get configuration for a specific emotion with intensity modifier"""
        if emotion in self.configs:
            config = self.configs[emotion]
            if intensity in INTENSITY_MODIFIERS:
                # Create modified config with intensity adjustment
                modified_config = EmotionConfig(
                    name=f"{emotion}_{intensity}",
                    concepts=config.concepts,
                    saliency_threshold=config.saliency_threshold
                    * INTENSITY_MODIFIERS[intensity],
                    roi_strategy=config.roi_strategy,
                    masking_strategy=config.masking_strategy,
                    therapeutic_goal=config.therapeutic_goal,
                    intensity_multiplier=config.intensity_multiplier
                    * INTENSITY_MODIFIERS[intensity],
                    concept_weights=config.concept_weights,
                    fallback_concepts=config.fallback_concepts,
                    description=config.description,
                )
                return modified_config
            return config
        else:
            raise ValueError(f"Unknown emotion: {emotion}")

    def get_composite_emotion_config(
        self, emotion: str, intensity: str = "moderate"
    ) -> EmotionConfig:
        """Get configuration for composite emotions"""
        if emotion not in self.composite_emotions:
            raise ValueError(f"Unknown composite emotion: {emotion}")

        # Blend configurations based on weights
        blend_weights = self.composite_emotions[emotion]

        # Start with the primary emotion (highest weight)
        primary_emotion = max(blend_weights.keys(), key=lambda x: abs(blend_weights[x]))
        base_config = self.get_emotion_config(primary_emotion, intensity)

        # Blend concepts from all contributing emotions
        blended_concepts = []
        blended_concept_weights = {}

        for emotion_name, weight in blend_weights.items():
            if weight > 0:  # Only include positive weights
                emotion_config = self.get_emotion_config(emotion_name, intensity)
                # Add concepts with weight adjustment
                for concept in emotion_config.concepts:
                    if concept not in blended_concepts:
                        blended_concepts.append(concept)
                        blended_concept_weights[concept] = weight
                    else:
                        blended_concept_weights[concept] += weight

        # Create blended configuration
        blended_config = EmotionConfig(
            name=f"{emotion}_{intensity}",
            concepts=blended_concepts,
            saliency_threshold=base_config.saliency_threshold,
            roi_strategy=base_config.roi_strategy,
            masking_strategy=base_config.masking_strategy,
            therapeutic_goal=base_config.therapeutic_goal,
            intensity_multiplier=base_config.intensity_multiplier,
            concept_weights=blended_concept_weights,
            fallback_concepts=base_config.fallback_concepts,
            description=f"Composite emotion blending: {blend_weights}",
        )

        return blended_config

    def get_concepts_for_emotion(
        self, emotion: str, intensity: str = "moderate"
    ) -> List[str]:
        """Get visual concepts for a given emotion"""
        cache_key = f"{emotion}_{intensity}"
        if cache_key in self.concept_cache:
            return self.concept_cache[cache_key]

        if emotion in self.configs:
            config = self.get_emotion_config(emotion, intensity)
        elif emotion in self.composite_emotions:
            config = self.get_composite_emotion_config(emotion, intensity)
        else:
            raise ValueError(f"Unknown emotion: {emotion}")

        concepts = config.concepts
        self.concept_cache[cache_key] = concepts
        return concepts

    def get_concept_weights(
        self, emotion: str, intensity: str = "moderate"
    ) -> Dict[str, float]:
        """Get concept weights for weighted saliency detection"""
        if emotion in self.configs:
            config = self.get_emotion_config(emotion, intensity)
        elif emotion in self.composite_emotions:
            config = self.get_composite_emotion_config(emotion, intensity)
        else:
            raise ValueError(f"Unknown emotion: {emotion}")

        return config.concept_weights or {}

    def validate_emotion(self, emotion: str) -> bool:
        """Validate if an emotion is supported"""
        return emotion in self.configs or emotion in self.composite_emotions

    def list_available_emotions(self) -> List[str]:
        """List all available emotions"""
        return list(self.configs.keys()) + list(self.composite_emotions.keys())

    def load_custom_config(self, config_path: str):
        """Load custom emotion configurations from JSON file"""
        try:
            with open(config_path, "r") as f:
                custom_configs = json.load(f)

            for emotion_name, config_data in custom_configs.items():
                # Convert JSON to EmotionConfig
                config = EmotionConfig(
                    name=emotion_name,
                    concepts=config_data["concepts"],
                    saliency_threshold=config_data["saliency_threshold"],
                    roi_strategy=ROIStrategy(config_data["roi_strategy"]),
                    masking_strategy=MaskingStrategy(config_data["masking_strategy"]),
                    therapeutic_goal=TherapeuticGoal(config_data["therapeutic_goal"]),
                    intensity_multiplier=config_data.get("intensity_multiplier", 1.0),
                    concept_weights=config_data.get("concept_weights"),
                    fallback_concepts=config_data.get("fallback_concepts"),
                    description=config_data.get("description"),
                )
                self.configs[emotion_name] = config

        except Exception as e:
            print(f"Warning: Could not load custom config {config_path}: {e}")

    def save_config(self, config_path: str):
        """Save current configuration to JSON file"""
        config_data = {}
        for emotion_name, config in self.configs.items():
            config_data[emotion_name] = {
                "concepts": config.concepts,
                "saliency_threshold": config.saliency_threshold,
                "roi_strategy": config.roi_strategy.value,
                "masking_strategy": config.masking_strategy.value,
                "therapeutic_goal": config.therapeutic_goal.value,
                "intensity_multiplier": config.intensity_multiplier,
                "concept_weights": config.concept_weights,
                "fallback_concepts": config.fallback_concepts,
                "description": config.description,
            }

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)


# Global emotion config manager instance
emotion_config_manager = EmotionConfigManager()


# Convenience functions
def get_concepts_for_emotion(emotion: str, intensity: str = "moderate") -> List[str]:
    """Convenience function to get concepts for an emotion"""
    return emotion_config_manager.get_concepts_for_emotion(emotion, intensity)


def get_emotion_config(emotion: str, intensity: str = "moderate") -> EmotionConfig:
    """Convenience function to get full emotion configuration"""
    return emotion_config_manager.get_emotion_config(emotion, intensity)


def validate_emotion(emotion: str) -> bool:
    """Convenience function to validate emotion"""
    return emotion_config_manager.validate_emotion(emotion)


def list_available_emotions() -> List[str]:
    """Convenience function to list available emotions"""
    return emotion_config_manager.list_available_emotions()
