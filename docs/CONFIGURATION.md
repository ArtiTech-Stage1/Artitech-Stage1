# Configuration Guide
**ArtiTech Stage 1 - PiDiNet + DDN Edge Detection Pipeline**

## 🎯 **Production Defaults**

### Current Configuration
```json
{
  "model_type": "pidinet",
  "model_variant": "standard",
  "threshold": 0.5,
  "use_sa": true,
  "use_dil": true,
  "device": "auto",
  "output_format": "jpg",
  "verbose": false,
  "benchmark": false
}
```

### Why These Defaults?
- **PiDiNet-Standard**: Highest quality for professional art applications
- **Threshold 0.5**: Optimal balance between detail and noise
- **Spatial Attention**: Enhanced edge detection accuracy
- **Dilated Convolutions**: Better context understanding
- **Auto Device**: Optimal performance on available hardware
- **JPG Output**: Standard format for edge maps
- **Verbose Off**: Clean output for production use

## 🔧 **Model Configuration**

### Edge Detection Settings
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **model_variant** | "standard" | tiny/small/standard | Model size vs quality trade-off |
| **threshold** | 0.5 | 0.1-0.9 | Edge detection sensitivity |
| **use_sa** | true | boolean | Enable spatial attention module |
| **use_dil** | true | boolean | Enable dilated convolutions |
| **device** | "auto" | auto/cpu/cuda/mps | Computing device selection |
| **output_format** | "jpg" | jpg/png/bmp | Output file format |

## 🔧 **Model Variants**

### Variant Comparison
| Variant | Channels | Quality | Speed | Memory | Best For |
|---------|----------|---------|-------|--------|----------|
| **tiny** | 20 | Good | Fastest | ~1GB | Mobile, real-time |
| **small** | 30 | Very Good | Fast | ~1.5GB | Balanced applications |
| **standard** | 60 | **Excellent** | Moderate | ~2GB | **Production quality** |

### Usage Examples
```bash
# Production default (highest quality)
python -m src.cli.edge_infer --input artwork.jpg

# Fast processing for real-time applications
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny

# Balanced option for general use
python -m src.cli.edge_infer --input artwork.jpg --model-variant small
```

## 🎨 **Threshold Configuration**

### Threshold Guide
| Value | Description | Edge Detail | Noise Level | Best For |
|-------|-------------|-------------|-------------|----------|
| **0.1-0.3** | High sensitivity | Maximum detail | Higher noise | Fine art, detailed drawings |
| **0.4-0.6** | **Balanced** | **Good detail** | **Low noise** | **General artwork** |
| **0.7-0.9** | Low sensitivity | Clean edges | Minimal noise | High contrast images |

### Threshold Examples
```bash
# High detail for intricate artwork
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.3

# Balanced setting (default)
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.5

# Clean edges for simple artwork
python -m src.cli.edge_infer --input artwork.jpg --threshold 0.7
```

## 💻 **Device Configuration**

### Device Options
| Device | Description | Performance | Compatibility |
|--------|-------------|-------------|---------------|
| **auto** | **Auto-detect best** | **Optimal** | **Universal** |
| **mps** | Apple Silicon GPU | Excellent | Mac M1/M2/M3/M4 |
| **cuda** | NVIDIA GPU | Excellent | NVIDIA GPUs |
| **cpu** | CPU processing | Good | Universal fallback |

### Device Examples
```bash
# Automatic device selection (recommended)
python -m src.cli.edge_infer --input artwork.jpg --device auto

# Force CUDA for NVIDIA GPUs
python -m src.cli.edge_infer --input artwork.jpg --device cuda

# Apple Silicon optimization
python -m src.cli.edge_infer --input artwork.jpg --device mps

# CPU fallback
python -m src.cli.edge_infer --input artwork.jpg --device cpu
```

## ⚙️ **Advanced Configuration**

### Spatial Attention Module
```bash
# Enable spatial attention (default, recommended)
python -m src.cli.edge_infer --input artwork.jpg --use-sa

# Disable spatial attention (faster, lower quality)
python -m src.cli.edge_infer --input artwork.jpg --no-sa
```

### Dilated Convolutions
```bash
# Enable dilated convolutions (default, recommended)
python -m src.cli.edge_infer --input artwork.jpg --use-dil

# Disable dilated convolutions (faster, lower quality)
python -m src.cli.edge_infer --input artwork.jpg --no-dil
```

### Output Format Options
```bash
# JPEG output (default, smaller files)
python -m src.cli.edge_infer --input artwork.jpg --output-format jpg

# PNG output (lossless, larger files)
python -m src.cli.edge_infer --input artwork.jpg --output-format png

# BMP output (uncompressed)
python -m src.cli.edge_infer --input artwork.jpg --output-format bmp
```

## 🚀 **Performance Optimization**

### Memory Optimization
```bash
# Use tiny model for low memory environments
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny

# Process smaller images to reduce memory usage
python -m src.cli.edge_infer --input artwork.jpg --max-size 1024
```

### Speed Optimization
```bash
# Fastest processing (sacrifice some quality)
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny --no-sa --no-dil

# Balanced speed vs quality
python -m src.cli.edge_infer --input artwork.jpg --model-variant small

# Maximum quality (slowest)
python -m src.cli.edge_infer --input artwork.jpg --model-variant standard --use-sa --use-dil
```

## 📊 **Benchmarking Configuration**

### Benchmark Options
```bash
# Quick benchmark (10 runs)
python -m src.cli.edge_infer --input artwork.jpg --benchmark --runs 10

# Detailed benchmark with timing
python -m src.cli.edge_infer --input artwork.jpg --benchmark --detailed --verbose

# Compare model variants
python -m src.cli.edge_infer --input artwork.jpg --benchmark --compare-variants
```

### Benchmark Output
```
📊 Benchmark Results:
Model: PiDiNet-Standard
Device: mps
Runs: 10
Average time: 45.2ms
Min time: 42.1ms
Max time: 48.7ms
Memory usage: 2.1GB
```

## 🔍 **Troubleshooting Configuration**

### Common Issues
**"Model weights not found"**
```bash
# Check model weights location
ls -la models/pidinet/
# Should contain: table5_pidinet-*.pth files
```

**"CUDA/MPS not available"**
```bash
# Force CPU usage
python -m src.cli.edge_infer --input artwork.jpg --device cpu
```

**"Out of memory"**
```bash
# Use smaller model variant
python -m src.cli.edge_infer --input artwork.jpg --model-variant tiny

# Reduce image size
python -m src.cli.edge_infer --input artwork.jpg --max-size 512
```

## 📝 **Configuration Files**

### System Defaults
Located in `src/config/system_defaults.py`:
```python
DEFAULT_CONFIG = {
    "model_variant": "standard",
    "threshold": 0.5,
    "use_sa": True,
    "use_dil": True,
    "device": "auto",
    "output_format": "jpg",
    "verbose": False
}
```

### Custom Configuration
Create custom configuration file:
```python
# custom_config.py
CUSTOM_CONFIG = {
    "model_variant": "small",
    "threshold": 0.3,
    "device": "cuda",
    "output_format": "png"
}
```

Use with:
```bash
python -m src.cli.edge_infer --config custom_config.py --input artwork.jpg
```

## ⚠️ **Future Features (Planned)**

The following features are described in the [Updated Approach](Updated%20Approach.md) document but not yet implemented:

- **Emotion-based processing**: ConceptAttention saliency integration
- **Therapeutic masking**: Partial outline generation for art therapy
- **Dual-ROI system**: Semantic and density-based region targeting
- **Interactive SVG output**: Therapeutic completion interfaces

These features are planned for future development phases and are not available in the current implementation.

---

**Configuration Status**: ✅ Complete for edge detection features  
**Optimization**: Well-tuned for production artwork processing  
**Device Support**: Optimized for CPU, CUDA, and Apple Silicon 