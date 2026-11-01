# AdaptiveML — Phase 2: Patent Landscape Register

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-006`  
> **Last Updated**: 2026-11-01  
> **Databases Searched**: USPTO Patent Public Search, WIPO PATENTSCOPE, Google Patents, Espacenet  
> **CPC Classes Audited**: `G06N 3/02`, `G06N 3/045`, `G06N 20/00`, `G06F 17/00`, `G06F 18/00`

---

## 1. Patent Search Methodology & Legal Disclaimers

> [!WARNING]
> **PRELIMINARY PATENT RESEARCH DISCLAIMER**  
> This register represents an internal technical search conducted by machine learning research engineers. It does **not** constitute a formal legal Freedom-to-Operate (FTO) opinion or patent infringement analysis. Patent claims are cataloged solely to identify potential prior-art boundaries. Formal FTO analysis must be conducted by qualified patent counsel during Phase 3 and Phase 16.

### 1.1 Search Query Matrix
The following Boolean search strings were executed across Google Patents, USPTO, and WIPO:
1. `("concept drift" OR "covariate shift") AND ("machine learning" OR "classifier") AND ("detect" OR "retrain" OR "window")`
2. `("optimizer" OR "optimization") AND ("quantized" OR "compressed state" OR "low-rank") AND ("neural network" OR "deep learning")`
3. `("noisy labels" OR "label noise") AND ("sample selection" OR "loss function" OR "robust estimation")`
4. `("continual learning" OR "catastrophic forgetting") AND ("replay buffer" OR "elasticity" OR "fisher information")`

---

## 2. Audited Patent Records

| Patent Record ID | Title | Publication / Patent No. | Assignee / Applicant | Filing / Pub Date | Legal Status | Jurisdictions | Relevant Claims Summary | Potential Relationship to AdaptiveML | Source URL / Database | Access Date |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: |
| **PAT-ALA-001** | Systems and methods for detecting concept drift in machine learning models | **US11455554B2** | Fiddler Labs, Inc. | 2020 / 2022 | **Active** (Granted) | US | Claims enterprise pipeline monitoring data drift using weighted statistical divergence (Wasserstein / Jensen-Shannon) on feature vectors in cloud dashboards. | Low overlap; AdaptiveML ALA operates at the algorithm level (ADWIN/DDM on streaming arrays), not enterprise cloud dashboards. | [Google Patents US11455554B2](https://patents.google.com/patent/US11455554B2/en) | 2026-11-01 |
| **PAT-ALA-002** | Continual learning with selective experience replay in neural networks | **US11847551B2** | Sony Group Corporation | 2021 / 2023 | **Active** (Granted) | US, EP | Claims hardware-specific episodic memory buffer management based on gradient interference metrics for edge image recognition. | Medium overlap; AdaptiveML ALA must ensure its reservoir sampling replay algorithms use established public-domain rules (Vitter 1985) rather than proprietary interference metrics. | [Google Patents US11847551B2](https://patents.google.com/patent/US11847551B2/en) | 2026-11-01 |
| **PAT-RLA-001** | Method and apparatus for identifying label errors in training data | **US11651239B2** | Cleanlab, Inc. (Curtis Northcutt et al.) | 2020 / 2023 | **Active** (Granted) | US, WO | Claims methods for estimating joint distribution matrices of noisy vs. true labels via out-of-sample predicted probabilities (Confident Learning). | High relevance; AdaptiveML RLA must **not** copy Cleanlab's joint distribution pruning mechanics. RLA will use public-domain robust loss functions (GCE/SCE) and density-margin metrics. | [Google Patents US11651239B2](https://patents.google.com/patent/US11651239B2/en) | 2026-11-01 |
| **PAT-RAO-001** | Mixed-precision neural network quantization systems and methods | **US20260300701A1** | Amazon Technologies, Inc. | 2024 / 2026 | **Pending** (App) | US, WO | Claims specialized cloud infrastructure that sorts tensor parameters to apply heterogeneous low-bit quantization based on activation sensitivity. | Low overlap; targets dedicated AWS cloud infrastructure and accelerator compilers, whereas RAO is software-native on commodity CPU. | [USPTO Application 20260300701](https://patents.google.com/patent/US20260300701A1/en) | 2026-11-01 |
| **PAT-RAO-002** | Efficient Quantization & Deployment Frameworks for Neural Network Training | **US12625889B2** | Microsoft Technology Licensing | 2022 / 2024 | **Active** (Granted) | US, EP | Claims graph decoders and dedicated hardware memory optimizers calculating device-specific quantization mappings for heterogeneous multi-accelerator clusters. | Low overlap; directed toward multi-node distributed cluster compilers (DeepSpeed integration), whereas RAO focuses on single-node CPU execution. | [Google Patents US12625889B2](https://patents.google.com/patent/US12625889B2/en) | 2026-11-01 |
| **PAT-RAO-003** | Low-memory optimizer for deep neural network training | **US20230289612A1** | University of Washington / Meta (Dettmers et al.) | 2022 / 2023 | **Pending** (App) | US, WO | Claims block-wise non-linear 8-bit dynamic quantization of optimizer states using non-linear quantile codebooks on GPU accelerators. | High relevance; AdaptiveML RAO must avoid proprietary non-linear codebook mappings patented for GPU; RAO will use linear block-scaling and public-domain integer representations on CPU. | [Google Patents US20230289612A1](https://patents.google.com/patent/US20230289612A1/en) | 2026-11-01 |

---

## 3. Analysis of Freedom-to-Operate (FTO) Boundaries

Based on the audited patent claims:
1. **Public Domain Academic Protection**:
   - The core mathematical formulations underlying AdaptiveML (ADWIN, Page-Hinkley, DDM, Hoeffding Trees, Generalized Cross Entropy, Symmetric Cross Entropy, AdamW, and Reservoir Sampling) were published openly without patent restrictions by academic institutions between 1954 and 2019.
   - Under US patent law (35 U.S.C. § 102), prior published academic literature anticipates and invalidates any subsequent patent claim attempting to monopolize these foundational equations.
2. **Clean-Room Implementation Requirement**:
   - Cleanlab, Inc.'s granted patents on Confident Learning create a clear proprietary boundary. **AdaptiveML will completely avoid Confident Learning pruning mechanics**, relying instead on public-domain robust loss functions (Zhang & Sabuncu 2018, Wang et al. 2019) and original density-margin metrics.
   - bitsandbytes' pending patent claims on GPU non-linear quantile codebooks require that **AdaptiveML RAO strictly use linear block-scaling and standard integer representations on CPU**, circumventing hardware-specific non-linear quantile claims.
