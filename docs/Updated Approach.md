# 🧠 New Workflow: Saliency-Guided Outline Generation (Arti v2)

This document presents the newly refined **ArtiTech image processing pipeline**, designed to replace the previous single-step outline masking with a **dual-ROI, saliency-aware, density-refined strategy**. This architecture aims to significantly enhance emotional relevance, visual engagement, and user creativity.

---

## ⚡️ What's New: Comparison to the Previous Workflow

|Aspect|Previous Workflow (v1)|New Workflow (v2)|
|---|---|---|
|🌟 Outline Generation|Directly extract full outline (PiDiNet + DDN)|Generate full outline, but apply **emotion-guided masking**|
|🧠 Saliency Targeting|Static masking or full drawing|Dynamic masking via **ConceptAttention**|
|🧹 ROI Selection Strategy|Manual or none|Dual ROI: **Semantic (saliency)** + **Visual (density)**|
|🧪 Detail Refinement|Global DDN application|DDN only applied **within ROI tiles**|
|🎨 User Experience|Full outline for tracing|Emotionally partial outline to **encourage reconstruction**|

---

## 🔁 Updated Workflow Overview

```
graph LR
A[Emotion Detected] --> B[Concept Prompt: "face", "dog", etc.]
B --> C[ConceptAttention → Saliency Map]
C --> D[Threshold → ROI-S]
E[Artwork] --> F[PiDiNet → Full Edge Map]
F --> G[Edge Density Map]
D --> H[Merged ROI = ROI-S ∩ ROI-D]
G --> H
H --> I[Apply DDN on ROI tiles]
I --> J[Fuse with PiDiNet → Final Outline]
J --> K[Mask Salient Areas → Partial Outline]
K --> L[User Completes Drawing Based on Emotion]
```

---

## 🧬 Stage-by-Stage Pipeline Explanation

### **Step 1: Emotion → Prompt (External Input)**

- The user’s emotional state (e.g., “lonely”, “joyful”) is detected and mapped to semantic concept prompts (e.g., “face”, “dog”, “sunlight”).
    
- ⚠️ **Note:** This step is handled by a separate module developed by another team member and is assumed to provide ready-to-use prompt strings for each input image.
    

### **Step 2: ConceptAttention → Saliency Map**

- Zero-shot saliency prediction using [ConceptAttention](https://github.com/helblazer811/ConceptAttention).
    
- Outputs a grayscale heatmap highlighting **emotionally meaningful regions**.
    
- Produces ROI-S (semantic Region of Interest).
    

### **Step 3: PiDiNet → Full Edge Map**

- [PiDiNet](https://github.com/zhuoinoulu/pidinet) extracts fast global outlines of the artwork.
    
- Resulting outline is used both for **baseline structure** and to compute edge density.
    

### **Step 4: Edge Density Map → ROI-D**

- The edge map is converted into a **local complexity score** via sliding-window tile density.
    
- Densely detailed regions (e.g., facial outlines, fabric folds) are selected as ROI-D (density-based ROI).
    

### **Step 5: Merge ROI-S and ROI-D**

- The intersection of semantic and visual complexity maps is computed to get the **Merged ROI**.
    
- This prevents over-masking or masking of flat background.
    

### **Step 6: Apply DDN (Detail Refinement)**

- DDN is applied **only within the merged ROI tiles**, reducing computational load and over-detailing.
    
- The output is fused with PiDiNet’s global edge map to create a rich, balanced outline.
    

### **Step 7: Mask Salient Area**

- The original saliency map is **thresholded and inverted**.
    
- These regions are masked out from the outline to generate **intentional empty zones** for user reconstruction.
    

### **Step 8: Output Partial Outline**

- The final outline contains **intentional emotional gaps**, encouraging therapeutic filling-in.
    
- Exported as SVG or bitmap for mobile rendering.
    

---

## 🔍 Key Advantages

|Feature|Benefit|
|---|---|
|💡 Dual ROI System|Combines emotional meaning with visual relevance|
|🌟 Targeted DDN Application|Increases clarity without wasting computation|
|🎭 Emotion-Driven Masking|Turns passive tracing into therapeutic co-creation|
|🧠 Zero-shot Saliency|No need for artwork-specific training|
|🔄 Modular Design|Easily swappable for other saliency/backbone models|

---

## 🛠 Future Integrations

- Prompt compositionality: `"face AND emotion AND gesture"`
    
- Gradual masking: Reveal saliency progressively during session
    
- User-personalized saliency: CLIP-style similarity or memory-based emotion biasing
    

---

## 📂 File Placement Suggestions

|File|Purpose|
|---|---|
|`emotion_to_prompt.py`|Maps emotions to saliency concepts|
|`roi_selector.py`|Handles ROI-S and ROI-D intersection logic|
|`ddn_roi_runner.py`|DDN tile inference only on merged ROIs|
|`outline_masker.py`|Applies saliency masking to outline map|
|`final_output_writer.py`|Exports SVG or PNG for frontend|

---

By replacing the static full-outline approach with a **modular, emotionally aware pipeline**, this new workflow aligns ArtiTech more closely with the **therapeutic goal of user self-expression through active completion**, instead of passive repetition.