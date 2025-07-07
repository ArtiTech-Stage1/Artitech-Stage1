# Phase 2: Saliency Integration Development Plan

## 🎯 **Objective**
Transform the current production-ready edge detection system into a saliency-guided therapeutic art pipeline by integrating ConceptAttention model, emotion-to-concept mapping, dual-ROI processing, and therapeutic masking capabilities.

## 📊 **Scope of Work**

### ✅ **In Scope**
- ConceptAttention model integration with PyTorch ecosystem
- Emotion-to-concept mapping system supporting 6+ emotions (sadness, joy, anxiety, loneliness, anger, fear)
- Dual-ROI processing system (semantic + density based)
- Saliency-guided DDN enhancement within ROI tiles
- Therapeutic masking algorithms for partial outline generation
- Performance optimization to meet <300ms total pipeline target
- Enhanced CLI interface with emotion parameters
- Comprehensive testing framework for saliency accuracy
- Memory optimization to stay within 2.5GB additional VRAM budget

### ❌ **Out of Scope**
- Interactive SVG generation (Phase 3)
- Web-based therapeutic interface (Phase 3)
- Real-time user interaction features (Phase 3)
- Clinical validation studies (Phase 4)
- Mobile application development (Phase 4)

## 📋 **Step-by-Step Implementation Plan**

### **Phase 2.1: Research & Foundation (Week 1-2)**

#### 1. ConceptAttention Model Research
- **Task**: Investigate ConceptAttention GitHub repository and API
- **Deliverables**:
  - Compatibility assessment with current PyTorch 2.0+ stack
  - Performance benchmarks on target hardware (RTX 4080/4090)
  - Memory usage analysis and optimization strategies
  - Integration approach documentation

#### 2. Emotion Configuration System Design
- **Task**: Create flexible emotion-to-concept mapping framework
- **Deliverables**:
  - `src/config/emotion_configs.py` with comprehensive emotion mappings
  - JSON schema for emotion configuration validation
  - Extension mechanism for future emotion additions
  - Performance caching strategy for concept lookups

### **Phase 2.2: Core Saliency Infrastructure (Week 3-4)**

#### 3. ConceptAttention Model Wrapper
- **Task**: Implement production-ready ConceptAttention wrapper
- **Deliverables**:
  - `src/edge_detection/saliency/concept_attention.py`
  - Multi-device support (CPU/CUDA/MPS)
  - Batch processing optimization
  - Memory-efficient tensor management
  - Error handling and graceful degradation

#### 4. Emotion Mapping System
- **Task**: Build emotion-to-concept translation layer
- **Deliverables**:
  - `src/edge_detection/saliency/emotion_mapper.py`
  - Support for composite emotions (e.g., "melancholy sadness")
  - Adaptive thresholding based on emotion intensity
  - Caching mechanism for performance optimization
  - Configuration validation and error handling

### **Phase 2.3: ROI Processing System (Week 5-6)**

#### 5. Dual-ROI Processor Implementation
- **Task**: Develop semantic + density ROI intersection logic
- **Deliverables**:
  - `src/edge_detection/saliency/roi_processor.py`
  - Semantic ROI extraction from saliency maps
  - Density ROI extraction from edge complexity analysis
  - Efficient ROI intersection algorithms
  - Tile-based processing for memory efficiency
  - ROI visualization tools for debugging

#### 6. DDN Model Enhancement
- **Task**: Modify DDN model for targeted ROI processing
- **Deliverables**:
  - Enhanced `src/edge_detection/ddn_model.py`
  - ROI-specific tile processing methods
  - Memory-efficient batch processing of ROI tiles
  - Performance monitoring and optimization
  - Backward compatibility with existing DDN usage

### **Phase 2.4: Saliency Pipeline Integration (Week 7-8)**

#### 7. Main Saliency Pipeline
- **Task**: Build comprehensive saliency processing pipeline
- **Deliverables**:
  - `src/edge_detection/saliency/saliency_pipeline.py`
  - End-to-end emotion-to-saliency processing
  - Integration with existing PiDiNet workflow
  - Performance monitoring and profiling
  - Comprehensive error handling and logging

#### 8. Therapeutic Masking System
- **Task**: Implement emotion-based partial outline generation
- **Deliverables**:
  - `src/edge_detection/saliency/therapeutic_masker.py`
  - Saliency-guided masking algorithms
  - Multiple masking strategies (invert, gradient, soft-mask)
  - Quality validation for therapeutic effectiveness
  - Export compatibility with existing output formats

### **Phase 2.5: Integration & Optimization (Week 9-10)**

#### 9. Pipeline Integration
- **Task**: Integrate saliency pipeline with existing edge detection system
- **Deliverables**:
  - Enhanced `src/edge_detection/fusion.py` for saliency-guided fusion
  - Seamless fallback to Phase 1 pipeline when saliency disabled
  - Configuration management for hybrid processing modes
  - Performance benchmarking against Phase 1 baseline

#### 10. CLI Interface Enhancement
- **Task**: Extend CLI with emotion parameters and therapeutic mode
- **Deliverables**:
  - Enhanced `src/cli/edge_infer.py` with emotion support
  - New command-line parameters: `--emotion`, `--therapeutic-mode`, `--roi-strategy`
  - Comprehensive help documentation
  - Backward compatibility with existing CLI usage

### **Phase 2.6: Performance & Testing (Week 11-12)**

#### 11. Performance Optimization
- **Task**: Optimize pipeline to meet <300ms target
- **Deliverables**:
  - Memory usage optimization (target: +2.5GB max)
  - Processing time optimization (target: <200ms saliency, <300ms total)
  - Caching strategies for emotion-concept mappings
  - Model quantization for deployment optimization
  - Device-specific optimization profiles

#### 12. Comprehensive Testing Framework
- **Task**: Create test suite for saliency accuracy and performance
- **Deliverables**:
  - Unit tests for all saliency components
  - Integration tests for end-to-end pipeline
  - Performance benchmarks across device types
  - Saliency accuracy validation against ground truth
  - Memory leak detection and stress testing

## 🔧 **Quality & Constraints**

### **Performance Requirements**
- **Total Pipeline**: <300ms processing time (including existing edge detection)
- **Saliency Processing**: <200ms for ConceptAttention + ROI processing
- **Memory Usage**: Additional 2.5GB VRAM maximum
- **Accuracy**: >90% emotion-concept mapping accuracy
- **Reliability**: 99.5% processing success rate

### **Testing Requirements**
- **Unit Testing**: >95% code coverage for all new components
- **Integration Testing**: End-to-end pipeline validation
- **Performance Testing**: Automated benchmarking across CPU/CUDA/MPS
- **Accuracy Testing**: Emotion-concept mapping validation
- **Stress Testing**: Memory usage and batch processing limits

### **Security & Privacy**
- **Local Processing**: All emotion and saliency processing remains local
- **Data Validation**: Secure input validation for emotion parameters
- **Memory Management**: Automatic cleanup of sensitive processing data
- **Error Handling**: Secure error messages without data leakage

### **Accessibility & Compatibility**
- **Device Support**: CPU, CUDA, Apple Silicon (MPS)
- **Python Compatibility**: Python 3.8+ with type hints
- **Backward Compatibility**: Existing CLI and API remain functional
- **Configuration Flexibility**: Extensible emotion configuration system

## 📁 **Files to be Modified/Created**

### **New Files**
```
src/edge_detection/saliency/
├── __init__.py
├── concept_attention.py      # ConceptAttention model wrapper
├── emotion_mapper.py         # Emotion-to-concept mapping system
├── roi_processor.py          # Dual-ROI processing algorithms
├── saliency_pipeline.py      # Main saliency pipeline orchestration
└── therapeutic_masker.py     # Therapeutic masking algorithms

src/config/
└── emotion_configs.py        # Emotion configuration definitions

tests/
├── test_saliency_accuracy.py # Saliency accuracy validation
├── test_emotion_mapping.py   # Emotion-concept mapping tests
├── test_roi_processing.py    # ROI processing unit tests
├── test_therapeutic_masking.py # Therapeutic masking tests
└── test_saliency_performance.py # Performance benchmarks
```

### **Modified Files**
```
src/edge_detection/
├── ddn_model.py             # Enhance with ROI-specific processing
├── fusion.py                # Add saliency-guided fusion logic
└── pidinet_model.py         # Optional: Add saliency integration hooks

src/config/
└── system_defaults.py       # Add emotion and saliency defaults

src/cli/
└── edge_infer.py           # Add emotion parameters and therapeutic mode

requirements.txt             # Add ConceptAttention dependencies
README.md                   # Update with Phase 2 capabilities
```

## 📈 **Success Metrics**

### **Technical Metrics**
- **Processing Time**: <300ms total pipeline (Target: 250ms)
- **Memory Usage**: <2.5GB additional VRAM (Target: 2.0GB)
- **Accuracy**: >90% emotion-concept mapping (Target: 95%)
- **Test Coverage**: >95% code coverage (Target: 98%)

### **Quality Metrics**
- **Saliency Relevance**: Visual inspection of emotion-appropriate saliency maps
- **Therapeutic Effectiveness**: Partial outline quality assessment
- **Edge Quality**: Maintain existing edge detection quality standards
- **User Experience**: Intuitive CLI interface with clear error messages

### **Performance Benchmarks**
- **RTX 4090**: <200ms total pipeline
- **RTX 4080**: <250ms total pipeline  
- **Apple M2 Max**: <300ms total pipeline
- **CPU Fallback**: <800ms total pipeline (acceptable degradation)

## 🛠️ **Implementation Architecture**

### **Workflow Overview**
```
Input Artwork + Emotion → ConceptAttention → Saliency Map
     ↓                                            ↓
PiDiNet → Complete Edge Map → Edge Density → ROI Intersection
     ↓                                            ↓
Dual-ROI Processing → DDN Enhancement → Therapeutic Masking
     ↓
Partial Outline Output (Therapeutic)
```

### **Key Components**

#### ConceptAttention Integration
```python
class ConceptAttentionModel:
    """Zero-shot saliency detection using diffusion transformers"""
    
    def __init__(self, model_path: str, device: str = "auto"):
        self.device = self._setup_device(device)
        self.model = self._load_concept_attention_model(model_path)
        
    def generate_saliency_map(self, image: torch.Tensor, concepts: List[str]) -> torch.Tensor:
        """Generate saliency map for given concepts"""
        # Implementation: ConceptAttention forward pass
        pass
```

#### Emotion Mapping System
```python
class EmotionMapper:
    """Maps emotions to visual concepts for saliency guidance"""
    
    def __init__(self, config_path: str):
        self.emotion_configs = self._load_emotion_configs(config_path)
        self.concept_cache = {}
        
    def get_concepts_for_emotion(self, emotion: str) -> List[str]:
        """Get visual concepts for given emotion"""
        # Implementation: Emotion-to-concept mapping
        pass
```

#### Dual-ROI Processing
```python
class DualROIProcessor:
    """Semantic + Density ROI targeting"""
    
    def extract_semantic_roi(self, saliency_map: torch.Tensor) -> torch.Tensor:
        """Extract semantic ROI from saliency map"""
        # Implementation: Saliency-based ROI extraction
        pass
        
    def extract_density_roi(self, edge_map: torch.Tensor) -> torch.Tensor:
        """Extract density ROI from edge complexity"""
        # Implementation: Edge density analysis
        pass
        
    def merge_rois(self, semantic_roi: torch.Tensor, density_roi: torch.Tensor) -> torch.Tensor:
        """Merge semantic and density ROIs"""
        # Implementation: ROI intersection logic
        pass
```

## 🔄 **Development Workflow**

### **Phase 2.1: Research & Foundation**
1. **Week 1**: ConceptAttention model research and compatibility assessment
2. **Week 2**: Emotion configuration system design and implementation

### **Phase 2.2: Core Infrastructure**
3. **Week 3**: ConceptAttention wrapper implementation
4. **Week 4**: Emotion mapping system implementation

### **Phase 2.3: ROI Processing**
5. **Week 5**: Dual-ROI processor implementation
6. **Week 6**: DDN model enhancement for ROI processing

### **Phase 2.4: Pipeline Integration**
7. **Week 7**: Main saliency pipeline implementation
8. **Week 8**: Therapeutic masking system implementation

### **Phase 2.5: Integration & Optimization**
9. **Week 9**: Pipeline integration with existing system
10. **Week 10**: CLI interface enhancement

### **Phase 2.6: Performance & Testing**
11. **Week 11**: Performance optimization and benchmarking
12. **Week 12**: Comprehensive testing framework implementation

## 📝 **Progress Tracking**

### **Completed Tasks**
- [ ] ConceptAttention model research
- [ ] Emotion configuration system design
- [ ] ConceptAttention wrapper implementation
- [ ] Emotion mapping system implementation
- [ ] Dual-ROI processor implementation
- [ ] DDN model enhancement
- [ ] Main saliency pipeline implementation
- [ ] Therapeutic masking system implementation
- [ ] Pipeline integration
- [ ] CLI interface enhancement
- [ ] Performance optimization
- [ ] Testing framework implementation

### **Current Status**
**Phase**: 2.2 - Core Saliency Infrastructure  
**Week**: 3  
**Active Task**: ConceptAttention model wrapper implementation  
**Next Milestone**: Emotion mapping system implementation

---

**Development Status**: 🚀 **Ready to Begin Phase 2 Implementation**  
**Timeline**: 12 weeks for complete saliency integration  
**Team Requirements**: 1-2 developers with PyTorch and computer vision experience  
**Success Criteria**: Production-ready saliency-guided therapeutic art pipeline

This comprehensive plan transforms your simple request into a detailed, actionable development roadmap that anticipates technical challenges, ensures quality standards, and provides clear success metrics for Phase 2 implementation. 