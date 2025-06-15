# Configuration Guide
**ArtiTech Stage 1 - Settings & Customization**

## 🎯 **Production Defaults**

### Current Configuration
```json
{
  "model_type": "pidinet",
  "model_variant": "standard",
  "threshold": 0.5,
  "use_sa": true,
  "use_dil": true,
  "device": "auto"
}
```

### Why These Defaults?
- **PiDiNet-Standard**: Highest quality for professional art applications
- **Threshold 0.5**: Optimal balance between detail and noise
- **Spatial Attention**: Enhanced edge detection accuracy
- **Dilated Convolutions**: Better context understanding
- **Auto Device**: Optimal performance on available hardware

## 🔧 **Model Variants**

### Variant Comparison
| Variant | Channels | Quality | Speed | Memory | Best For |
|---------|----------|---------|-------|--------|----------|
| **tiny** | 20 | Good | Fastest | 1GB | Mobile, real-time |
| **small** | 30 | Very Good | Fast | 1.5GB | Balanced apps |
| **standard** | 60 | **Excellent** | Moderate | 2GB | **Production** |

### Usage Examples
```bash
# Production default (highest quality)
python -m src.cli.edge_infer --input artwork.jpg

# Fast processing
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny

# Balanced option
python -m src.cli.edge_infer --input artwork.jpg --model-variant small
```

## 🎨 **Threshold Configuration**

### Threshold Guide
| Value | Description | Edge Detail | Noise Level | Best For |
|-------|-------------|-------------|-------------|----------|
| **0.1-0.3** | High sensitivity | Maximum detail | Higher noise | Fine art, detailed illustrations |
| **0.4-0.6** | **Balanced** | **Good detail** | **Low noise** | **General purpose** |
| **0.7-0.9** | Low sensitivity | Clean edges | Minimal noise | High contrast, modern art |

### Threshold Examples
```bash
# Detailed edges (traditional art)
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.3

# Balanced (production default)
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.5

# Clean edges (modern art)
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.7
```

### Artwork-Specific Recommendations
```bash
# Classical paintings (portraits, landscapes)
--threshold 0.4

# Traditional Asian art (ink paintings, calligraphy)
--threshold 0.3

# Modern art (abstract, high contrast)
--threshold 0.7

# Photography-based art
--threshold 0.5
```

## 💻 **Device Configuration**

### Device Options
| Device | Description | Performance | Compatibility |
|--------|-------------|-------------|---------------|
| **auto** | **Auto-detect best** | **Optimal** | **Universal** |
| **mps** | Apple Silicon GPU | Excellent | Mac M1/M2/M3/M4 |
| **cuda** | NVIDIA GPU | Excellent | NVIDIA GPUs |
| **cpu** | CPU processing | Good | Universal fallback |

### Device Selection
```bash
# Auto-detect (recommended)
python -m src.cli.edge_infer --input artwork.jpg --device auto

# Force Apple Silicon GPU
python -m src.cli.edge_infer --input artwork.jpg --device mps

# Force NVIDIA GPU
python -m src.cli.edge_infer --input artwork.jpg --device cuda

# Force CPU (compatibility)
python -m src.cli.edge_infer --input artwork.jpg --device cpu
```

## ⚙️ **Advanced Configuration**

### Configuration System
```bash
# View current configuration
python -c "from src.config import get_default_config; import json; print(json.dumps(get_default_config(), indent=2))"

# Validate configuration
python -c "from src.config import validate_config, get_default_config; print(validate_config(get_default_config()))"

# Get model path for variant
python -c "from src.config import get_model_path; print(get_model_path('standard'))"
```

### Custom Configuration File
Create `custom_config.py`:
```python
from src.config import EDGE_DETECTION_DEFAULTS

# Custom configuration
CUSTOM_CONFIG = {
    **EDGE_DETECTION_DEFAULTS,
    "model_variant": "small",
    "threshold": 0.4,
    "device": "mps"
}
```

## 🚀 **Performance Optimization**

### Memory Optimization
```bash
# Low memory usage
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny

# Batch processing (future)
python -m src.cli.edge_infer --input "*.jpg" --model-variant small
```

### Speed Optimization
```bash
# Fastest processing
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny --threshold 0.7

# CPU optimization
python -m src.cli.edge_infer --input artwork.jpg --device cpu --model-variant small
```

### Quality Optimization
```bash
# Maximum quality
python -m src.cli.edge_infer --input artwork.jpg --model-variant standard --threshold 0.3

# Balanced quality/speed
python -m src.cli.edge_infer --input artwork.jpg --model-variant small --threshold 0.5
```

## 📊 **Benchmarking Configuration**

### Benchmark Options
```bash
# Quick benchmark (10 runs)
python -m src.cli.edge_infer --input artwork.jpg --benchmark

# Detailed benchmark (50 runs)
python -m src.cli.edge_infer --input artwork.jpg --benchmark --num-runs 50

# Comprehensive benchmark (100 runs)
python -m src.cli.edge_infer --input artwork.jpg --benchmark --num-runs 100 --verbose
```

### Performance Monitoring
```bash
# Monitor with verbose output
python -m src.cli.edge_infer --input artwork.jpg --verbose

# Save intermediate results
python -m src.cli.edge_infer --input artwork.jpg --save-intermediate
```

## 🎨 **Art Style Presets**

### Recommended Configurations by Art Style

**Classical Art (Oil Paintings, Portraits)**
```bash
python -m src.cli.edge_infer \
    --input classical_art.jpg \
    --model-variant standard \
    --threshold 0.4 \
    --device auto
```

**Traditional Asian Art (Ink Paintings, Calligraphy)**
```bash
python -m src.cli.edge_infer \
    --input asian_art.jpg \
    --model-variant standard \
    --threshold 0.3 \
    --device auto
```

**Modern Art (Abstract, High Contrast)**
```bash
python -m src.cli.edge_infer \
    --input modern_art.jpg \
    --model-variant small \
    --threshold 0.7 \
    --device auto
```

**Photography-Based Art**
```bash
python -m src.cli.edge_infer \
    --input photo_art.jpg \
    --model-variant standard \
    --threshold 0.5 \
    --device auto
```

## 🔍 **Configuration Validation**

### Validate Settings
```python
from src.config import validate_config

config = {
    "edge_detection": {
        "model_variant": "standard",
        "threshold": 0.5,
        "device": "auto"
    }
}

is_valid = validate_config(config)
print(f"Configuration valid: {is_valid}")
```

### Common Configuration Errors
```bash
# Invalid threshold (outside 0.0-1.0)
--threshold 1.5  # ❌ Error

# Invalid model variant
--model-variant large  # ❌ Error

# Invalid device
--device gpu  # ❌ Error (use 'cuda' or 'mps')
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