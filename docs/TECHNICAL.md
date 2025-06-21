# Technical Details
**ArtiTech Stage 1 - Architecture & Implementation**

## 🏗️ **System Architecture**

### Current Implementation - **UPDATED with Saliency Integration**
```
Input Artwork
     ↓
Image Preprocessing
     ↓
PiDiNet Model (PyTorch)
     ↓
Edge Probability Map
     ↓
DDN Model Enhancement (Phase 2)
     ↓
Hybrid Fusion (PiDiNet + DDN)
     ↓
Full Outline Map
     ↓
ConceptAttention Saliency Analysis ✨ NEW
     ↓
Emotion-based Masking
     ↓
Partial Outline Generation
     ↓
Output Edge Map (with Hidden Emotional Regions)
```

### Component Status
| Component | Status | Implementation | Performance |
|-----------|--------|----------------|-------------|
| **PiDiNet Model** | ✅ Complete | Real PyTorch implementation | 21-576ms |
| **CLI Interface** | ✅ Complete | Click-based with full features | Working |
| **Configuration** | ✅ Complete | Centralized system with validation | Working |
| **Multi-Device** | ✅ Complete | CPU/CUDA/MPS support | Optimized |
| **DDN Model** | 🟡 Planned | Phase 2 implementation | TBD |
| **Hybrid Fusion** | 🟡 Planned | Phase 3 implementation | TBD |
| **ConceptAttention** | 🟡 **NEW - Planned** | **Saliency-guided masking** | **~200ms CUDA** |
| **Emotion Mapping** | 🟡 **NEW - Planned** | **Therapeutic interaction** | **Real-time** |

## 🧠 **PiDiNet Model Architecture**

### Model Variants
```python
# Model configurations
VARIANTS = {
    "tiny": {
        "channels": 20,
        "layers": ["conv1", "conv2", "conv3", "conv4"],
        "memory": "~1GB",
        "performance": "21ms"
    },
    "small": {
        "channels": 30, 
        "layers": ["conv1", "conv2", "conv3", "conv4", "conv5"],
        "memory": "~1.5GB",
        "performance": "24ms"
    },
    "standard": {
        "channels": 60,
        "layers": ["conv1", "conv2", "conv3", "conv4", "conv5", "conv6"],
        "memory": "~2GB", 
        "performance": "45ms"
    }
}
```

### Key Components
1. **Pixel Difference Convolution (PDC)**
   - Custom convolution operations: cd, ad, rd, cv
   - Enhanced edge detection compared to standard convolutions

2. **Compact Spatial Attention Module (CSAM)**
   - Attention mechanism for improved edge localization
   - Reduces false positives and enhances edge quality

3. **Compact Dilation Convolution Module (CDCM)**
   - Multi-scale context understanding
   - Dilated convolutions with rates 5, 7, 9, 11

4. **MapReduce Module**
   - Feature aggregation and dimensionality reduction
   - Efficient processing of multi-scale features

## 🎯 **ConceptAttention Saliency Integration** ✨ **NEW**

### Saliency-Guided Pipeline
The ConceptAttention module enables **emotion-adaptive partial outline generation** for therapeutic art interaction:

```python
# Saliency Integration Pipeline
class SaliencyGuidedPipeline:
    """
    Emotion-based partial outline generation using ConceptAttention
    """
    def __init__(self, concept_attention_model, emotion_prompt_map):
        self.saliency_model = concept_attention_model
        self.emotion_prompts = emotion_prompt_map
        
    def generate_partial_outline(self, image, emotion, full_outline):
        # 1. Generate saliency map based on emotion
        prompt = self.emotion_prompts.get(emotion, "face")
        saliency_map = self.saliency_model.get_saliency_map(image, prompt)
        
        # 2. Create emotion mask (hide salient regions)
        emotion_mask = self._create_emotion_mask(saliency_map)
        
        # 3. Apply mask to outline (remove emotional regions)
        partial_outline = full_outline * (1 - emotion_mask)
        
        return partial_outline, emotion_mask
```

### Key Saliency Components

1. **ConceptAttention Model**
   - Zero-shot concept-based saliency detection
   - Diffusion Image Transformer (DiT) backbone
   - Emotion-guided attention mapping

2. **Emotion Prompt System**
   - Dynamic prompt selection based on user emotion
   - Semantic concept mapping (face, gesture, eyes, etc.)
   - Therapeutic context awareness

3. **Adaptive Masking**
   - Threshold-based saliency conversion
   - Emotion-specific masking strategies
   - User creativity encouragement through strategic hiding

4. **Partial Outline Generation**
   - Selective edge removal from complete outline
   - Emotion-region identification and masking
   - SVG-compatible output for interactive drawing

### Emotion-to-Concept Mapping
```python
EMOTION_CONCEPT_MAP = {
    "sadness": ["face", "figure", "eyes"],
    "joy": ["sun", "sky", "flowers"],
    "anxiety": ["hand", "gesture", "body"],
    "loneliness": ["window", "silhouette", "distance"],
    "anger": ["mouth", "expression", "tension"],
    "fear": ["shadow", "background", "isolation"]
}
```

## 💻 **Implementation Details**

### File Structure - **UPDATED**
```
src/
├── edge_detection/
│   ├── pidinet_model.py      # Main PiDiNet implementation
│   ├── ddn_model.py          # DDN model (placeholder)
│   ├── fusion.py             # Hybrid fusion logic
│   ├── saliency_model.py     # ✨ NEW: ConceptAttention integration
│   ├── emotion_mapper.py     # ✨ NEW: Emotion-to-concept mapping
│   └── converter.py          # ONNX conversion utilities
├── config/
│   ├── system_defaults.py    # Production configuration + saliency params
│   ├── emotion_presets.py    # ✨ NEW: Emotion-based configurations
│   └── __init__.py           # Configuration interface
└── cli/
    └── edge_infer.py         # Command-line interface + saliency options
```

### Core Classes - **EXTENDED**
```python
class SaliencyModel:
    """ConceptAttention wrapper for emotion-based saliency"""
    def __init__(self, model_path, device, emotion_threshold=0.4)
    def get_emotion_saliency(self, image, emotion)
    def create_therapy_mask(self, saliency_map, mask_strategy)

class EmotionMapper:
    """Maps user emotions to visual concepts for saliency guidance"""
    def __init__(self, concept_map_path)
    def get_concepts_for_emotion(self, emotion)
    def get_adaptive_threshold(self, emotion, image_complexity)

class PartialOutlineGenerator:
    """Generates therapeutic partial outlines from complete edge maps"""
    def __init__(self, saliency_model, edge_fusion)
    def generate_partial_outline(self, image, emotion, full_outline)
    def save_interactive_svg(self, partial_outline, output_path)
```

## 🚀 **Future Architecture (Updated)**

### Phase 2: DDN Integration
```
PiDiNet (Client) → Edge Map → ROI Detection
                                    ↓
DDN (Server) ← Complex Regions ← Tile Extraction
     ↓
Enhanced Edges → Fusion → Full Outline
```

### Phase 3: **Saliency-Guided Therapeutic Pipeline** ✨ **NEW**
```
Full Outline → ConceptAttention → Emotion Saliency Map
                    ↓                      ↓
            User Emotion Input → Concept Mapping → Adaptive Masking
                                     ↓
                            Partial Outline → Interactive SVG
                                     ↓
                            Therapeutic Drawing Experience
```

### Phase 4: Hybrid Fusion + Emotion Integration
```python
class TherapeuticEdgeFusion:
    """Enhanced fusion with emotion-aware processing"""
    def __init__(self, pidinet_model, ddn_model, saliency_model)
    def fuse_edges_with_emotion(self, pidinet_output, ddn_output, 
                               emotion, alpha=0.7, saliency_weight=0.3)
    def adaptive_therapeutic_fusion(self, image, emotion, complexity_threshold)
```

### Phase 5: ONNX Optimization + Mobile Saliency
```python
# Extended ONNX pipeline with saliency
torch_model → ONNX → Optimization → Quantization → Mobile Deployment
    ↓           ↓         ↓            ↓              ↓
  PyTorch    ONNX     Graph Opt    INT8/FP16    Mobile+Saliency
```

## 🔬 **Technical Specifications - UPDATED**

### Saliency Model Parameters ✨ **NEW**
| Component | Parameters | Model Size | Processing Time | Memory |
|-----------|------------|------------|-----------------|--------|
| **ConceptAttention** | ~85M | 340MB | 150-250ms | 2.5GB |
| **Emotion Mapper** | Config-based | <1MB | <5ms | 50MB |
| **Mask Generator** | Algorithmic | - | 10-20ms | 100MB |

### Input/Output Specifications - EXTENDED
```python
SALIENCY_INPUT_SPEC = {
    "image_format": "RGB image (same as edge detection)",
    "emotion_input": "string (sadness, joy, anxiety, etc.)",
    "concept_prompt": "string (auto-generated from emotion)",
    "threshold": "0.3-0.5 (emotion-adaptive)"
}

SALIENCY_OUTPUT_SPEC = {
    "saliency_map": "float32 [0.0, 1.0]",
    "emotion_mask": "uint8 binary mask", 
    "partial_outline": "uint8 edge map with hidden regions",
    "interactive_svg": "SVG with dashed/hidden sections"
}
```

## 🛠️ **Development Workflow - UPDATED**

### Saliency Model Development ✨ **NEW**
```bash
# 1. Saliency integration testing
python -m src.cli.edge_infer --input test.jpg --emotion sadness --enable-saliency

# 2. Emotion mapping validation
python -m src.cli.edge_infer --input test.jpg --emotion joy --concept-override "sun"

# 3. Therapeutic outline generation
python -m src.cli.edge_infer --input test.jpg --emotion anxiety --output-format svg

# 4. Benchmark saliency performance
python -m src.cli.edge_infer --input test.jpg --emotion sadness --benchmark --verbose
```

### Emotion Configuration Testing
```bash
# 1. Test emotion presets
python -c "from src.config.emotion_presets import validate_emotion_config; validate_emotion_config()"

# 2. Validate concept mappings
python -c "from src.edge_detection.emotion_mapper import EmotionMapper; mapper = EmotionMapper(); print(mapper.get_concepts_for_emotion('sadness'))"
```

## 📈 **Optimization Roadmap**

### Immediate (Phase 2)
1. **DDN Implementation**
   - Dense dilated network architecture
   - Server-side deployment
   - ROI-based processing

2. **Performance Profiling**
   - Detailed timing analysis
   - Memory usage optimization
   - Bottleneck identification

### Medium-term (Phase 3-4)
1. **ONNX Conversion**
   - Model export to ONNX format
   - Graph optimization
   - Quantization (INT8/FP16)

2. **Mobile Optimization**
   - CoreML conversion (iOS)
   - TensorFlow Lite (Android)
   - WebAssembly (Web)

### Long-term (Phase 5+)
1. **Custom Kernels**
   - CUDA kernel optimization
   - Metal shader optimization
   - CPU SIMD optimization

2. **Hardware Acceleration**
   - Neural Processing Unit (NPU) support
   - Tensor Processing Unit (TPU) support
   - Edge device deployment

## 🔍 **Debugging & Profiling**

### Performance Profiling
```python
# PyTorch profiler
with torch.profiler.profile(
    activities=[torch.profiler.ProfilerActivity.CPU, 
                torch.profiler.ProfilerActivity.CUDA],
    record_shapes=True
) as prof:
    model(input_tensor)

print(prof.key_averages().table(sort_by="cuda_time_total"))
```

### Memory Profiling
```python
# Memory usage tracking
import torch.profiler
torch.profiler.profile(profile_memory=True)

# GPU memory monitoring
if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.memory_allocated() / 1e9:.2f}GB")
```

---

**Implementation Status**: ✅ Production-ready PiDiNet with comprehensive testing  
**Next Phase**: DDN integration for hybrid pipeline  
**Optimization**: ONNX conversion for 2-3x performance improvement 