# ArtiTech Stage 1 - Outline-to-Sketch Engine

**High-performance edge detection using PiDiNet with production-ready configuration**

## 🎯 **Status: Production Ready**

✅ **Real PiDiNet Implementation Complete**  
✅ **Production Default: PiDiNet-Standard + 0.5 threshold**  
✅ **Comprehensive Testing on Real Artworks**  
✅ **Multi-Device Support (CPU/CUDA/MPS)**  

## 🚀 **Quick Start**

```bash
# Activate environment
source venv_artitech/bin/activate

# Process artwork with production defaults
python -m src.cli.edge_infer --input your_artwork.jpg --verbose

# Performance benchmark
python -m src.cli.edge_infer --input your_artwork.jpg --benchmark
```

## 📊 **Performance Summary**

| Model Variant | Performance | Quality | Use Case |
|---------------|-------------|---------|----------|
| **Standard** | 45-576ms | **Excellent** | **Production Default** |
| **Small** | 24-53ms | Very Good | Balanced |
| **Tiny** | 21-40ms | Good | Real-time |

*Tested on diverse artworks: Classical portraits, Asian ink paintings, Post-impressionist works*

## 🏗️ **Architecture**

```
Input Artwork → PiDiNet Model → Edge Detection → High-Quality Output
```

**Current**: PiDiNet-Standard (production ready)  
**Next Phase**: + DDN hybrid pipeline for enhanced quality

## 📚 **Documentation**

| Document | Purpose | Audience |
|----------|---------|----------|
| **[Setup Guide](docs/SETUP.md)** | Installation & basic usage | New users |
| **[Performance Report](docs/PERFORMANCE.md)** | Benchmarks & test results | Technical evaluation |
| **[Configuration Guide](docs/CONFIGURATION.md)** | Settings & customization | Power users |
| **[Technical Details](docs/TECHNICAL.md)** | Architecture & implementation | Developers |

## 🎨 **Key Features**

- **Production Quality**: Superior edge detection for professional art applications
- **Multi-Variant Support**: 3 model sizes for different performance needs
- **Device Optimized**: Automatic CPU/CUDA/MPS detection
- **Artwork Tested**: Validated on classical, traditional, and modern art styles
- **CLI Interface**: Full-featured command-line tool with benchmarking

## 🔧 **Project Structure**

```
ArtiTech-Stage1/
├── src/                     # Source code
│   ├── edge_detection/      # PiDiNet model implementation
│   ├── config/             # Production configuration
│   └── cli/                # Command-line interface
├── models/pidinet/         # Pre-trained weights
├── docs/                   # Organized documentation
└── outputs/                # Generated edge maps
```

## 🚀 **Next Steps**

- **Phase 2**: DDN integration for hybrid pipeline
- **Phase 3**: ONNX optimization for mobile deployment
- **Phase 4**: REST API and production deployment

---

**Status**: ✅ Production-ready edge detection system  
**Quality**: Excellent results on real artwork testing  
**Performance**: Optimized for Apple Silicon with multi-device support
