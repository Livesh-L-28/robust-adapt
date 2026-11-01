# AdaptiveML — Documentation Architecture
## Phase 15 Documentation & Developer Experience Deliverable

**Document Identifier:** `DOC-DOC-008`  
**Working Codename:** AdaptiveML  
**Distribution Package Identifier:** `aml-core`  
**Current Version:** `0.1.0.dev0`  
**Date:** November 2026  
**Status:** `READY FOR REVIEW`

---

## 1. Executive Summary & Information Architecture

This document specifies the information architecture, user journeys, content hierarchy, and navigation structure of the AdaptiveML documentation site.

The site is organized to serve five distinct technical developer personas:
1. **Python ML Engineers**: Seeking drop-in streaming drift detection and scikit-learn estimators.
2. **Deep Learning Researchers**: Seeking memory-efficient AdamW optimizers and PyTorch loss modules.
3. **Edge / Embedded Developers**: Seeking CPU-first execution, bounded memory buffers, and zero GPU overhead.
4. **Academics & Peer Reviewers**: Seeking mathematical proofs, empirical telemetry, and reproducible benchmark scripts.
5. **Open-Source Contributors**: Seeking clean-room coding standards, DCO 1.1 guidance, and architecture ADRs.

---

## 2. Documentation Directory Hierarchy

The documentation is configured via `mkdocs.yml` (Material for MkDocs theme):

```
docs/
├── index.md                            # Comprehensive project overview & philosophy
│
├── getting-started/                    # Onboarding Pathway
│   ├── installation.md                 # Dependencies, wheel install, extras
│   ├── quickstart.md                   # 5-minute executable quickstart
│   └── supported-environments.md       # OS, Python, and framework matrix
│
├── concepts/                           # Theoretical & Algorithmic Foundations
│   ├── adaptive-learning.md            # Concept drift & ADWIN theory
│   ├── robust-learning.md              # Noisy labels & Theorem 2 minority guarantee
│   ├── resource-aware-optimization.md  # 8-bit quantization & optimizer state RAM
│   └── unified-controller.md           # 5-state automaton & arbitration theory
│
├── guides/                             # Practical Component How-To Guides
│   ├── ala.md                          # AdaptiveClassifier & ADWIN usage
│   ├── rla.md                          # RobustLearningPipeline & loss functions
│   ├── rao.md                          # LowMemoryAdamW & ResourceBudget
│   └── ulc.md                          # AdaptiveLearningController orchestration
│
├── integrations/                       # Ecosystem Adapters
│   ├── numpy.md                        # Standalone NumPy backend vectorization
│   ├── scikit-learn.md                 # BaseEstimator, clone(), Pipeline
│   └── pytorch.md                      # nn.Module loss & optimizer factory
│
├── tutorials/                          # 10 Practical Step-by-Step Tutorials
│   ├── 01_your_first_workflow.md
│   ├── 02_detecting_concept_drift.md
│   ├── 03_incremental_learning.md
│   ├── 04_learning_with_noisy_labels.md
│   ├── 05_preserving_minority_class.md
│   ├── 06_resource_aware_optimization.md
│   ├── 07_pytorch_integration.md
│   ├── 08_scikit_learn_integration.md
│   ├── 09_coordinating_with_ulc.md
│   └── 10_reproducing_benchmarks.md
│
├── troubleshooting/                    # Problem Diagnosis & Resolution
│   └── index.md                        # Common issues & fixes
│
└── faq.md                              # Frequently Asked Questions
```

---

## 3. Site Navigation & Theming Principles

1. **Light/Dark Mode Toggle**: Material theme supporting system preference.
2. **Search Integration**: Client-side instant keyword indexing covering code blocks, parameters, and math formulas.
3. **Copyable Snippets**: Code blocks feature one-click copy buttons.
4. **Mathematical Formatting**: KaTeX / MathJax rendering for LaTeX formulas ($\bar{\mu}_W$, $\mathcal{L}_{\text{SCE}}$, $O(P)$).
5. **Strict File Linking**: Standard relative markdown links that work on GitHub, IDEs, and local static HTML previews.

---

## 4. Audit Verdict

**Documentation Architecture Verdict**: **`PASSED — COMPREHENSIVE 8-SECTION HIERARCHY RATIFIED`**.
