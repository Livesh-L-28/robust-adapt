# AdaptiveML — Phase 3: Patent and Freedom-to-Operate Preliminary Review

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-007`  
> **Last Updated**: 2026-11-01  
> **Classification**: Preliminary Technical Engineering Review (*Not a Formal Legal FTO Opinion*)

---

## 1. Epistemic Separation of Patent Categories

In accordance with Research Governance Rule 10, this review maintains strict separation across four distinct legal concepts:
1. **Patent Existence**: The presence of an issued patent or published patent application in a patent office database.
2. **Legal Status**: Whether the patent is active, granted, pending, expired, abandoned, or invalidated as shown by official registry telemetry.
3. **Claim Relevance**: A technical assessment of whether the published claims describe mechanisms similar to AdaptiveML's target features.
4. **Legal Infringement Analysis**: A formal statutory determination of whether an actual product infringes valid, enforceable patent claims in a specific jurisdiction.

> [!CAUTION]
> **NO FREEDOM-TO-OPERATE (FTO) IS DECLARED.**  
> Technical teams cannot legally grant or certify Freedom to Operate. This review identifies potential patent boundaries to guide clean-room software design and direct retained legal counsel during Phase 16.

---

## 2. Preliminary Risk Assessment of Audited Patent Claims

| Patent Record | Assignee | Subject Matter | Technical Claim Scope | AdaptiveML Risk Evaluation | Engineering Design Boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **US11651239B2** | Cleanlab, Inc. | Label error identification | Claims estimating confident joint distribution matrices via out-of-sample predicted probabilities. | **High Risk if Confident Learning is copied** | **STRICT BOUNDARY**: AdaptiveML RLA will completely omit joint distribution pruning. RLA relies exclusively on public-domain loss functions (GCE, SCE) and original density-margin scoring. |
| **US20230289612A1** | Univ. of Washington / Meta | Quantized optimizer states | Claims non-linear dynamic quantile codebook quantization of optimizer states on GPU CUDA kernels. | **Medium Risk if non-linear codebooks copied** | **STRICT BOUNDARY**: AdaptiveML RAO will use linear block scaling and standard integer representations on CPU, avoiding non-linear quantile codebook mapping. |
| **US11455554B2** | Fiddler Labs, Inc. | Drift detection in cloud pipelines | Claims cloud dashboard pipelines monitoring statistical divergence (Wasserstein distance) across enterprise data. | **Low Risk** | AdaptiveML operates locally as an in-loop algorithmic estimator (`partial_fit`), not an enterprise cloud monitoring service. |
| **US11847551B2** | Sony Group Corporation | Continual learning replay buffer | Claims episodic memory buffer management based on gradient interference metrics on specialized edge neural chips. | **Low / Medium Risk** | AdaptiveML ALA uses classic public-domain reservoir sampling (Vitter 1985) and standard parameter elasticity, avoiding proprietary gradient interference selection. |

---

## 3. Public Domain Safe Harbors Under Patent Law

The strongest defense against patent aggression in machine learning is **unassailable prior art in the public domain**:
- **Bifet & Gavaldà (ADWIN, 2007)**: Published openly; anticipated any broad claim attempting to monopolize adaptive windowing for concept drift.
- **Zhang & Sabuncu (GCE, 2018)**: Open academic publication in NeurIPS 2018; invalidates subsequent attempts to patent generalized cross entropy loss.
- **Kingma & Ba (Adam, 2014) / Loshchilov & Hutter (AdamW, 2017)**: Publicly published open-access papers; foundation of modern optimization.

By grounding AdaptiveML's baseline implementations strictly in peer-reviewed academic publications predating recent corporate patent filings, the project operates within established public domain safe harbors.
