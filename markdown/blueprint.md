_Outline‑to‑Sketch Engine for Art Re‑interpretation —_ **_Stage 1_**

---

## 1. Foundation — What to Study _before coding_

| Domain                                       | Key Concepts & Papers                                                                                                                                                            | Mastery Goals                                                                   |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Digital Image Processing**                 | Convolution • DoG/XDoG filtering • Bilateral & guided filters • Morphological thinning                                                                                           | Understand why noise & lighting normalization are critical for stable edge maps |
| **Edge‑aware CNNs**                          | HED → RCF → **PiDiNet** (ECCV 2020) → **DDN** (Dense Dilated Network) → **EDMB (https://arxiv.org/abs/2501.04846?utm_source=chatgpt.com)(Vision‑Mamba)** paper | Compare architectures; learn deep supervision & multi‑scale fusion tricks       |
| **Vectorization & Differentiable Rendering** | Potrace algorithm • DiffVG pipeline • **Bézier Splatting** (2025) (https://arxiv.org/html/2503.16424v2?utm_source=chatgpt.com)                                                   | See how raster → SVG optimizers work; grasp differentiable SVG loss             |
| **Neural SVG Generation**                    | StarVector (SVG‑Stack 2 M) (https://arxiv.org/html/2312.11556v3?utm_source=chatgpt.com) • Reason‑SVG (SVGX‑DwT‑10k) (https://arxiv.org/html/2505.24499v1?utm_source=chatgpt.com) | Explore image‑to‑SVG & prompt‑to‑SVG for future creative modes                  |
| **Non‑Photorealistic Rendering (NPR)**       | Real‑Time Hatching (MSR) • Cross‑Hatch GLSL shader (https://github.com/spite/cross-hatching?utm_source=chatgpt.com)                                                              | Learn stroke‑direction quantization & tone synthesis                            |
| **Mobile/Edge AI**                           | ONNX Runtime • CoreML • INT8 quantization • Metal Performance Shaders                                                                                                            | Deploy PiDiNet/DDN at < 50 ms on phones                                        |
| **Front‑End Canvas & SVG**                   | HTML5 Canvas • Fabric.js • Paper.js • dash‑array manipulation                                                                                                                    | Interactive trace‑along UI & real‑time density slider                           |

> **Study cadence:** _2 weeks_ theory (reading + small experiments) → _1 week_ deep‑dive prototyping per domain while running team learning sessions in parallel.

---

## 2. Preferred Tech Stack (2025‑Q3)

|                       |                                                                                                            |                                                                                                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Layer                 | Stack Choice                                                                                               | Rationale                                                                                                                                                                 |
| **Model Training**    | Python 3.11 · PyTorch 2.x (`torch.compile`)                                                                | Modern compiler speed‑ups & Mamba support                                                                                                                                 |
| **Edge Detector**     | PiDiNet (client) **+** DDN (server) **+** EDMB ensemble                                                    | Fast on-device inference, server-side enhancement for complex regions, state‑of‑the‑art thin‑stroke recall<br>(https://arxiv.org/abs/2501.04846?utm_source=chatgpt.com) |
| **Vectorization**     | Potrace (C → py_potrace) for on‑device; DiffVG nightly for server; Bézier Splatting for research         | Balance latency vs. smoothness                                                                                                                                            |
| **Stylization / NPR** | OpenCV + XDoG · custom GLSL (cross‑hatch) (https://github.com/spite/cross-hatching?utm_source=chatgpt.com) | GPU shading keeps > 30 fps during preview                                                                                                                                 |
| **Runtime Back‑end**  | FastAPI (Python) + Uvicorn · Docker/K8s · Redis queue                                                      | Async image tasks, scalable micro‑services                                                                                                                                |
| **Front‑End**         | React + TypeScript · Vite · Fabric.js + Three.js                                                           | Canvas editing, future WebGL NPR shaders                                                                                                                                  |
| **Mobile**            | React‑Native + Expo; CoreML/Metal back‑end                                                                 | Single codebase → ship iOS/Android beta                                                                                                                                   |
| **Data & Ops**        | GitHub Actions CI/CD · Weights & Biases tracking · S3 (art dataset) · Supabase (auth)                      | Reproducible model runs, simple infra                                                                                                                                     |

---

## 3. Step‑by‑Step Execution Roadmap

> **Timeline:** ≈ 16 weeks • **Team:** 2 DL engineers · 1 FE/dev · 1 PM/UX

### Phase 0 — _On‑Ramp_ (Week 1‑2)

1. **Kick‑off workshop** — align on vision & success metrics (F‑score ≥ 0.82, MOS ≥ 4/5 for "traceability").

2. **Reading sprints** — split papers; each member presents a 15‑min summary.

3. **Dataset audit** — sample 50 museum images; annotate 5 ground‑truth edge maps for quick sanity checks.
    

### Phase 1 — _Baseline Prototype_ (Week 3‑5)

|                                          |                                                 |
| ---------------------------------------- | ----------------------------------------------- |
| Task                                     | Deliverable                                     |
| Integrate PiDiNet + DDN (PyTorch) → ONNX | `edge_infer.py` CLI < 50 ms/512 px on M2 laptop |
| Binary → SVG via Potrace                 | `bitmap2svg.py` produces < 250 KB files         |
| Minimal React demo                       | Upload image → returns dashed‑SVG overlay       |

### Phase 2 — _Quality Boost_ (Week 6‑8)

1. **EDMB fusion** — logical‑OR ensemble, auto‑tune thresholds; log recall ↑, FP ↓.
    
2. **Stylization pass** — add XDoG + Cross‑Hatch GLSL shader; create tone presets (sepia, graphite).
    
3. **Automated eval** — compute ODS F‑score on 100‑image hold‑out; integrate Weights & Biases dashboard.
    

### Phase 3 — _Vector Refinement & Creative Mode_ (Week 9‑11)

|   |   |
|---|---|
|Sub‑step|Tooling|
|Replace Potrace with DiffVG (5 iter) server‑side|Expect 15–20 % smoother Bézier curvature|
|Experiment Bézier Splatting for hi‑res (> 2 K px)|Benchmark rasterization speed gains|
|Spike "Prompt → SVG" micro‑service using StarVector ckpt|Demo: "Make lines floral" option for power users|

### Phase 4 — _Mobile & UX Polish_ (Week 12‑14)

- Convert PiDiNet to CoreML‑INT8; measure battery drain on iPhone 13.
    
- Add UI sliders: **Detail (ε)**, **Dash gap**, **Tone α**.
    
- Implement touch‑based "trace‑progress highlight" (dashed segments change colour when drawn).
    

### Phase 5 — _Beta Test & Iteration_ (Week 15‑16)

1. 20‑participant pilot (art students & casual users).
    
2. Collect metrics: trace time, perceived difficulty, enjoyment.
    
3. Bug‑fix, performance profiling, finalize MVP release tag `v0.1`.
    

---

## 4. Risk Matrix & Mitigation

|   |   |   |
|---|---|---|
|Risk|Impact|Mitigation|
|Edge models heavy on GPU|Mobile lag|ONNX‑INT8, dynamic tiling, fallback to Potrace‑only mode|
|SVG size spikes on texture‑heavy art|Slow load|RDP ε auto‑scales, gzip transfer, lazy‑load layers|
|Stylization artefacts on low‑contrast pieces|User confusion|Auto‑detect low contrast → increase EDMB weight|
|Dataset copyright|Legal issues|Use CC‑0 museum sets; for user uploads, transient processing only|

---

## 5. High‑Level Gantt

|   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Week|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|
|**Study / Paper Reviews**|█|█|||||||||||||||
|**Baseline PiDiNet + DDN**|||█|█|█||||||||||||
|**Stylization & EDMB**||||||█|█|█|||||||||
|**DiffVG & Creative SVG**|||||||||█|██|█||||||
|**Mobile / UX Polish**||||||||||||█|█|█|||
|**Beta & QA**|||||||||||||||█|█|

`█ = active weeks`

---

## 6. Key References

1. **Li et al.** "EDMB: Edge Detector with Mamba." _WACV 2025_.
    
2. **Pi et al.** "PiDiNet: Pixel Difference Network for Edge Detection." _ECCV 2020_.
    
3. **DDN Team** "Dense Dilated Network for Edge Detection Enhancement." GitHub.
    
4. **Reason‑SVG** "Hybrid Reward RL for Aha‑Moments in Vector Graphics Generation" (SVGX‑DwT‑10k).
    
5. _spite_ — Cross‑Hatch GLSL Shader (MIT).
    
6. **Zhou et al.** "Bézier Splatting for Fast & Differentiable Vector Graphics." _arXiv 2503.16424_.
    
7. **Guo et al.** "StarVector: Generating Scalable Vector Graphics from Images." _arXiv 2312.11556_.
    

---

### ✅ Immediate Next Steps

- **Finalize learning schedule** and assign paper owners.
    
- **Clone PiDiNet repo** and run first edge inference on three sample artworks.
    
- **Set up mono‑repo** (Python + React) with GitHub Actions template for lint/tests.