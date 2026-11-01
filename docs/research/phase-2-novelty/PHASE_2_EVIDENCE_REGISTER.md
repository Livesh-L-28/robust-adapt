# AdaptiveML — Phase 2: Evidence Register

> **Document Status**: Complete Baseline Deliverable (Phase 2)  
> **Document Identifier**: `DOC-RES-P2-009`  
> **Last Updated**: 2026-11-01  
> **Traceability Index**: DOIs, Patent Numbers, Repository URLs, Epistemic Classifications

---

## 1. Traceable Research Evidence Master Log

| Evidence ID | Focus Area | Classification | Foundational Citation / Database Record | DOI / Patent / URL | Year | Core Technical Evidence | Confidence |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- | :---: |
| **EVD-P2-001** | ALA Drift | **FACT** | Bifet, A., & Gavalda, R. *Learning from time-changing data with adaptive windowing*. SDM 2007. | [10.1137/1.9781611972771.42](https://doi.org/10.1137/1.9781611972771.42) | 2007 | ADWIN bounds false positive rate by Hoeffding inequality on sub-window means. | High |
| **EVD-P2-002** | ALA Stream | **FACT** | Gomes, H. M., et al. *Adaptive random forests for evolving data stream classification*. Machine Learning. | [10.1007/s10994-017-5642-8](https://doi.org/10.1007/s10994-017-5642-8) | 2017 | Adaptive Random Forest combines Poisson online bagging with ADWIN drift monitors per tree. | High |
| **EVD-P2-003** | ALA Continual | **FACT** | Kirkpatrick, J., et al. *Overcoming catastrophic forgetting in neural networks*. PNAS. | [10.1073/pnas.1611835114](https://doi.org/10.1073/pnas.1611835114) | 2017 | EWC uses diagonal Fisher Information Matrix to quadratically penalize weight updates on previous tasks. | High |
| **EVD-P2-004** | RLA Loss | **FACT** | Zhang, Z., & Sabuncu, M. *Generalized cross entropy loss for training deep neural networks with noisy labels*. NeurIPS. | [arXiv:1805.07836](https://arxiv.org/abs/1805.07836) | 2018 | GCE interpolates between CE and MAE using Box-Cox transformation parameter $q$. | High |
| **EVD-P2-005** | RLA Loss | **FACT** | Wang, Y., et al. *Symmetric cross entropy for robust learning with noisy labels*. IEEE ICCV. | [10.1109/ICCV.2019.00041](https://doi.org/10.1109/ICCV.2019.00041) | 2019 | SCE bounds gradient explosion by adding Reverse Cross Entropy (RCE) to standard Cross Entropy. | High |
| **EVD-P2-006** | RLA Cleanlab | **FACT** | Northcutt, C., Jiang, L., & Chuang, I. *Confident learning: Estimating uncertainty in dataset labels*. JAIR. | [10.1613/jair.1.12125](https://doi.org/10.1613/jair.1.12125) | 2021 | Confident Learning estimates joint distribution of noisy vs. true labels via out-of-fold predicted probabilities. | High |
| **EVD-P2-007** | RLA Imbalance | **FACT** | Cui, Y., et al. *Class-balanced loss based on effective number of samples*. IEEE CVPR. | [10.1109/CVPR.2019.00949](https://doi.org/10.1109/CVPR.2019.00949) | 2019 | Class-balanced reweighting scales loss by $(1-\beta)/(1-\beta^n)$ based on feature space overlap volume. | High |
| **EVD-P2-008** | RAO 8-bit | **FACT** | Dettmers, T., et al. *8-bit Optimizers via Block-wise Quantization*. ICLR. | [arXiv:2110.02861](https://arxiv.org/abs/2110.02861) | 2022 | Block-wise dynamic non-linear quantization reduces optimizer state memory to 2 bytes/param on CUDA GPUs. | High |
| **EVD-P2-009** | RAO Factor | **FACT** | Shazeer, N., & Stern, M. *Adafactor: Adaptive learning rates with sublinear memory cost*. ICML. | [arXiv:1804.04235](https://arxiv.org/abs/1804.04235) | 2018 | Factoring second moment into row and column sums reduces memory from $O(nm)$ to $O(n+m)$; omits momentum. | High |
| **EVD-P2-010** | RAO Low-Rank | **FACT** | Zhao, J., et al. *GaLore: Memory-Efficient LLM Training by Gradient Low-Rank Projection*. NeurIPS. | [arXiv:2403.03507](https://arxiv.org/abs/2403.03507) | 2024 | SVD gradient subspace projection saves 65%–80% optimizer memory; triggers CPU latency on SVD updates. | High |
| **EVD-P2-011** | Patent Cleanlab | **OBSERVATION** | Cleanlab, Inc. *Method and apparatus for identifying label errors in training data*. | **US11651239B2** | 2023 | Granted patent covering commercial Confident Learning joint distribution estimation algorithms. | High |
| **EVD-P2-012** | Patent 8-bit | **OBSERVATION** | Univ. of Washington / Meta. *Low-memory optimizer for deep neural network training*. | **US20230289612A1** | 2023 | Patent application covering non-linear quantile codebook quantization of optimizer states on GPU. | High |

---

## 2. Epistemic Assessment & Phase 2 Gate Validation

- **Established Facts**: Verified that core algorithms across all three pillars (ADWIN, GCE/SCE, Adafactor, 8-bit Adam) are published prior art.
- **Novelty Boundaries**: Formally concluded that AdaptiveML will claim **zero novelty on standalone baselines**, focusing original contributions on **rare-sample preserving reliability scoring (RLA)** and **in-loop drift-noise arbitration (ULC)**.
- **Phase 2 Gate Status**: **READY FOR REVIEW**.
