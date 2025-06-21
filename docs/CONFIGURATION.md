# Configuration Guide
**ArtiTech Stage 1 - Settings & Customization**

## 🎯 **Production Defaults - UPDATED**

### Current Configuration
```json
{
  "model_type": "pidinet",
  "model_variant": "standard",
  "threshold": 0.5,
  "use_sa": true,
  "use_dil": true,
  "device": "auto",
  "saliency_enabled": false,
  "emotion_mode": "disabled",
  "saliency_threshold": 0.4,
  "default_emotion": "neutral"
}
```

### Why These Defaults?
- **PiDiNet-Standard**: Highest quality for professional art applications
- **Threshold 0.5**: Optimal balance between detail and noise
- **Spatial Attention**: Enhanced edge detection accuracy
- **Dilated Convolutions**: Better context understanding
- **Auto Device**: Optimal performance on available hardware
- **Saliency Disabled**: ✨ **NEW** - Optional therapeutic enhancement
- **Emotion Mode**: ✨ **NEW** - Enables emotion-guided partial outlines

## 🎨 **Emotion-Based Configuration** ✨ **NEW SECTION**

### Emotion Settings
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **saliency_enabled** | false | boolean | Enable ConceptAttention saliency |
| **emotion_mode** | "disabled" | disabled/basic/advanced | Emotion processing level |
| **saliency_threshold** | 0.4 | 0.1-0.7 | Emotion region sensitivity |
| **mask_strategy** | "hide_salient" | hide_salient/highlight_salient | Masking approach |
| **concept_override** | null | string | Manual concept prompt |

### Emotion Prompt Configuration
```python
# src/config/emotion_presets.py
EMOTION_CONCEPT_MAP = {
    "sadness": {
        "primary_concepts": ["face", "figure"],
        "secondary_concepts": ["eyes", "expression"],
        "threshold": 0.35,
        "mask_strength": 0.8
    },
    "joy": {
        "primary_concepts": ["sun", "sky"],
        "secondary_concepts": ["flowers", "bright_objects"],
        "threshold": 0.45,
        "mask_strength": 0.6
    },
    "anxiety": {
        "primary_concepts": ["hand", "gesture"],
        "secondary_concepts": ["body", "tension"],
        "threshold": 0.3,
        "mask_strength": 0.9
    },
    "loneliness": {
        "primary_concepts": ["window", "silhouette"],
        "secondary_concepts": ["distance", "empty_space"],
        "threshold": 0.4,
        "mask_strength": 0.7
    }
}
```

### Therapeutic Configuration Examples
```bash
# Enable basic emotion-guided outlines
python -m src.cli.edge_infer --input artwork.jpg --emotion sadness --enable-saliency

# Advanced therapeutic mode with custom threshold
python -m src.cli.edge_infer --input artwork.jpg --emotion anxiety --saliency-threshold 0.3

# Manual concept override for specific therapy goals
python -m src.cli.edge_infer --input artwork.jpg --emotion joy --concept-override "smile,eyes"
```

## 🔧 **Model Variants - UPDATED**

### Variant Comparison
| Variant | Channels | Quality | Speed | Memory | Saliency Support | Best For |
|---------|----------|---------|-------|--------|------------------|----------|
| **tiny** | 20 | Good | Fastest | 1GB | Limited | Mobile, real-time |
| **small** | 30 | Very Good | Fast | 1.5GB | Basic | Balanced apps |
| **standard** | 60 | **Excellent** | Moderate | 2GB | **Full** | **Production + Therapy** |

### Usage Examples - EXTENDED
```bash
# Production default (highest quality + full saliency)
python -m src.cli.edge_infer --input artwork.jpg --emotion sadness

# Fast processing (limited saliency features)
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny --emotion joy

# Balanced option (basic saliency support)
python -m src.cli.edge_infer --input artwork.jpg --model-variant small --emotion anxiety
```

## 🎨 **Threshold Configuration - UPDATED**

### Threshold Guide
| Value | Description | Edge Detail | Noise Level | Emotion Sensitivity | Best For |
|-------|-------------|-------------|-------------|-------------------|----------|
| **0.1-0.3** | High sensitivity | Maximum detail | Higher noise | Very High | Fine art, detailed therapy |
| **0.4-0.6** | **Balanced** | **Good detail** | **Low noise** | **Moderate** | **General + Therapeutic** |
| **0.7-0.9** | Low sensitivity | Clean edges | Minimal noise | Low | High contrast, simple therapy |

### Emotion-Adaptive Threshold Examples ✨ **NEW**
```bash
# Sadness - high sensitivity for facial features
python -m src.cli.edge_infer --input artwork.jpg --emotion sadness --threshold 0.3

# Joy - moderate sensitivity for general features
python -m src.cli.edge_infer --input artwork.jpg --emotion joy --threshold 0.5

# Anxiety - high sensitivity for gesture detection
python -m src.cli.edge_infer --input artwork.jpg --emotion anxiety --threshold 0.25
```

## 💻 **Device Configuration - UPDATED**

### Device Options
| Device | Description | Performance | Saliency Support | Compatibility |
|--------|-------------|-------------|------------------|---------------|
| **auto** | **Auto-detect best** | **Optimal** | **Full** | **Universal** |
| **mps** | Apple Silicon GPU | Excellent | Full | Mac M1/M2/M3/M4 |
| **cuda** | NVIDIA GPU | Excellent | Full | NVIDIA GPUs |
| **cpu** | CPU processing | Good | Limited | Universal fallback |

### Saliency Device Requirements ✨ **NEW**
```bash
# Optimal saliency performance (GPU recommended)
python -m src.cli.edge_infer --input artwork.jpg --device cuda --emotion sadness

# Apple Silicon optimization
python -m src.cli.edge_infer --input artwork.jpg --device mps --emotion joy

# CPU fallback (slower saliency processing)
python -m src.cli.edge_infer --input artwork.jpg --device cpu --emotion anxiety --fast-saliency
```

## ⚙️ **Advanced Configuration - UPDATED**

### Saliency Configuration System ✨ **NEW**
```bash
# View saliency configuration
python -c "from src.config import get_saliency_config; import json; print(json.dumps(get_saliency_config(), indent=2))"

# Validate emotion mappings
python -c "from src.config.emotion_presets import validate_emotion_config; print(validate_emotion_config())"

# Test concept mapping for emotion
python -c "from src.config.emotion_presets import get_concepts_for_emotion; print(get_concepts_for_emotion('sadness'))"
```

### Custom Emotion Configuration
Create `custom_emotion_config.py`:
```python
from src.config.emotion_presets import EMOTION_CONCEPT_MAP

# Custom therapeutic configuration
THERAPY_CONFIG = {
    "custom_emotion": {
        "primary_concepts": ["specific_feature"],
        "threshold": 0.35,
        "mask_strength": 0.75,
        "therapy_goal": "encourage_expression"
    }
}

# Merge with defaults
EXTENDED_EMOTION_MAP = {**EMOTION_CONCEPT_MAP, **THERAPY_CONFIG}
```

## 🚀 **Performance Optimization - UPDATED**

### Saliency Performance Optimization ✨ **NEW**
```bash
# Fast saliency mode (reduced accuracy for speed)
python -m src.cli.edge_infer --input artwork.jpg --emotion sadness --fast-saliency

# Quality saliency mode (slower but more accurate)
python -m src.cli.edge_infer --input artwork.jpg --emotion joy --quality-saliency

# Batch saliency processing (future)
python -m src.cli.edge_infer --input "*.jpg" --emotion anxiety --batch-saliency
```

### Memory Optimization with Saliency
```bash
# Low memory saliency usage
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny --emotion sadness --low-memory

# Balanced memory + saliency
python -m src.cli.edge_infer --input artwork.jpg --model-variant small --emotion joy --optimize-memory
```

## 📊 **Benchmarking Configuration - UPDATED**

### Benchmark Options with Saliency ✨ **NEW**
```bash
# Quick benchmark with saliency (10 runs)
python -m src.cli.edge_infer --input artwork.jpg --emotion sadness --benchmark

# Detailed saliency benchmark (50 runs)
python -m src.cli.edge_infer --input artwork.jpg --emotion joy --benchmark --num-runs 50 --include-saliency

# Comprehensive benchmark (100 runs, all emotions)
python -m src.cli.edge_infer --input artwork.jpg --benchmark-all-emotions --num-runs 100 --verbose
```

## 🎨 **Therapeutic Art Style Presets** ✨ **NEW SECTION**

### Emotion-Based Configurations by Art Style

**Therapeutic Portrait Processing (Sadness/Grief)**
```bash
python -m src.cli.edge_infer \
    --input portrait.jpg \
    --model-variant standard \
    --emotion sadness \
    --threshold 0.3 \
    --saliency-threshold 0.35 \
    --mask-strategy hide_salient \
    --device auto
```

**Uplifting Landscape Processing (Joy/Hope)**
```bash
python -m src.cli.edge_infer \
    --input landscape.jpg \
    --model-variant standard \
    --emotion joy \
    --threshold 0.5 \
    --saliency-threshold 0.45 \
    --concept-override "sun,sky,horizon" \
    --device auto
```

**Anxiety/Stress Relief Processing**
```bash
python -m src.cli.edge_infer \
    --input calming_scene.jpg \
    --model-variant small \
    --emotion anxiety \
    --threshold 0.25 \
    --saliency-threshold 0.3 \
    --mask-strategy hide_salient \
    --device auto
```

**Abstract Emotional Expression**
```bash
python -m src.cli.edge_infer \
    --input abstract_art.jpg \
    --model-variant standard \
    --emotion loneliness \
    --threshold 0.4 \
    --saliency-threshold 0.4 \
    --concept-override "empty_space,isolation" \
    --device auto
```

## 🔍 **Configuration Validation - UPDATED**

### Validate Saliency Settings ✨ **NEW**
```python
from src.config import validate_saliency_config
from src.config.emotion_presets import validate_emotion_config

config = {
    "edge_detection": {
        "model_variant": "standard",
        "threshold": 0.5,
        "device": "auto"
    },
    "saliency": {
        "enabled": true,
        "emotion": "sadness",
        "threshold": 0.4,
        "mask_strategy": "hide_salient"
    }
}

is_valid = validate_saliency_config(config)
emotion_valid = validate_emotion_config(config["saliency"]["emotion"])
print(f"Configuration valid: {is_valid}")
print(f"Emotion mapping valid: {emotion_valid}")
```

### Common Saliency Configuration Errors ✨ **NEW**
```bash
# Invalid emotion (not in predefined map)
--emotion happiness  # ❌ Error (should be "joy")

# Invalid saliency threshold (outside 0.0-1.0)
--saliency-threshold 1.5  # ❌ Error

# Invalid mask strategy
--mask-strategy show_all  # ❌ Error (should be hide_salient/highlight_salient)

# Saliency without emotion
--enable-saliency  # ❌ Error (requires --emotion parameter)
```

### Emotion Configuration Troubleshooting ✨ **NEW**
```bash
# Check available emotions
python -c "from src.config.emotion_presets import list_available_emotions; print(list_available_emotions())"

# Test emotion concept mapping
python -c "from src.edge_detection.emotion_mapper import EmotionMapper; mapper = EmotionMapper(); print(mapper.get_concepts_for_emotion('sadness'))"

# Validate concept prompt
python -c "from src.edge_detection.saliency_model import SaliencyModel; model = SaliencyModel(); print(model.validate_concept_prompt('face,eyes'))"
```

## 📝 **Configuration Best Practices**

### Production Deployment
1. **Use standard variant** for highest quality
2. **Keep threshold at 0.5** for balanced results
3. **Use auto device detection** for optimal performance
4. **Enable verbose logging** for monitoring
5. **Regular benchmarking** for performance tracking

### Development/Testing
1. **Use small variant** for faster iteration
2. **Adjust threshold** based on artwork type
3. **Force CPU** for consistent testing
4. **Save intermediate results** for debugging
5. **Use detailed benchmarking** for optimization

---

**Next**: See [Technical Details](TECHNICAL.md) for implementation specifics  
**Performance**: See [Performance Report](PERFORMANCE.md) for benchmark data 