# Open-Source Ecosystem & Community Strategy v2.0

**Document Identifier:** `DOC-STRAT-EVO-ECO-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Approved Strategic Architecture<br>

---

## 1. Ecosystem Vision & Core Commitments

The long-term vitality of **AdaptiveML** depends on cultivating an open, technically rigorous, and welcoming developer and research ecosystem.

In strict compliance with **Non-Functional Requirement NFR-DEP-001 and Research Governance Rule 9**, the ecosystem strategy is founded on three non-negotiable principles:
1. **Zero Cloud Lock-In:** AdaptiveML will never require proprietary cloud accounts, SaaS subscriptions, or paid remote APIs. Every algorithm, tutorial, benchmark, and CLI tool must be fully executable offline on commodity hardware.
2. **Minimalist Core Packaging:** The core PyPI distribution (`aml-core`) will remain lightweight, with runtime dependencies strictly restricted to standard library and NumPy.
3. **Meritocratic, Transparent Governance:** Decisions are driven by reproducible empirical evidence and open peer review rather than commercial vendor priorities.

---

## 2. Package Architecture & Extension Hierarchy

```
+-------------------------------------------------------------------------------+
|                       ADAPTIVEML DISTRIBUTION HIERARCHY                       |
+-------------------------------------------------------------------------------+
| CORE RUNTIME (Mandatory: Python >= 3.10, numpy >= 1.24.0)                     |
|  - adaptive_ml.ala (Adaptive Learning Algorithms)                             |
|  - adaptive_ml.rla (Robust Learning Algorithms)                               |
|  - adaptive_ml.rao (Resource-Aware Optimization)                              |
|  - adaptive_ml.ulc (Unified Learning Controller)                              |
|  - adaptive_ml.core (Protocols, Config, Telemetry, Exceptions)                |
+-------------------------------------------------------------------------------+
                                        |
       +--------------------------------+--------------------------------+
       |                                |                                |
       v                                v                                v
+----------------------+     +----------------------+     +----------------------+
| aml-core[torch]      |     | aml-core[sklearn]    |     | aml-core[safetensors]|
| - PyTorch optimizers |     | - scikit-learn       |     | - Zero-copy fast     |
| - Custom torch loss  |     |   estimators         |       parameter loading    |
| - Lightning hooks    |     | - Pipeline checks    |     | - Safe serialization |
+----------------------+     +----------------------+     +----------------------+
       |                                |                                |
       +--------------------------------+--------------------------------+
                                        v
+-------------------------------------------------------------------------------+
| aml-core[all] (Complete development, test, and framework integration suite)   |
+-------------------------------------------------------------------------------+
```

---

## 3. Modular Ecosystem Components

### 3.1 Plugin Architecture & Dynamic Entry Points
To encourage third-party researchers and organizations to contribute novel drift detectors, robust loss formulations, and quantization kernels without modifying the core repository, AdaptiveML will support Python entry-point plugins:

```python
# [PROPOSED / ILLUSTRATIVE: pyproject.toml of a third-party plugin]
[project.entry-points."adaptive_ml.drift_detectors"]
my_custom_detector = "my_research_package.detectors:FastCUSUMDetector"

[project.entry-points."adaptive_ml.robust_losses"]
my_custom_loss = "my_research_package.losses:TrimmableLoss"
```

Core modules discover registered plugins lazily via `importlib.metadata.entry_points(group="adaptive_ml.*")`, enabling zero-cost discovery without runtime overhead.

### 3.2 Command-Line Interface (`aml` CLI)
The `aml` CLI provides developers with instant command-line introspection and environment verification:
- `aml info`: Displays active package versions, NumPy BLAS linkage, and CPU SIMD capabilities.
- `aml inspect <path>`: Parses Safetensors / JSON model checkpoints and prints parameter shapes and compression statistics.
- `aml bench`: Executes the standard 30-second local CPU benchmark suite and outputs performance metrics.
- `aml verify`: Executes the local regression test battery in the active Python environment.

### 3.3 Documentation Portal & Benchmark Explorer
- **Documentation Engine:** MkDocs Material portal featuring search, dark mode, API reference generated from docstrings via `mkdocstrings`, and interactive runnable snippets.
- **Benchmark Explorer:** Static web dashboard hosted on GitHub Pages displaying benchmark runs across datasets, random seeds, and baselines with Wilcoxon significance p-values and confidence intervals.
- **Recipe Showcase:** Curated gallery of verified domain workflows (predictive maintenance, financial fraud, streaming NLP).

---

## 4. Community Governance & Contribution Lifecycle

```
+-------------------------------------------------------------------------------+
|                       COMMUNITY CONTRIBUTION LIFECYCLE                         |
+-------------------------------------------------------------------------------+
| 1. Research Issue / RFC Discussion (docs/rfcs/RFC-YYYYMMDD-title.md)          |
| 2. Prior-Art & Governance Check (Rules 1-10 compliance validation)           |
| 3. Clean-Room Implementation (Pure NumPy core, strict typing, 90% coverage)   |
| 4. Peer Review by Core Maintainers & Scientific Review Board                  |
| 5. Automated CI Verification (Multi-OS: Linux, macOS, Windows x Python 3.10+) |
| 6. Acceptance & Changelog Integration                                         |
+-------------------------------------------------------------------------------+
```

### 4.1 Developer Certificate of Origin (DCO)
All contributors must sign off their Git commits using `git commit -s`, certifying adherence to the standard Linux Foundation Developer Certificate of Origin (DCO 1.1) to guarantee copyright provenance and IP hygiene.

### 4.2 Mentorship & Contributor Ladder
To foster community growth:
- **Triage Maintainers:** Review bug reports, reproduce user issues, and label PRs.
- **Core Reviewers:** Review code quality, ensure typing and test coverage.
- **Pillar Custodians:** Scientific experts responsible for specific pillars (ALA, RLA, RAO, ULC).
- **Leadership Council:** Project direction, roadmap evolution, and release clearance.

---

## 5. Ecosystem Partnerships & External Bridges

To expand adoption without creating hard dependencies, AdaptiveML establishes zero-cost adapter bridges:

```
+-------------------------------------------------------------------------------+
|                         EXTERNAL ECOSYSTEM BRIDGES                            |
+-----------------------------------+-------------------------------------------+
| Target Ecosystem                  | Technical Bridge Mechanism                |
+-----------------------------------+-------------------------------------------+
| **Polars Streaming Engine**       | Arrow-based zero-copy streaming connector |
| **Hugging Face Hub**              | Safetensors model card serialization      |
| **OpenML Benchmark Repository**   | Automated public dataset loader utility   |
| **ONNX Runtime**                  | Graph exporter for streaming decision tree|
| **Jupyter / Marimo Ecosystem**    | Interactive streaming visualization widget|
+-----------------------------------+-------------------------------------------+
```

---

## 6. Adoption Metrics & Success Indicators

Long-term community health and ecosystem adoption will be evaluated against objective, publicly verifiable metrics:

| Metric Category | Target Indicator | 1-Year Post-GA Target | 3-Year Evolution Target |
| :--- | :--- | :--- | :--- |
| **Distribution** | Monthly PyPI downloads (core) | $\ge 25,000\text{ / month}$ | $\ge 250,000\text{ / month}$ |
| **Community** | GitHub Stars & Watchers | $\ge 1,500\text{ stars}$ | $\ge 8,000\text{ stars}$ |
| **Contributors** | Non-maintainer external PRs merged | $\ge 20\text{ contributors}$ | $\ge 100\text{ contributors}$ |
| **Scientific Impact** | Academic citations (Google Scholar) | $\ge 15\text{ citations}$ | $\ge 150\text{ citations}$ |
| **Production** | Documented enterprise production uses | $\ge 5\text{ organizations}$ | $\ge 30\text{ organizations}$ |

---

## 7. Itemized Ecosystem Evolution Register

| Identifier | Priority | Classification | Original Phase Mapping | Complexity | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-ECO-001** | **P2** | New Engineering | Phase 14 & Phase 20 | Medium | Low | Python Entry Points |
| **EVO-ECO-002** | **P2** | Proposed Enhancement | Phase 15 & Phase 20 | Low | Low | GitHub Pages |
| **EVO-ECO-003** | **P3** | Proposed Enhancement | Phase 20 (Ecosystem Growth)| Low | Low | Community Guidelines |
| **EVO-ECO-004** | **P3** | New Engineering | Phase 13 & Phase 20 | Medium | Low | Polars API |
| **EVO-ECO-005** | **P3** | New Engineering | Phase 13 & Phase 20 | Medium | Low | ONNX Runtime |
| **EVO-ECO-006** | **P4** | Proposed Enhancement | Phase 20 (Ecosystem Growth)| High | Medium | Jupyter Widget API |
| **EVO-ECO-007** | **P4** | Deferred Opportunity | Phase 20 (Ecosystem Growth)| Very High | High | Conda-Forge Team |

---

### Detailed Specification of Evolution Items

#### EVO-ECO-001: Dynamic Plugin Registry via PEP 621 Entry Points
- **Classification:** New Engineering
- **Priority:** P2
- **Phase Mapping:** Phase 14 (Production Engineering) & Phase 20 (Global Ecosystem Growth)
- **Problem Statement:** Third-party researchers must currently fork AdaptiveML to integrate new drift detectors or loss functions into the ULC pipeline.
- **Proposed Solution:** Implement standard entry-point hooks in `adaptive_ml.core.plugins` enabling runtime discovery of external classes registered under `adaptive_ml.ala.drift_detectors`, `adaptive_ml.rla.losses`, etc.
- **Acceptance Criteria:** Third-party package installing an entry point is automatically discoverable via `aml.plugins.list()`; zero performance overhead when no plugins are installed.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ECO-002: Interactive Benchmark Explorer & Leaderboard
- **Classification:** Proposed Enhancement
- **Priority:** P2
- **Phase Mapping:** Phase 15 (Docs & DX) & Phase 20 (Global Ecosystem Growth)
- **Problem Statement:** Benchmark results currently reside in static markdown reports, making it cumbersome for researchers to compare specific subsets of seeds or hardware environments.
- **Proposed Solution:** Build a client-side static web application (deployed via GitHub Pages) that reads benchmark JSON output files and renders interactive latency vs accuracy Pareto frontiers and Wilcoxon significance matrices.
- **Acceptance Criteria:** Zero server-side infrastructure required; loads and parses benchmark logs dynamically in the browser.
- **Estimated Complexity:** Low.
- **Risk:** Low.

---

#### EVO-ECO-003: Academic Paper Submission Artifact Kit
- **Classification:** Proposed Enhancement
- **Priority:** P3
- **Phase Mapping:** Phase 19 (Research Publication) & Phase 20 (Ecosystem Growth)
- **Problem Statement:** Researchers citing AdaptiveML in academic papers need standardized BibTeX citations, reproducible experiment shell scripts, and reproducible seed configurations.
- **Proposed Solution:** Create `docs/research/CITATION.cff` and automated bash/powershell scripts that execute publication benchmarks in a single command.
- **Acceptance Criteria:** Fully automated reproducibility runner matching published paper tables.
- **Estimated Complexity:** Low.
- **Risk:** Low.

---

#### EVO-ECO-004: Polars Streaming Zero-Copy Adapter
- **Classification:** New Engineering
- **Priority:** P3
- **Phase Mapping:** Phase 13 (Framework Integrations) & Phase 20 (Ecosystem Growth)
- **Problem Statement:** Modern streaming data pipelines increasingly use Polars for high-speed columnar data manipulation. Converting Polars DataFrames to NumPy arrays can trigger unnecessary data duplication.
- **Proposed Solution:** Implement `adaptive_ml.integrations.polars.StreamBatchIterator` using Apache Arrow zero-copy memory buffers to pass batches directly to `partial_fit`.
- **Acceptance Criteria:** Throughput increased by $\ge 25\%$ compared to `df.to_numpy()` on batches $\ge 50,000$ rows; memory allocation halved.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ECO-005: ONNX Model Export for Streaming Decision Trees
- **Classification:** New Engineering
- **Priority:** P3
- **Phase Mapping:** Phase 13 (Framework Integrations) & Phase 20 (Ecosystem Growth)
- **Problem Statement:** Enterprise production environments frequently mandate deploying models as standardized ONNX graphs to run inside existing C++ or Go inference microservices.
- **Proposed Solution:** Implement `adaptive_ml.integrations.onnx.export_tree_to_onnx()` converting a trained [`VectorizedHoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py) into an ONNX `TreeEnsembleClassifier` graph.
- **Acceptance Criteria:** ONNX model predictions match AdaptiveML Python predictions within numerical epsilon ($10^{-6}$); passes standard `onnxruntime` validation.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ECO-006: Interactive Marimo & Jupyter Streaming Dashboard Widgets
- **Classification:** Proposed Enhancement
- **Priority:** P4
- **Phase Mapping:** Phase 20 (Global Ecosystem Growth)
- **Problem Statement:** Interactive notebook data analysis benefits from visual drift indicators, real-time loss tracking, and confusion matrix plots during streaming training.
- **Proposed Solution:** Provide lightweight HTML/Canvas visualization widgets for Jupyter and Marimo notebooks rendering real-time streaming updates with $<100\text{ lines}$ of JavaScript.
- **Acceptance Criteria:** Zero heavy JS framework dependencies; works seamlessly in VS Code, JupyterLab, and Marimo.
- **Estimated Complexity:** High.
- **Risk:** Medium.

---

#### EVO-ECO-007: Automated Conda-Forge Feedstock Maintenance
- **Classification:** Deferred Opportunity
- **Priority:** P4
- **Phase Mapping:** Phase 18 (PyPI 1.0 Release) & Phase 20 (Global Ecosystem Growth)
- **Problem Statement:** Many enterprise data scientists and academic researchers manage environments exclusively via Conda/Mamba rather than pip.
- **Proposed Solution:** Establish an automated GitHub Action workflow updating the Conda-Forge feedstock recipe upon official PyPI releases.
- **Acceptance Criteria:** Clean automated conda-forge feedstock builds across Linux, macOS, and Windows.
- **Estimated Complexity:** Very High.
- **Risk:** High (conda-forge review and governance approval timeline).
