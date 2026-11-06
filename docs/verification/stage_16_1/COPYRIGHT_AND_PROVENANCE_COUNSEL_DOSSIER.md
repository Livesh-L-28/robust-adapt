# STAGE 16.1 DELIVERABLE 05
# Copyright Provenance, Academic Source Lineage & Authorship Counsel Dossier

**Document Identifier:** `docs/verification/stage_16_1/COPYRIGHT_AND_PROVENANCE_COUNSEL_DOSSIER.md`<br>
**Stage:** 16.1 — External Legal Counsel Review & Owner Decision Preparation<br>
**Distribution Identifier:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Working Codename:** AdaptiveML<br>
**Date:** 2026-11-06<br>
**Auditor:** Copyright and Provenance Auditor & Legal-Readiness Reviewer<br>
**Target Recipient:** External Intellectual Property Legal Counsel<br>
**Review Status:** `COUNSEL DETERMINATION REQUIRED`<br>

---

## 1. Executive Summary & Legal Background

This dossier provides specialized copyright counsel with an evidentiary lineage of all source code, mathematical implementations, documentation diagrams, and contributor sign-offs in AdaptiveML (`aml-core`).

### Core Copyright Principle
Under established copyright doctrine (e.g. 17 U.S.C. § 102(b) in the United States and international equivalents under the Berne Convention):
> *"In no case does copyright protection for an original work of authorship extend to any idea, procedure, process, system, method of operation, concept, principle, or discovery, regardless of the form in which it is described, explained, illustrated, or embodied in such work."*

While published academic papers are themselves protected by literary copyright, the abstract mathematical equations, statistical formulas, and algorithmic theorems described therein are non-copyrightable principles. AdaptiveML's source code represents independent, clean-room Python expressions of those mathematical principles.

---

## 2. Component-by-Component Traceability Matrix

The table below maps each technical subsystem to its foundational academic source, its exact implementation file, its attribution status, and the specific copyright review question for counsel:

| Component Pillar | Published Academic / Research Source | Implementation Location | Expression Category | Attribution in Code | Counsel Review Required |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Pillar 1: ALA (Hoeffding Tree)** | Domingos & Hulten, *Mining High-Speed Data Streams* (KDD 2000). | `adaptive_ml/ala/tree.py` | Original clean-room vectorized NumPy expression of the Hoeffding bound inequality. | Full citation in module docstring. | `[LEGAL QUESTION]` Does clean-room implementation of Hoeffding tree split criteria create any derivative work exposure? |
| **Pillar 1: ALA (RW-ADWIN)** | Bifet & Gavaldà, *Learning from Time-Changing Data with Adaptive Windowing* (SDM 2007). | `adaptive_ml/ala/adwin.py` | Clean-room Python implementation of sub-window cut variance bound with original reliability weighting. | Full citation in module docstring. | `[LEGAL QUESTION]` Confirm that mathematical adaptation of ADWIN sub-window variance formulas is non-infringing. |
| **Pillar 1: ALA (Concept Memory)** | Continuous Gaussian mixture and episodic rehearsal literature. | `adaptive_ml/ala/concept_memory.py` | Original architectural design combining online mean/covariance vectors with cosine retrieval. | Original design; docstring attributes project authors. | `[LEGAL QUESTION]` Confirm project ownership of original episodic memory design. |
| **Pillar 2: RLA (Symmetric CE)** | Yisen Wang et al., *Symmetric Cross Entropy for Robust Learning with Noisy Labels* (ICCV 2019). | `adaptive_ml/rla/losses.py` | Clean-room derivation of analytical gradients for closed-form formula: $\alpha \mathcal{L}_{\text{CE}} + \beta \mathcal{L}_{\text{RCE}}$. | Full ICCV citation in docstring. | `[LEGAL QUESTION]` Confirm mathematical formula expression is permissible under Apache-2.0. |
| **Pillar 2: RLA (Generalized CE)** | Zhilu Zhang & Mert Sabuncu, *Generalized Cross Entropy Loss for Training DNNs* (NeurIPS 2018). | `adaptive_ml/rla/losses.py` | Clean-room derivation of negative Box-Cox transformation bounded gradients. | Full NeurIPS citation in docstring. | `[LEGAL QUESTION]` Confirm non-infringing clean-room expression. |
| **Pillar 2: RLA (Multi-Signal Engine)**| Spatial $k$-NN consensus coupled with margin and temporal moving consistency. | `adaptive_ml/rla/reliability.py` | Original composite scoring formula: $r_i = w_m S_m + w_n S_n + w_t S_t$. | Original design; docstring attributes project authors. | `[LEGAL QUESTION]` Confirm project ownership of multi-signal reliability formula. |
| **Pillar 3: Minority Intelligence** | Beta-Binomial Bayesian conjugate prior and PID threshold control. | `adaptive_ml/minority/prior.py`, `threshold.py`, `learner.py` | Original mathematical synthesis combining rolling conjugate priors with sublinear cost powers ($0.52$). | Original design; docstring attributes project authors. | `[LEGAL QUESTION]` Confirm project ownership of dynamic FP threshold regulation. |
| **Pillar 4: RAO (Dynamic Block Quant)**| Tim Dettmers et al., *8-Bit Optimizers via Block-wise Dynamic Quantization* (ICLR 2022). | `adaptive_ml/rao/quantizer.py`, `adamw.py` | Independent CPU-vectorized NumPy & PyTorch block quantizer (64/256 elements). | Full ICLR citation in docstring. | `[LEGAL QUESTION]` Confirm implementation distinguishes from bitsandbytes CUDA custom kernel code. |
| **Pillar 5: ULC (Arbitration Automaton)**| Cross-pillar arbitration literature and utility-based control. | `adaptive_ml/ulc/automaton.py`, `v5_controller.py` | Original 5-tier intervention finite-state automaton with hysteresis and spatial discordance gating. | Original design; docstring attributes project authors. | `[LEGAL QUESTION]` Confirm project ownership of ULC-v5 master coordination architecture. |

---

## 3. Contributor Governance & DCO 1.1 Invariants

The project enforces the **Linux Foundation Developer Certificate of Origin (DCO 1.1)**:
- Every Git commit in the repository repository contains an explicit `Signed-off-by: Name <email>` line.
- By submitting with DCO 1.1, contributors legally certify that their contribution was created in whole or in part by them, that they have the right to submit it under Apache-2.0, and that no proprietary employer or university IP was misappropriated.
- `[COUNSEL DETERMINATION REQUIRED]`: Counsel is requested to advise whether an additional Contributor License Agreement (CLA) is recommended for future corporate contributions prior to 1.0 General Availability.

---

## 4. Formal Copyright Inquiries for Legal Counsel

Counsel is requested to review the following specific questions:

1. `[LEGAL QUESTION]` **Clean-Room Implementation Sufficiency:**
   Does counsel concur that implementing published mathematical equations (e.g. Hoeffding bounds, Symmetric Cross-Entropy, ADWIN cut thresholds) in clean-room Python code without copying text from academic papers creates an original copyright work owned by the project contributors?
2. `[LEGAL QUESTION]` **Sufficiency of NOTICE Attributions:**
   Does our current [`NOTICE`](file:///c:/projects/AdaptiveML/NOTICE) file properly fulfill the requirements of Section 4(d) of the Apache License, Version 2.0?
3. `[LEGAL QUESTION]` **Employee / Contractor Contribution Considerations:**
   Where open-source contributors author code while employed by commercial corporations or academic institutions, does counsel advise instituting an explicit Corporate CLA (CCLA) or does DCO 1.1 provide sufficient protection against employer copyright infringement claims?
4. `[LEGAL QUESTION]` **AI-Generated Code Precedents:**
   To the extent that code snippets or documentation structures were authored in partnership with AI pair-programming tools (e.g. Google DeepMind Antigravity), what copyright ownership and registrability implications exist under US Copyright Office guidance (March 2023 statement of policy)?
