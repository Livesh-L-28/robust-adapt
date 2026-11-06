# Stage 15 Documentation Architecture & Information Architecture Specification

**Stage:** 15 — Documentation Engineering, Developer Experience, API Reference, Tutorials & Adoption Readiness<br>
**Package:** `aml-core` v0.1.0.dev0<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Execution Environment:** Windows 11 Enterprise (AMD64), Python 3.14.3<br>
**Date:** 2026-11-06<br>
**Status:** COMPLETE & INDEPENDENTLY VERIFIED

---

## 1. Executive Summary

This document specifies the technical documentation architecture, site taxonomy, directory structure, navigation hierarchy, and rendering configuration for AdaptiveML (`aml-core`).

A high-quality documentation system must balance developer onboarding speed (sub-5 minute quick start) with deep algorithmic transparency, rigorous mathematical formulations, comprehensive API references, and reproducible benchmarks.

---

## 2. Documentation Framework Selection

### Evaluated Alternatives
1. **Sphinx + ReadTheDocs Theme**: Powerful autodoc capabilities, but heavy dependency footprint, complex reStructuredText markup syntax, and sluggish local live-reload performance.
2. **Docusaurus (Node.js)**: Modern React-based UI, but introduces mandatory Node.js/npm dependencies into a pure Python repository.
3. **MkDocs with Material (`mkdocs-material`)**: **SELECTED**.
   - **Simplicity**: Pure Markdown and GitHub Flavored Markdown (GFM).
   - **Performance**: High-speed local build ($<5\text{ s}$ for $>50$ pages) and instant hot-reload.
   - **Search & Navigation**: Client-side full-text search index, progressive disclosure sidebar navigation, and deep linking.
   - **Accessibility & Mobile**: Mobile-responsive, dark/light theme switching, ARIA-accessible markup.
   - **Code Ergonomics**: Syntax highlighting with line numbers, copy-to-clipboard buttons, and Mermaid diagram rendering.

---

## 3. Information Architecture (Site Taxonomy)

The documentation is organized into 16 coherent major sections:

```
AdaptiveML Documentation
├── 1. Introduction
│   ├── Overview (docs/index.md)
│   ├── Problem Statement (docs/introduction/problem-statement.md)
│   ├── Architecture Overview (docs/introduction/architecture-overview.md)
│   └── Design Principles (docs/introduction/design-principles.md)
├── 2. Getting Started
│   ├── Installation (docs/getting-started/installation.md)
│   ├── Environment Setup (docs/getting-started/environment-setup.md)
│   ├── Installation Verification (docs/getting-started/installation-verification.md)
│   ├── Optional Integrations (docs/getting-started/optional-integrations.md)
│   ├── 5-Minute Quickstart (docs/getting-started/quickstart.md)
│   ├── First Adaptive Model (docs/getting-started/first-adaptive-model.md)
│   └── First Streaming Model (docs/getting-started/first-streaming-model.md)
├── 3. Core Concepts
│   ├── Concept Drift Fundamentals (docs/concepts/concept-drift.md)
│   ├── Label Noise & Robustness (docs/concepts/label-noise.md)
│   ├── Minority Intelligence & Imbalance (docs/concepts/class-imbalance.md)
│   ├── Resource-Aware Optimization (docs/concepts/resource-optimization.md)
│   └── Unified Controller Coordination (docs/concepts/controller-arbitration.md)
├── 4. Algorithms
│   ├── ALA 3.0 (Adaptive Learning Algorithms)
│   │   ├── Overview & Theory (docs/algorithms/ala/overview.md)
│   │   ├── Algorithm Design (docs/algorithms/ala/algorithm-design.md)
│   │   ├── Configuration Guide (docs/algorithms/ala/configuration.md)
│   │   ├── Recurring Concept Memory (docs/algorithms/ala/recurring-concept-memory.md)
│   │   ├── Code Examples (docs/algorithms/ala/examples.md)
│   │   └── Known Limitations (docs/algorithms/ala/limitations.md)
│   ├── RLA 3.0 (Robust Learning Algorithms)
│   │   ├── Overview & Noise Taxonomy (docs/algorithms/rla/overview.md)
│   │   ├── Algorithm Design (docs/algorithms/rla/algorithm-design.md)
│   │   ├── Configuration Guide (docs/algorithms/rla/configuration.md)
│   │   ├── Asymmetric Transition Defense (docs/algorithms/rla/asymmetric-noise.md)
│   │   ├── Code Examples (docs/algorithms/rla/examples.md)
│   │   └── Known Limitations (docs/algorithms/rla/limitations.md)
│   ├── Adaptive Minority Intelligence 2.0
│   │   ├── Overview & Prior Estimation (docs/algorithms/minority-intelligence/overview.md)
│   │   ├── Algorithm Design (docs/algorithms/minority-intelligence/algorithm-design.md)
│   │   ├── Configuration Guide (docs/algorithms/minority-intelligence/configuration.md)
│   │   ├── Dynamic FP Threshold Management (docs/algorithms/minority-intelligence/threshold-management.md)
│   │   ├── Code Examples (docs/algorithms/minority-intelligence/examples.md)
│   │   └── Known Limitations (docs/algorithms/minority-intelligence/limitations.md)
│   ├── RAO 2.0 (Resource-Aware Optimization)
│   │   ├── Overview & Memory Profile (docs/algorithms/rao/overview.md)
│   │   ├── Algorithm Design (docs/algorithms/rao/algorithm-design.md)
│   │   ├── Configuration Guide (docs/algorithms/rao/configuration.md)
│   │   ├── Vectorized Low-Memory AdamW (docs/algorithms/rao/vectorized-optimizer.md)
│   │   ├── Code Examples (docs/algorithms/rao/examples.md)
│   │   └── Known Limitations (docs/algorithms/rao/limitations.md)
│   └── ULC-v5 (Unified Learning Controller)
│       ├── Overview & Motivation (docs/algorithms/ulc/overview.md)
│       ├── Architecture & State (docs/algorithms/ulc/architecture.md)
│       ├── Configuration Guide (docs/algorithms/ulc/configuration.md)
│       ├── Five-Tier Intervention Hierarchy (docs/algorithms/ulc/intervention-hierarchy.md)
│       ├── Code Examples (docs/algorithms/ulc/examples.md)
│       └── Known Limitations (docs/algorithms/ulc/limitations.md)
├── 5. Public API Reference
│   ├── API Overview & Exports (docs/api/index.md)
│   ├── Core API (docs/api/core.md)
│   ├── ALA API (docs/api/ala.md)
│   ├── RLA API (docs/api/rla.md)
│   ├── Minority Intelligence API (docs/api/minority.md)
│   ├── RAO API (docs/api/rao.md)
│   ├── ULC API (docs/api/ulc.md)
│   ├── Integrations API (docs/api/integrations.md)
│   └── State & Serialization API (docs/api/state.md)
├── 6. Framework Integrations
│   ├── Overview & Data Contracts (docs/integrations/index.md)
│   ├── Pure NumPy Workflows (docs/integrations/numpy.md)
│   ├── Scikit-Learn Pipelines & Estimators (docs/integrations/scikit-learn.md)
│   ├── PyTorch Modules & Optimizers (docs/integrations/pytorch.md)
│   ├── DataFrames: Pandas & Polars (docs/integrations/dataframes.md)
│   └── Deferred Frameworks: TensorFlow/Keras (docs/integrations/deferred-frameworks.md)
├── 7. Guides & Checkpoints
│   ├── Checkpoints, State & Recovery (docs/guides/checkpoints-and-recovery.md)
│   ├── Observability & Telemetry (docs/guides/observability.md)
│   └── CPU Optimization Guide (docs/guides/cpu-performance.md)
├── 8. Practical Industry Tutorials
│   ├── 01. Streaming Anomaly Detection (docs/tutorials/01_streaming_anomaly_detection.md)
│   ├── 02. Recurring Concept Demand Shifts (docs/tutorials/02_recurring_demand_shifts.md)
│   ├── 03. Learning Under Extreme Label Noise (docs/tutorials/03_extreme_label_noise.md)
│   ├── 04. Fraud Detection Imbalanced Streams (docs/tutorials/04_fraud_detection_streams.md)
│   ├── 05. Low-Memory PyTorch Training (docs/tutorials/05_low_memory_pytorch.md)
│   └── 06. Unified Multi-Pillar Coordination (docs/tutorials/06_unified_coordination.md)
├── 9. System Architecture & Research
│   ├── System Architecture (docs/architecture/system-architecture.md)
│   ├── Security Architecture (docs/architecture/security-architecture.md)
│   └── Empirical Research & Provenance (docs/research/research-methodology.md)
├── 10. Troubleshooting & FAQ
│   ├── Troubleshooting Common Errors (docs/troubleshooting/index.md)
│   └── Frequently Asked Questions (docs/faq.md)
└── 11. Community & Governance
    ├── Contributing Guide (docs/community/contributing.md)
    ├── Code of Conduct (docs/community/code-of-conduct.md)
    ├── Security Policy (docs/community/security.md)
    └── Licensing & Trademark Notice (docs/community/license.md)
```

---

## 4. Navigation and Build Hygiene Standards

1. **Zero External Directory Escapes**: All MkDocs nav entries point strictly to markdown files inside `docs/`. Root community files (`CONTRIBUTING.md`, `LICENSE`, etc.) are wrapped in dedicated clean community pages within `docs/community/`.
2. **Strict Link Resolution**: All relative cross-page links are verified against the document root.
3. **No Build Warnings**: Build execution runs with strict validation (`mkdocs build --strict`).
4. **Runnable Code Guarantee**: All code examples in Quick Start, Component Guides, and Tutorials are tested directly against the installed `adaptive_ml` distribution.
