# Setup Guide
**ArtiTech Stage 1 - PiDiNet + DDN Edge Detection Pipeline**

## 🚀 **Quick Setup**

### Prerequisites
- Python 3.8+ (3.9+ recommended)
- 4GB+ RAM for standard model
- Optional: CUDA-capable GPU or Apple Silicon for acceleration

### Installation
```bash
# Clone repository
git clone <repository-url>
cd ArtiTech-Stage1

# Create virtual environment
python -m venv venv_artitech
source venv_artitech/bin/activate  # Linux/Mac
# venv_artitech\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download model weights (if not included)
python -c "from src.edge_detection.pidinet_model import download_weights; download_weights()"
```

### First Run
```bash
# Test with sample image
python -m src.cli.edge_infer --input images/test_image.jpg --verbose
```

## 🔧 **Detailed Installation**

### System Requirements

#### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **RAM**: 2GB for tiny model, 4GB for standard model
- **Storage**: 500MB for models and dependencies
- **Python**: 3.8+ with pip

#### Recommended Requirements
- **OS**: macOS 12+ (M1/M2) or Windows 11 with NVIDIA GPU
- **RAM**: 8GB+ for optimal performance
- **GPU**: Apple Silicon, NVIDIA RTX series, or modern AMD GPU
- **Storage**: 1GB+ for models and output space

### Step-by-Step Installation

#### 1. Environment Setup
```bash
# Verify Python version
python --version  # Should be 3.8+

# Create isolated environment
python -m venv venv_artitech

# Activate environment
source venv_artitech/bin/activate  # Linux/Mac
# OR
venv_artitech\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip
```

#### 2. Install Dependencies
```bash
# Install PyTorch (automatically detects CUDA/MPS)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# For CUDA support (if NVIDIA GPU available)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other requirements
pip install -r requirements.txt
```

#### 3. Verify Installation
```bash
# Test device detection
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, MPS: {torch.backends.mps.is_available()}')"

# Test model loading
python -c "from src.edge_detection.pidinet_model import PiDiNetModel; print('✅ PiDiNet model loaded successfully')"
```

## 📁 **Model Weights Setup**

### Pre-trained Models
The following model weights are required:

```
models/
├── pidinet/
│   ├── table5_pidinet.pth          # Standard model (60 channels)
│   ├── table5_pidinet-small.pth    # Small model (30 channels)
│   └── table5_pidinet-tiny.pth     # Tiny model (20 channels)
└── ddn/
    └── [DDN weights - placeholder for future]
```

### Download Models
```bash
# Automatic download (recommended)
python -c "from src.cli.edge_infer import setup_models; setup_models()"

# Manual download links (if automatic fails)
# Standard: https://github.com/hellozhuo/pidinet/releases/download/v1.0/table5_pidinet.pth
# Small: https://github.com/hellozhuo/pidinet/releases/download/v1.0/table5_pidinet-small.pth  
# Tiny: https://github.com/hellozhuo/pidinet/releases/download/v1.0/table5_pidinet-tiny.pth
```

## 🖥️ **Device Configuration**

### Apple Silicon (M1/M2/M3/M4)
```bash
# Verify MPS support
python -c "import torch; print('MPS available:', torch.backends.mps.is_available())"

# Test with MPS device
python -m src.cli.edge_infer --input images/test_image.jpg --device mps --verbose
```

### NVIDIA CUDA
```bash
# Verify CUDA installation
nvidia-smi  # Should show GPU information
python -c "import torch; print('CUDA version:', torch.version.cuda)"

# Test with CUDA device
python -m src.cli.edge_infer --input images/test_image.jpg --device cuda --verbose
```

### CPU Fallback
```bash
# Force CPU usage (works on all systems)
python -m src.cli.edge_infer --input images/test_image.jpg --device cpu --verbose
```

## 📖 **Basic Usage**

### Command Line Interface
```bash
# Basic edge detection
python -m src.cli.edge_infer --input your_artwork.jpg

# Specify output location
python -m src.cli.edge_infer --input your_artwork.jpg --output outputs/my_edges.jpg

# Use specific model variant
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant standard

# Adjust edge sensitivity
python -m src.cli.edge_infer --input your_artwork.jpg --threshold 0.3

# Verbose output for debugging
python -m src.cli.edge_infer --input your_artwork.jpg --verbose
```

### Command Line Options
```
Basic Options:
  --input INPUT         Input image file path
  --output OUTPUT       Output edge map file path
  --model-variant VARIANT    tiny|small|standard (default: standard)
  --threshold FLOAT     Edge detection threshold 0.1-0.9 (default: 0.5)
  --device DEVICE       auto|cpu|cuda|mps (default: auto)

Output Options:
  --output-format FORMAT     jpg|png|bmp (default: jpg)
  --save-intermediate        Save intermediate processing steps
  --output-dir DIR           Directory for all outputs

Model Options:
  --use-sa / --no-sa         Enable/disable spatial attention (default: enabled)
  --use-dil / --no-dil       Enable/disable dilated convolutions (default: enabled)

Performance Options:
  --benchmark               Run performance benchmark
  --verbose                 Detailed output and timing information
  --max-size SIZE           Maximum image dimension (for memory control)
```

### Expected Output

#### Standard Processing
```
📷 Loaded image: 1920x1080 pixels
🔧 Initializing PiDiNet model (standard variant)...
💻 Device: mps (Apple M2)
⚡ Edge detection completed in 67.3ms
💾 Saved edge map: outputs/your_artwork_edges.jpg
✅ Processing completed successfully
```

#### Verbose Mode
```
📷 Loaded image: 1920x1080 pixels
🔧 Initializing PiDiNet model...
  ├── Model variant: standard (60 channels)
  ├── Spatial attention: enabled
  ├── Dilated convolutions: enabled
  ├── Device: mps (Apple M2)
  └── Memory allocated: 2.1GB

⚡ Processing stages:
  ├── Preprocessing: 2.1ms
  ├── Model inference: 62.8ms
  ├── Postprocessing: 2.4ms
  └── Total time: 67.3ms

💾 Output saved:
  ├── Edge map: outputs/your_artwork_edges.jpg
  ├── Resolution: 1920x1080
  ├── File size: 234KB
  └── Format: JPEG

✅ Processing completed successfully
Memory peak: 2.3GB
```

## 🔍 **Troubleshooting**

### Common Issues

**"Model weights not found"**
```bash
# Check if weights exist
ls -la models/pidinet/
# Should show: table5_pidinet*.pth files

# Download missing weights
python -c "from src.cli.edge_infer import setup_models; setup_models()"
```

**"CUDA/MPS not available"**
```bash
# Force CPU usage (slower but works everywhere)
python -m src.cli.edge_infer --input your_artwork.jpg --device cpu
```

**"Out of memory"**
```bash
# Use smaller model variant
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant tiny

# Limit image size
python -m src.cli.edge_infer --input your_artwork.jpg --max-size 1024

# Close other applications to free memory
```

**"ImportError: No module named..."**
```bash
# Reinstall requirements
pip install -r requirements.txt

# Check virtual environment is activated
which python  # Should point to venv_artitech
```

**"Slow processing on CPU"**
```bash
# Expected - CPU is much slower than GPU
# Consider using smaller model variant for CPU
python -m src.cli.edge_infer --input your_artwork.jpg --model-variant tiny --device cpu
```

### Getting Help
```bash
# Show all available options
python -m src.cli.edge_infer --help

# View current configuration
python -c "from src.config import get_default_config; import json; print(json.dumps(get_default_config(), indent=2))"

# Test installation
python -m src.cli.edge_infer --input assets/test_images/test_image.png --benchmark --verbose
```

## 📊 **Performance Testing**

### Benchmark Your System
```bash
# Quick benchmark (10 runs)
python -m src.cli.edge_infer --input images/test_image.jpg --benchmark

# Detailed benchmark (50 runs)
python -m src.cli.edge_infer --input images/test_image.jpg --benchmark --runs 50 --detailed

# Compare model variants
python -m src.cli.edge_infer --input images/test_image.jpg --benchmark --compare-variants

# Compare devices (if multiple available)
python -m src.cli.edge_infer --input images/test_image.jpg --benchmark --compare-devices
```

### Performance Expectations
| Device Type | Model | Expected Time |
|-------------|-------|---------------|
| Apple M2 | Standard | ~45ms |
| Apple M2 | Small | ~24ms |
| Apple M2 | Tiny | ~21ms |
| NVIDIA RTX 4090 | Standard | ~32ms |
| Intel i7 CPU | Standard | ~576ms |
| Intel i7 CPU | Tiny | ~156ms |

## 🔧 **Advanced Configuration**

### Custom Configuration File
Create `config.json`:
```json
{
  "model_variant": "small",
  "threshold": 0.3,
  "device": "auto",
  "output_format": "png",
  "use_sa": true,
  "use_dil": true,
  "verbose": true
}
```

Use with:
```bash
python -m src.cli.edge_infer --config config.json --input your_artwork.jpg
```

### Environment Variables
```bash
# Set default device
export ARTITECH_DEVICE=mps

# Set default model variant
export ARTITECH_MODEL=standard

# Set memory limit (MB)
export ARTITECH_MAX_MEMORY=4096
```

## 📝 **Development Setup**

### For Contributors
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run linting
flake8 src/
black src/

# Type checking
mypy src/
```

### Testing Changes
```bash
# Test basic functionality
python -m src.cli.edge_infer --input assets/test_images/test_image.png --verbose

# Run benchmarks
python -m src.cli.edge_infer --input assets/test_images/test_image.png --benchmark

# Test different model variants
for variant in tiny small standard; do
    echo "Testing $variant variant..."
    python -m src.cli.edge_infer --input assets/test_images/test_image.png --model-variant $variant
done
```

## ⚠️ **Future Features**

The following features are planned but not yet implemented:

- **Emotion-based processing**: Requires ConceptAttention model integration
- **Therapeutic masking**: Partial outline generation for art therapy
- **Interactive SVG output**: Web-compatible partial outlines
- **Batch processing**: Multiple image processing optimization

See [Updated Approach](Updated%20Approach.md) for the roadmap of planned features.

---

**Setup Status**: ✅ Complete for edge detection features  
**Compatibility**: Tested on macOS, Windows, and Linux  
**Performance**: Optimized for Apple Silicon, NVIDIA CUDA, and CPU