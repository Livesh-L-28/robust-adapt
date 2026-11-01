# AdaptiveML

> **Adaptive, Robust, and Resource-Efficient Learning**  
> *A modular, CPU-first, local-first Python algorithm library for non-stationary, noisy, and resource-constrained machine learning.*

[![Phase](https://img.shields.io/badge/Phases%200--5%3A%20Research%20Foundation%20Complete%20(Ready%20for%20Review)-blue.svg)](#roadmap-overview)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](docs/foundation/LICENSING_AND_IP_POLICY.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](docs/foundation/SCOPE_AND_REQUIREMENTS.md)
[![Architecture](https://img.shields.io/badge/Architecture-CPU--First%20%7C%20Local--First-orange.svg)](docs/foundation/PRODUCT_SPECIFICATION.md)

---

> [!IMPORTANT]
> **PROVISIONAL CODENAME & TRADEMARK NOTICE**  
> "AdaptiveML" is a working engineering codename. It is subject to formal legal, trademark, and namespace clearance during Phase 3 and Phase 16. **No packages shall be registered or published under this name until clearance gates are formally approved.**

> [!NOTE]
> **RESEARCH INTEGRITY & CLAIMS NOTICE**  
> The research challenges addressed by this project (concept drift, noisy label learning, and low-memory optimization) are active open problems in computer science. **AdaptiveML does not claim that these problems are solved.** All performance thresholds documented across project literature are **engineering and scientific targets** until verified through multi-seed empirical benchmarks in Phase 12.

---

## What is AdaptiveML?

**AdaptiveML** is an open-source Python algorithmic library designed to complement existing machine learning and deep learning ecosystems (such as NumPy, scikit-learn, and PyTorch). 

While conventional machine learning pipelines assume static datasets, pristine annotations, massive GPU memory, and continuous cloud connectivity, real-world deployment environments frequently present:
- **Non-stationary distributions and concept drift** that degrade static models.
- **Corrupted, crowd-annotated, or noisy labels** that undermine empirical risk minimization.
- **Severe memory and computational constraints** that prevent local model training and fine-tuning on commodity hardware.

AdaptiveML delivers modular, mathematically grounded algorithmic components engineered specifically for **local-first** and **CPU-first** execution.

---

## Core Product Pillars

AdaptiveML is structured around three autonomous, unbundled algorithm pillars and an optional coordination layer:

```
+-------------------------------------------------------------------------------+
|                       ULC: Unified Learning Controller                         |
|   (Optional coordination layer; balances drift, noise, and memory dynamics)   |
+-----------------------+-------------------------------+-----------------------+
                        |                               |
        +---------------+---------------+               |
        v                               v               v
+-------------------------------+ +-------------------+ +-----------------------+
|  ALA: Adaptive Learning       | |  RLA: Robust      | |  RAO: Resource-Aware  |
|  Algorithms                   | |  Learning         | |  Optimization         |
|  ---------------------------  | |  Algorithms       | |  -------------------  |
|  - Concept drift detection    | |  ---------------  | |  - Compressed states  |
|  - Incremental updates        | |  - Noisy labels   | |  - CPU efficiency     |
|  - Knowledge retention        | |  - Sample scoring | |  - Training stability |
|  - Controlled forgetting      | |  - Robust losses  | |  - Memory reduction   |
+-------------------------------+ +-------------------+ +-----------------------+
```

1. **ALA — Adaptive Learning Algorithms**:
   Addresses changing data distributions, concept drift, incremental learning, knowledge retention, and controlled forgetting.
2. **RLA — Robust Learning Algorithms**:
   Addresses noisy labels, sample reliability scoring, non-Gaussian outliers, class imbalance, and noise-tolerant learning objectives.
3. **RAO — Resource-Aware Optimization**:
   Addresses optimizer memory consumption, computational step efficiency, training stability, and constrained execution on commodity CPUs.
4. **ULC — Unified Learning Controller**:
   Coordinates ALA, RLA, and RAO dynamically when multi-objective trade-offs are required. **Each pillar remains completely independent and usable in standalone workflows.**

---

## Product Philosophy

- **Complementary Ecosystem Citizen**: Designed to work seamlessly with NumPy, scikit-learn, and PyTorch rather than re-inventing basic abstractions or autograd runtimes.
- **CPU-First & Local-First**: Built to run efficiently on standard consumer and workstation CPUs without mandatory GPU accelerators.
- **Zero Cloud Lock-In**: No mandatory cloud services, remote SaaS endpoints, or vendor-specific SDKs. Fully operable in air-gapped environments.
- **Minimalist Dependencies**: Core package depends strictly on Python standard library and `numpy >= 1.24.0`. All framework integrations are optional extras.
- **Independent Algorithm Pillars**: Adopt only what you need. ALA, RLA, and RAO never depend on each other.
- **Research Evidence Before Claims**: Theoretical formulation and prior-art vetting precede implementation; empirical multi-seed benchmarks precede superiority claims.
- **Developer-Friendly Interfaces**: Clean, idiomatic Python code with 100% strict type annotations and standard scikit-learn / PyTorch API ergonomics.

---

## Phase 0 Foundation Documentation

The project foundation is documented across ten ratified foundation artifacts:

| Document | Identifier | Description |
| :--- | :--- | :--- |
| [**Product Specification**](docs/foundation/PRODUCT_SPECIFICATION.md) | `DOC-FDN-001` | Product vision, problem statements, target personas, use cases, input/output contracts, and boundaries. |
| [**Project Charter**](docs/foundation/PROJECT_CHARTER.md) | `DOC-FDN-002` | Mission, objectives, governance structure, RFC process, engineering gates, and organizational boundaries. |
| [**Success Criteria**](docs/foundation/SUCCESS_CRITERIA.md) | `DOC-FDN-003` | Measurable scientific, engineering, and developer-experience criteria distinguishing targets from achieved results. |
| [**Scope and Requirements**](docs/foundation/SCOPE_AND_REQUIREMENTS.md) | `DOC-FDN-004` | Functional requirements (FR-ALA/RLA/RAO/ULC), non-functional requirements (NFRs), and explicit exclusions. |
| [**Research Governance**](docs/foundation/RESEARCH_GOVERNANCE.md) | `DOC-FDN-005` | Evidence standards, citation mandates, claim restrictions, negative result registry, and research ethics. |
| [**Licensing and IP Policy**](docs/foundation/LICENSING_AND_IP_POLICY.md) | `DOC-FDN-006` | Proposed Apache-2.0 license, DCO 1.1 sign-off, clean-room implementation rules, and trademark disclaimers. |
| [**Development Roadmap**](docs/foundation/ROADMAP.md) | `DOC-FDN-007` | The complete 22-phase development roadmap (Phases 0–21) with explicit deliverables and acceptance gates. |
| [**Risk Register**](docs/foundation/RISK_REGISTER.md) | `DOC-FDN-008` | Comprehensive technical, scientific, product, legal, and operational risks with mitigations and contingencies. |
| [**Decisions Log (ADRs)**](docs/foundation/DECISIONS.md) | `DOC-FDN-009` | Ratified strategic Architecture Decision Records (ADRs) and open unresolved decisions backlog. |

---

## Phase 1 Research Documentation

The Phase 1 comprehensive product and market research package comprises the following authoritative deliverables:

| Document | Identifier | Description |
| :--- | :--- | :--- |
| [**Market Research Report**](docs/research/MARKET_RESEARCH_REPORT.md) | `DOC-RES-001` | **Authoritative Phase 1 deliverable**: 24-section comprehensive report covering ecosystem, competitors, developer pain points, personas, use cases, positioning, opportunities, and references. |
| [**Competitor Register**](docs/research/COMPETITOR_REGISTER.md) | `DOC-RES-002` | Detailed competitor taxonomy, in-depth profiles (River, Cleanlab, Avalanche, bitsandbytes, imbalanced-learn, Menelaus), and capability matrices. |
| [**Developer Problem Register**](docs/research/DEVELOPER_PROBLEM_REGISTER.md) | `DOC-RES-003` | Evidence-backed pain points cataloging drift false alarms, minority-class pruning, CPU optimizer state RAM bloat, and drift-noise retraining collisions. |
| [**User & Use-Case Analysis**](docs/research/USER_AND_USE_CASE_ANALYSIS.md) | `DOC-RES-004` | Market segmentation, evidence-synthesized developer personas, realistic deployment use cases, and trust dynamics. |
| [**Opportunity Matrix**](docs/research/OPPORTUNITY_MATRIX.md) | `DOC-RES-005` | Objective 8-dimension scoring across 12 opportunities, Priority A/B/C classification, rejected vectors, and answers to the 8 core differentiation questions. |
| [**Research Evidence Register**](docs/research/RESEARCH_EVIDENCE_REGISTER.md) | `DOC-RES-006` | Traceable source log with stable URLs, access dates, epistemic classifications (`FACT`, `OBSERVATION`, `INFERENCE`, `HYPOTHESIS`, `RECOMMENDATION`), and confidence ratings. |
| [**Phase 1 Decisions & Handoff**](docs/research/PHASE_1_DECISIONS.md) | `DOC-RES-007` | Ratified strategic recommendations, rejected/deferred directions, and formal research handoff to Phases 2–7. |
| **Supporting CSV Datasets** | — | Raw structured data: [`competitor_comparison.csv`](docs/research/competitor_comparison.csv), [`opportunity_scoring.csv`](docs/research/opportunity_scoring.csv), [`research_evidence.csv`](docs/research/research_evidence.csv). |

---

## Phases 2–5 Research Foundation Documentation

The scientific and legal research foundation for AdaptiveML is codified across four specialized research dossiers and cross-phase audits:

### Phase 2: Novelty & Prior-Art Research (`docs/research/phase-2-novelty/`)
- [**Master Novelty & Prior-Art Report**](docs/research/phase-2-novelty/NOVELTY_AND_PRIOR_ART_REPORT.md) (`DOC-RES-P2-001`)
- [**ALA Prior-Art Analysis**](docs/research/phase-2-novelty/ALA_PRIOR_ART_ANALYSIS.md) (`DOC-RES-P2-002`) — ADWIN, DDM, Page-Hinkley, ARF, EWC.
- [**RLA Prior-Art Analysis**](docs/research/phase-2-novelty/RLA_PRIOR_ART_ANALYSIS.md) (`DOC-RES-P2-003`) — GCE, SCE, Co-teaching, Confident Learning, Class-Balanced Loss.
- [**RAO Prior-Art Analysis**](docs/research/phase-2-novelty/RAO_PRIOR_ART_ANALYSIS.md) (`DOC-RES-P2-004`) — AdamW, Adafactor, Lion, 8-bit Adam, GaLore.
- [**ULC Prior-Art Analysis**](docs/research/phase-2-novelty/ULC_PRIOR_ART_ANALYSIS.md) (`DOC-RES-P2-005`) — Multi-objective in-loop coordination vs. MLOps DAG tools.
- [**Patent Landscape Register**](docs/research/phase-2-novelty/PATENT_LANDSCAPE_REGISTER.md) (`DOC-RES-P2-006`) — Audited USPTO, WIPO, and Espacenet records.
- [**Existing Implementation Analysis**](docs/research/phase-2-novelty/EXISTING_IMPLEMENTATION_ANALYSIS.md) (`DOC-RES-P2-007`) — Code-level inspection of River, Cleanlab, bitsandbytes, etc.
- [**Novelty Claim Register**](docs/research/phase-2-novelty/NOVELTY_CLAIM_REGISTER.md) (`DOC-RES-P2-008`) — Strict prior-art classification.
- [**Phase 2 Evidence Register**](docs/research/phase-2-novelty/PHASE_2_EVIDENCE_REGISTER.md) (`DOC-RES-P2-009`) — Traceable DOIs and citations.

### Phase 3: Legal & IP Assessment (`docs/research/phase-3-legal-ip/`)
- [**Master Legal & IP Assessment**](docs/research/phase-3-legal-ip/LEGAL_AND_IP_ASSESSMENT.md) (`DOC-RES-P3-001`)
- [**Trademark & Naming Review**](docs/research/phase-3-legal-ip/TRADEMARK_AND_NAMING_REVIEW.md) (`DOC-RES-P3-002`) — Collision analysis with Datadog's *Adaptive ML, Inc.* and `aml-core` fallback.
- [**Open-Source License Analysis**](docs/research/phase-3-legal-ip/OPEN_SOURCE_LICENSE_ANALYSIS.md) (`DOC-RES-P3-003`) — Apache-2.0 analysis and AGPL copyleft quarantine.
- [**Dependency License Register**](docs/research/phase-3-legal-ip/DEPENDENCY_LICENSE_REGISTER.md) (`DOC-RES-P3-004`) — Direct and optional dependency license audit.
- [**Dataset License Review**](docs/research/phase-3-legal-ip/DATASET_AND_BENCHMARK_LICENSE_REVIEW.md) (`DOC-RES-P3-005`) — Usage rights and zero-vendoring policy.
- [**Copyright & Contributor Policy**](docs/research/phase-3-legal-ip/COPYRIGHT_AND_CONTRIBUTOR_POLICY.md) (`DOC-RES-P3-006`) — Developer Certificate of Origin (DCO 1.1) adoption.
- [**Patent & FTO Preliminary Review**](docs/research/phase-3-legal-ip/PATENT_AND_FTO_PRELIMINARY_REVIEW.md) (`DOC-RES-P3-007`) — Public domain safe harbors.
- [**Legal & IP Risk Register**](docs/research/phase-3-legal-ip/LEGAL_IP_RISK_REGISTER.md) (`DOC-RES-P3-008`) — 6 evaluated risks and mitigations.
- [**Phase 3 Owner Decisions**](docs/research/phase-3-legal-ip/PHASE_3_OWNER_DECISIONS.md) (`DOC-RES-P3-009`) — Ratified leadership decisions.

### Phase 4: Comprehensive Literature Review (`docs/research/phase-4-literature/`)
- [**ALA Research Dossier**](docs/research/phase-4-literature/ALA_RESEARCH_DOSSIER.md) (`DOC-LIT-001`) — Primary Dossier 1 (Concept Drift & Streaming).
- [**RLA Research Dossier**](docs/research/phase-4-literature/RLA_RESEARCH_DOSSIER.md) (`DOC-LIT-002`) — Primary Dossier 2 (Noisy Labels & Imbalance).
- [**RAO Research Dossier**](docs/research/phase-4-literature/RAO_RESEARCH_DOSSIER.md) (`DOC-LIT-003`) — Primary Dossier 3 (Low-Memory Optimization).
- [**ULC Cross-Cutting Synthesis**](docs/research/phase-4-literature/ULC_CROSS_CUTTING_SYNTHESIS.md) (`DOC-LIT-004`) — Synthesis of cross-pillar conflict modes.
- [**Comprehensive Literature Register**](docs/research/phase-4-literature/COMPREHENSIVE_LITERATURE_REGISTER.md) (`DOC-LIT-005`) — 20 verified papers with DOIs (1951–2024).
- [**Research Methods & Datasets**](docs/research/phase-4-literature/RESEARCH_METHODS_AND_DATASETS.md) (`DOC-LIT-006`) — Standardized evaluation protocols.
- [**Literature Review Master Summary**](docs/research/phase-4-literature/LITERATURE_REVIEW_SUMMARY.md) (`DOC-LIT-007`) — Scientific consensus synthesis.

### Phase 5: Research Gap Identification (`docs/research/phase-5-gap-analysis/`)
- [**Master Research Gap Analysis**](docs/research/phase-5-gap-analysis/RESEARCH_GAP_ANALYSIS.md) (`DOC-RES-P5-001`) — Consolidated gap matrix.
- [**Pillar-Specific Gaps**](docs/research/phase-5-gap-analysis/ALA_RESEARCH_GAPS.md) (`ALA_RESEARCH_GAPS.md`, `RLA_RESEARCH_GAPS.md`, `RAO_RESEARCH_GAPS.md`, `ULC_RESEARCH_GAPS.md`).
- [**Research Gap Priority Matrix**](docs/research/phase-5-gap-analysis/RESEARCH_GAP_PRIORITY_MATRIX.md) (`DOC-RES-P5-006`) — 8-dimension objective scoring.
- [**Research Questions & Hypotheses**](docs/research/phase-5-gap-analysis/RESEARCH_QUESTIONS_AND_HYPOTHESES.md) (`DOC-RES-P5-007`) — Formal $RQ$, $H_1$, $H_0$ specifications.
- [**Preliminary Experimental Designs**](docs/research/phase-5-gap-analysis/PRELIMINARY_EXPERIMENTAL_DESIGNS.md) (`DOC-RES-P5-008`) — Multi-seed benchmark protocols.
- [**Recommended Research Directions**](docs/research/phase-5-gap-analysis/RECOMMENDED_RESEARCH_DIRECTIONS.md) (`DOC-RES-P5-009`) — Mathematical tasks advancing to Phase 6.
- [**Phase 5 Decisions & Handoff**](docs/research/phase-5-gap-analysis/PHASE_5_DECISIONS.md) (`DOC-RES-P5-010`) — Formal Phase 6 authorization.

### Consolidated Cross-Phase Quality Audit & Completion
- [**Cross-Phase Quality Audit (Phases 1–5)**](docs/research/PHASE_2_TO_5_CROSS_PHASE_AUDIT.md) (`DOC-AUD-001`)
- [**Consolidated Research Completion Report (Phases 2–5)**](docs/research/PHASE_2_TO_5_COMPLETION_REPORT.md) (`DOC-REP-P25-001`)

---

## Roadmap Overview (Phases 0–21)

AdaptiveML follows a disciplined 22-phase development lifecycle. Each phase must satisfy its Acceptance Gate before subsequent phases may commence:

- **Phase 0: Project Foundation** *(ACCEPTED)*
- **Phase 1: Product & Market Research** *(READY FOR REVIEW)*
- **Phase 2: Novelty & Prior-Art Research** *(READY FOR REVIEW)*
- **Phase 3: Legal & IP Assessment** *(READY FOR REVIEW)*
- **Phase 4: Comprehensive Literature Review** *(READY FOR REVIEW)*
- **Phase 5: Research Gap Identification** *(READY FOR REVIEW)*
- **Phase 6: Mathematical & Algorithm Design** *(UPCOMING)*
- **Phase 7: Technical Architecture**
- **Phase 8: ALA Development (Adaptive Learning Algorithms)**
- **Phase 9: RLA Development (Robust Learning Algorithms)**
- **Phase 10: RAO Development (Resource-Aware Optimization)**
- **Phase 11: Unified Learning Controller (ULC)**
- **Phase 12: Research Experiments & Benchmarking**
- **Phase 13: Framework Integrations**
- **Phase 14: Production Engineering**
- **Phase 15: Documentation & Developer Experience**
- **Phase 16: Legal & Release Audit**
- **Phase 17: Alpha & Beta Releases**
- **Phase 18: PyPI 1.0 Release**
- **Phase 19: Research Publication**
- **Phase 20: Global Ecosystem Growth**
- **Phase 21: Continuous R&D**

For full phase deliverables and acceptance criteria, see the [Master Roadmap](docs/foundation/ROADMAP.md).

---

## Research & Governance Rules

Contributors and researchers must adhere to our [Research Governance](docs/foundation/RESEARCH_GOVERNANCE.md):
1. **Separate Facts from Hypotheses**: Theoretical conjectures must never be presented as established facts.
2. **Cite Prior Art**: Every algorithmic implementation must cite foundational academic literature.
3. **No Unverified Superiority Claims**: Claims of algorithmic superiority require multi-seed ($\ge 5$ seeds) statistical significance testing against standard baselines.
4. **Preserve Negative Results**: Negative empirical outcomes must be recorded in the negative results registry.
5. **No Rare-Sample Discarding**: Noise-filtering mechanisms must not discard legitimate minority-class data.
6. **Strict Pillar Independence**: ALA, RLA, and RAO must remain fully decoupled.
7. **No Mandatory Cloud or Telemetry**: Execution must remain local-first and privacy-preserving.

---

## Contributing & Legal

AdaptiveML welcomes contributions aligned with our charter. All contributions are subject to:
- **Developer Certificate of Origin (DCO 1.1)**: Every commit must include a `Signed-off-by` line.
- **License**: Proposed under the [Apache License, Version 2.0](docs/foundation/LICENSING_AND_IP_POLICY.md).

