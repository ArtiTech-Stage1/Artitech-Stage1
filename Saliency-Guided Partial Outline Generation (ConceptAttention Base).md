This document describes how to integrate **ConceptAttention**, a state-of-the-art zero-shot saliency model, into the existing **PiDiNet + DDN edge extraction pipeline** to enable **emotion-based partial outline generation** for ArtiTech.

---

## 📌 Objective

- Generate partial outlines that **hide emotionally important parts** of artworks
    
- Let users **fill in blank areas** as a form of therapeutic expression
    
- Use **ConceptAttention** to identify those key emotional regions
    

### 🎯 Purpose of Saliency Map

The saliency map highlights **regions of high semantic or emotional importance** within the artwork based on a concept prompt (e.g., "face", "gesture"). These regions are used to determine which parts of the outline should be hidden to encourage user creativity.

By selectively masking these salient areas, the system allows users to express or project their emotions by drawing them back into the composition. This promotes **engaged, reflective participation** instead of passive tracing.

- Generate partial outlines that **hide emotionally important parts** of artworks
    
- Let users **fill in blank areas** as a form of therapeutic expression
    
- Use **ConceptAttention** to identify those key emotional regions
    

---

## 🔁 High-Level Pipeline

```
Input Artwork
     ↓
PiDiNet → Edge Map A
     ↓
DDN Model → Edge Map B
     ↓
Hybrid Fusion (A + B) → Full Outline
     ↓
ConceptAttention → Saliency Heatmap
     ↓
Threshold + Invert → Saliency Mask
     ↓
Mask ∩ Outline → Partial Outline
     ↓
→ Save SVG or render to user canvas
```

---

## 🧠 ConceptAttention Overview

- Uses pre-trained **Diffusion Image Transformers (DiT)** for zero-shot concept-based saliency
    
- Input = image + concept prompt (e.g., `"face"`, `"emotion center"`, `"eyes"`)
    
- Output = attention-based saliency map aligned with concept
    
- Reference: [ConceptAttention GitHub (helblazer811)](https://github.com/helblazer811/ConceptAttention)
    
- Uses pre-trained **Diffusion Image Transformers (DiT)** for zero-shot concept-based saliency
    
- Input = image + concept prompt (e.g., `"face"`, `"emotion center"`, `"eyes"`)
    
- Output = attention-based saliency map aligned with concept
    
- Reference: [ConceptAttention GitHub](https://github.com/StanfordVL/ConceptAttention)
    

---

## 🦪 Integration with PiDiNet + DDN

### 1. **Edge Map Extraction**

#### A. PiDiNet Output

```python
from src.edge_detection.pidinet_model import PiDiNetModel
model = PiDiNetModel(model_path="weights/pidinet.pth", device="cuda", model_variant="small")
edge_map_a = model.predict(image, threshold=0.25)
```

#### B. DDN Output _(Phase 2)_

```python
from src.edge_detection.ddn_model import DDNModel
model_ddn = DDNModel(model_path="weights/ddn.pth", device="cuda")
edge_map_b = model_ddn.predict(image)
```

#### C. Fusion

```python
from src.edge_detection.fusion import EdgeFusion
fusion = EdgeFusion(pidinet_model=model, ddn_model=model_ddn)
outline = fusion.fuse_edges(edge_map_a, edge_map_b, alpha=0.7)
```

### 2. **ConceptAttention Saliency Map**

```python
from conceptattention import ConceptAttentionPredictor
predictor = ConceptAttentionPredictor()
heatmap = predictor.get_saliency_map(image, prompt="face")  # float32 [0.0, 1.0]
```

> Prompt can be dynamically selected based on emotion:
> 
> - "sadness" → `"face"`, `"eye"`
>     
> - "joy" → `"sun"`, `"sky"`
>     
> - "loneliness" → `"figure"`, `"empty space"`
>     

### 3. **Threshold + Mask Conversion**

```python
import numpy as np
saliency_mask = (heatmap > 0.4).astype(np.uint8)  # tunable threshold
mask_inverted = 1 - saliency_mask
```

### 4. **Outline ∩ (1 - Saliency Mask)**

```python
partial_outline = outline * mask_inverted
```

This removes the most emotionally salient parts from the outline, allowing users to fill them in themselves.

### 5. **Save as SVG (Optional)**

```python
from potrace import Bitmap
bmp = Bitmap(partial_outline)
path = bmp.trace()
path.write_svg("output_partial.svg")
```

---

## 🎨 Emotion-based Prompt Map (Example)

|Emotion|ConceptAttention Prompt|
|---|---|
|Sad|`"face"`, `"figure"`|
|Anxiety|`"hand"`, `"gesture"`|
|Joy|`"sun"`, `"flowers"`|
|Loneliness|`"window"`, `"distance"`|

These prompts can be managed in a central mapping dictionary (e.g., `emotion_to_prompt.py`).

---

## 🛠️ Configuration

Add to `config/system_defaults.py`:

```python
SAL_THRESHOLD = 0.4
CONCEPT_PROMPT_MAP = {
    "sad": ["face", "figure"],
    "joy": ["sun", "sky"],
    "anxious": ["hand"],
    "lonely": ["window", "silhouette"]
}
```

---

## 📈 Tuning & Testing

### ✅ Threshold Tuning

- Recommended range: `0.3 ~ 0.5`
    
- Visualize saliency + mask side-by-side for quality control
    

### ✅ Rendering Benchmark

- PiDiNet: ~21–50 ms
    
- DDN: ~70–120 ms (planned)
    
- ConceptAttention: ~200 ms (on CUDA)
    

---

## ✅ Output Spec

- Format: `uint8` image or SVG
    
- Resolution: same as input
    
- Channels: 1 (binary mask)
    

---

## 🔄 Future Extensions

- Combine multiple prompts: `"face AND emotion"`
    
- Mask-based progressive reveal during drawing
    
- Adaptive masking strength based on emotion intensity
    
- Smart fusion tuning using drawing complexity analysis
    

---

## 🔚 Summary

This saliency integration allows ArtiTech to move from static tracing to **emotion-adaptive, creativity-guiding interaction**, giving users the freedom to **emotionally reconstruct** artworks with therapeutic intent.