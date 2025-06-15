# Setup Guide
**ArtiTech Stage 1 - Installation & Basic Usage**

## 🔧 **Prerequisites**

- **Hardware**: Mac M4 (or compatible ARM64/x86_64)
- **OS**: macOS 12+ or Linux Ubuntu 20.04+
- **Python**: 3.12+
- **Memory**: 8GB+ RAM
- **Storage**: 5GB+ free space

## 📦 **Installation**

### 1. Environment Setup
```bash
# Activate existing environment
source venv_artitech/bin/activate

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "from src.config import get_default_config; print('✅ ArtiTech Stage 1 ready')"
```

### 2. Test Installation
```bash
# Quick test with production defaults
python -m src.cli.edge_infer --input images/435864.jpg --verbose

# Should output: Model loading, processing time, and save edge map
```

## 🚀 **Basic Usage**

### Production Default (Recommended)
```bash
# Process artwork with optimal settings
python -m src.cli.edge_infer --input your_artwork.jpg

# With verbose output
python -m src.cli.edge_infer --input your_artwork.jpg --verbose

# Custom output location
python -m src.cli.edge_infer --input your_artwork.jpg --output my_edges.jpg
```

### Performance Testing
```bash
# Quick benchmark
python -m src.cli.edge_infer --input your_artwork.jpg --benchmark

# Detailed benchmark
python -m src.cli.edge_infer --input your_artwork.jpg --benchmark --num-runs 50
```

### Model Variants
```bash
# Fastest processing
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant tiny

# Balanced performance/quality
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant small

# Highest quality (default)
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant standard
```

## 🎯 **Quick Reference**

### CLI Options
```bash
python -m src.cli.edge_infer [OPTIONS]

Required:
  --input PATH              Input image path

Optional:
  --output PATH             Output path (auto-generated if not specified)
  --model-variant VARIANT   tiny|small|standard (default: standard)
  --threshold FLOAT         0.0-1.0 (default: 0.5)
  --device DEVICE          auto|cpu|cuda|mps (default: auto)
  --benchmark              Run performance test
  --verbose                Show detailed output
```

### Expected Output
```
📷 Loaded image: 3092x4000 pixels
🔧 Initializing PIDINET model...
💻 Device: mps
⚡ Total processing time: 541.82ms
💾 Saved edge map: outputs/your_artwork_edges.jpg
```

## 🔍 **Troubleshooting**

### Common Issues

**"Model weights not found"**
```bash
# Check if weights exist
ls -la models/pidinet/
# Should show: table5_pidinet.pth, table5_pidinet-small.pth, table5_pidinet-tiny.pth
```

**"CUDA/MPS not available"**
```bash
# Force CPU usage
python -m src.cli.edge_infer --input your_artwork.jpg --device cpu
```

**"Out of memory"**
```bash
# Use smaller model variant
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant tiny
```

### Getting Help
```bash
# Show all options
python -m src.cli.edge_infer --help

# View current configuration
python -c "from src.config import get_default_config; import json; print(json.dumps(get_default_config(), indent=2))"
```

---

**Next**: See [Configuration Guide](CONFIGURATION.md) for advanced settings  
**Performance**: See [Performance Report](PERFORMANCE.md) for detailed benchmarks 