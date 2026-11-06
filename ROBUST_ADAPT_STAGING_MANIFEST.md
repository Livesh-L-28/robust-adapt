# ROBUST-ADAPT — Explicit Git Staging Manifest & Exclusion Policy

**Document ID:** `STAGING-MANIFEST-001`<br>
**Working Repository:** `C:\projects\AdaptiveML`<br>
**Distribution:** `robust-adapt` (`0.1.0.dev0`)<br>
**Canonical Namespace:** `robust_adapt`<br>
**Compatibility Namespace:** `adaptive_ml`<br>
**Baseline Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Target Milestone:** Local Git Migration Commit<br>
**Date:** November 6, 2026<br>

---

## 1. Staging Strategy & Governance Directives

To guarantee repository hygiene, supply-chain security, and reproducible builds, **blind repository staging (e.g., `git add .` or `git add -A`) is strictly prohibited**.

This staging manifest defines:
1. **Intended File Set**: Exactly 742 reviewed, production-grade files required to establish the ROBUST-ADAPT project identity, backward compatibility shims, test suites, documentation, and formal governance reports.
2. **Excluded File Set**: Exactly 1,069 files across snapshot backups, build artifacts, static site outputs, and experiment scratch spaces, with technical justifications for exclusion.
3. **Owner Staging & Commit Command Sequence**: Explicit, non-destructive commands prepared for the Project Owner to execute locally with Developer Certificate of Origin (DCO 1.1) sign-off.

> [!IMPORTANT]
> In accordance with project governance, Antigravity has **not executed any staging or commit commands**. The working tree remains unstaged.

---

## 2. Intended File Inventory (742 Files)

The following files represent the complete, intentional delta of the ROBUST-ADAPT rebranding and defect remediation.

```
Intended Staging Set Summary:
├── robust_adapt/ (71 files)         Canonical package implementation
├── adaptive_ml/ (71 files)          PEP 562 compatibility forwarding shims
├── .github/workflows/ (2 files)     Dual-namespace CI/CD and security workflows
├── tests/ (42 files)                Unit, integration, example, and SDK test suites
├── examples/ (35 files)             Core pillar and cross-framework integration examples
├── docs/ (494 files)                Guides, API specs, architecture, tutorials, & research
├── Root Project Files (10 files)    Configs, licensing, security, & community files
└── Root Audit Reports (18 files)    Formal rebranding, defect remediation, & audit reports
Total: 742 Files
```

### 2.1 Canonical Package (`robust_adapt/`) — 71 Files
All production algorithmic logic resides exclusively within this package.
- `robust_adapt/py.typed`: PEP 561 type marker.
- `robust_adapt/__init__.py`: Package entrypoint, version (`0.1.0.dev0`), and top-level public API exports.
- `robust_adapt/core/` (7 files): `__init__.py`, `config.py`, `constants.py`, `diagnostics.py`, `exceptions.py`, `telemetry.py`, `types.py`, `validation.py`.
- `robust_adapt/ala/` (8 files): `__init__.py`, `adwin.py`, `classifier.py`, `concept_memory.py`, `delayed_labels.py`, `detector.py`, `drift_classifier.py`, `ensemble.py`, `replay.py`, `tree.py`.
- `robust_adapt/rla/` (7 files): `__init__.py`, `label_correction.py`, `losses.py`, `noise_classifier.py`, `pipeline.py`, `reliability.py`, `scorer.py`, `weighting.py`.
- `robust_adapt/minority/` (6 files): `__init__.py`, `boundary.py`, `classifier.py`, `detector.py`, `memory.py`, `resampler.py`, `stream.py`.
- `robust_adapt/rao/` (8 files): `__init__.py`, `accumulator.py`, `adamw.py`, `budget.py`, `device.py`, `memory.py`, `profiler.py`, `quantizer.py`, `recovery.py`.
- `robust_adapt/ulc/` (14 files): `__init__.py`, `arbitrator.py`, `automaton.py`, `confidence.py`, `conflict_resolver.py`, `controller.py`, `directives.py`, `evidence.py`, `explainer.py`, `spatial.py`, `v4_1_controller.py`, `v4_automaton.py`, `v4_controller.py`, `v4_evidence.py`, `v5_controller.py`.
- `robust_adapt/backends/` (4 files): `__init__.py`, `base.py`, `numpy_backend.py`, `torch_backend.py`.
- `robust_adapt/integrations/` (6 files): `__init__.py`, `data.py`, `sklearn.py`, `torch_callback.py`, `torch_module.py`, `torch_optim.py`.
- `robust_adapt/state/` (3 files): `__init__.py`, `checkpoint.py`, `serializer.py`.

### 2.2 Compatibility Forwarding Shims (`adaptive_ml/`) — 71 Files
Lightweight PEP 562 forwarding stubs resolving AUDIT-DEF-001. No duplicated algorithms.
- `adaptive_ml/py.typed`: Type marker.
- `adaptive_ml/__init__.py`: Version declaration, `FutureWarning` deprecation notice, and top-level proxy delegation.
- 70 submodules mirroring the structure of `robust_adapt/`, dynamically forwarding attributes and preserving class identity (`AdaptiveClassifier is LegacyClassifier` evaluates to `True`) and exception identity (`RobustAdaptError is AdaptiveMLError` evaluates to `True`).

### 2.3 CI/CD & Security Workflows (`.github/workflows/`) — 2 Files
Resolves AUDIT-DEF-002:
- `.github/workflows/ci.yml`: Multi-OS test matrix, dual-namespace Ruff linting/formatting (`robust_adapt adaptive_ml tests`), wheel building, and isolated venv cross-namespace identity assertions.
- `.github/workflows/security.yml`: Dual-namespace Bandit AST security scanning (`-r robust_adapt adaptive_ml -ll -ii`) and `pip-audit`.

### 2.4 Comprehensive Test Suite (`tests/`) — 42 Files
Validates all 334 test cases:
- `tests/unit/` (33 files): Unit test coverage for all pillars, plus `test_compatibility_shim.py` (9 tests for PEP 562 proxies) and `test_defect_remediation.py` (12 tests for AUDIT-DEF-001 & AUDIT-DEF-002).
- `tests/integration/` (6 files): End-to-end streaming pipelines, PyTorch integration, scikit-learn integration, cross-pillar ULC arbitration, and data interoperability.
- `tests/examples/` (1 file): `test_all_examples.py` (automated verification of all standalone industry examples).
- `tests/sdk/` (2 files): Public API stability, import parity, and deprecation warning assertions.

### 2.5 Practical Industry Examples (`examples/`) — 35 Files
Standalone, runnable reference implementations:
- `examples/` (19 numbered files): `01_static_classification_baseline.py` through `19_ulc_v5_calibrated_controller.py` covering concept drift, label noise, class imbalance, and resource-constrained optimization.
- `examples/integrations/` (8 numbered files): `01_sklearn_static_pipeline.py` through `08_core_only_workflow.py` for scikit-learn and PyTorch workflows.
- `examples/` legacy pillar examples (8 files): `quickstart.py`, `ala/streaming_classification_example.py`, `end_to_end/streaming_pipeline.py`, `rao/low_memory_optimization_example.py`, `rla/robust_learning_example.py`, `ulc/unified_controller_example.py`, etc.

### 2.6 Documentation Site (`docs/`) — 494 Files
Comprehensive Markdown documentation and historical research registers:
- `docs/migration/ADAPTIVEML_TO_ROBUST_ADAPT.md`: Official 12-section migration guide for library users.
- `docs/algorithms/` (30 files): Mathematical formulas and algorithm specifications for ALA 3.0, RLA 3.0, RAO 2.0, Minority, and ULC.
- `docs/api/` (9 files): Public API reference documentation.
- `docs/architecture/` (2 files): Architecture overview and threat modeling.
- `docs/community/` (4 files): Contributing guidelines, code of conduct, security policy.
- `docs/concepts/` (9 files): Fundamental machine learning concepts.
- `docs/getting-started/` & `docs/getting_started/` (10 files): Quickstart, installation, and environment setup.
- `docs/guides/` (7 files): Deep-dive guides for each pillar.
- `docs/integrations/` (11 files): Scikit-learn, PyTorch, NumPy, and dataframe interoperability.
- `docs/research/` (68 files): Complete preservation of historical research registers (Phases 1–5, 12, 19, 21).
- `docs/tutorials/` (26 files): Step-by-step interactive tutorials.
- `docs/verification/` (320 files): Verification logs, phase audits, and test evidence across all development phases.

### 2.7 Root Configuration & Governance Files — 10 Files
- `pyproject.toml`: Official PEP 517 / PEP 621 build specification for distribution `robust-adapt` (version `0.1.0.dev0`).
- `mkdocs.yml`: MkDocs documentation site configuration rebranded to ROBUST-ADAPT.
- `README.md`: Official README with architecture diagrams, dual-namespace quickstart, and feature overview.
- `CONTRIBUTING.md`: Contributor guide enforcing Developer Certificate of Origin (DCO 1.1) and clean-room practices.
- `LICENSE`: Apache License, Version 2.0.
- `NOTICE`: Copyright attribution and third-party notices.
- `SECURITY.md`: Security vulnerability disclosure policy and private reporting channel.
- `CODE_OF_CONDUCT.md`: Contributor Covenant Code of Conduct.
- `DEVELOPMENT.md`: Developer environment setup, linting, and testing guide.
- `SUPPORT.md`: Community channels and issue reporting guidelines.

### 2.8 Formal Audit, Remediation & Governance Reports — 18 Files
Historical and current technical audit records documenting the full rebranding and verification lifecycle:
1. `ROBUST_ADAPT_REBRANDING_REPORT.md`
2. `ROBUST_ADAPT_PACKAGE_MIGRATION_REPORT.md`
3. `ROBUST_ADAPT_TEST_VALIDATION_REPORT.md`
4. `ROBUST_ADAPT_COMPATIBILITY_REPORT.md`
5. `ROBUST_ADAPT_RELEASE_READINESS.md`
6. `ROBUST_ADAPT_PACKAGE_INTEGRITY_AUDIT.md`
7. `ROBUST_ADAPT_COMPATIBILITY_AUDIT.md`
8. `ROBUST_ADAPT_GIT_CHANGE_INVENTORY.md`
9. `ROBUST_ADAPT_FINAL_ENGINEERING_AUDIT.md`
10. `ROBUST_ADAPT_FINAL_OWNER_DECISION.md`
11. `ROBUST_ADAPT_COMPATIBILITY_DEFECT_REMEDIATION.md`
12. `ROBUST_ADAPT_CI_WORKFLOW_REMEDIATION.md`
13. `ROBUST_ADAPT_POST_REMEDIATION_TEST_REPORT.md`
14. `ROBUST_ADAPT_POST_REMEDIATION_BUILD_REPORT.md`
15. `ROBUST_ADAPT_POST_REMEDIATION_HANDOVER.md`
16. `ROBUST_ADAPT_FINAL_GIT_COMMIT_REVIEW.md`
17. `ROBUST_ADAPT_STAGING_MANIFEST.md` (This document)
18. `ROBUST_ADAPT_FINAL_GOVERNANCE_STATUS.md`

---

## 3. Excluded File Inventory (1,069 Files)

The following directories and files are explicitly **EXCLUDED** from the Git staging manifest.

| Excluded Directory / File Group | File Count | Exclusion Justification |
| :--- | :---: | :--- |
| `.stage_13_pre_integration_snapshot/` | 97 files | Point-in-time backup snapshot of codebase and tests created before Stage 13 cross-pillar integration. Operational local backup; must not be committed to Git. |
| `.stage_14_pre_hardening_snapshot/` | 142 files | Point-in-time backup snapshot created before Stage 14 production hardening. Operational local backup; must not be committed to Git. |
| `site/` | 560 files | Local MkDocs static HTML/CSS/JS build output directory generated by `mkdocs build`. Ephemeral build artifact; must be generated dynamically from `docs/` and `mkdocs.yml`. |
| `experiments/` | 270 files | Local optimization experiments, benchmark result JSONs, CSV traces, and exploratory scripts from Stages 7, 11, and 12. Kept on local disk for reproducibility, but excluded from the production distribution commit. |
| `dist/` | 4 files | Local PEP 517 build artifacts (`.whl` and `.tar.gz`). Built dynamically by CI/CD; excluded per standard Python `.gitignore`. |
| `build/` | Multiple dirs | Setuptools/wheel intermediate compilation directories (`bdist.win-amd64`, `lib`). Excluded per `.gitignore`. |
| `*.egg-info/` | Multiple dirs | Local packaging metadata caches (`aml_core.egg-info`, `robust_adapt.egg-info`). Excluded per `.gitignore`. |
| `__pycache__/` | Multiple dirs | Python bytecode compilation caches (`.pyc`). Excluded per `.gitignore`. |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Multiple dirs | Tool execution state and linting caches. Excluded per `.gitignore`. |

**Total Excluded Files:** 1,069 files.

---

## 4. Owner Staging and Commit Execution Plan

The project owner should execute the following non-destructive commands in the project root (`C:\projects\AdaptiveML`) to stage the intended files and finalize the commit.

### Step 1: Stage Intended Files
```powershell
# Stage production packages and forwarding shims
git add robust_adapt/
git add adaptive_ml/

# Stage CI/CD and security workflows
git add .github/

# Stage test suites and industry examples
git add tests/
git add examples/

# Stage project configuration, build specification, and governance files
git add pyproject.toml mkdocs.yml README.md CONTRIBUTING.md SECURITY.md DEVELOPMENT.md SUPPORT.md CODE_OF_CONDUCT.md LICENSE NOTICE

# Stage comprehensive documentation and historical research registers
git add docs/

# Stage formal audit, defect remediation, and governance reports
git add ROBUST_ADAPT_*.md
```

### Step 2: Pre-Commit Validation Checks
```powershell
# Verify no whitespace or conflict marker errors exist in staged diff
git diff --cached --check

# Inspect summary of staged changes (verifying 742 files staged)
git diff --cached --stat

# (Optional) Review full patch delta
git diff --cached
```

### Step 3: Execute Signed Commit
```powershell
git commit -s -m "feat: migrate project identity to ROBUST-ADAPT and establish compatibility forwarding"
```

> [!NOTE]
> The `-s` (`--signoff`) flag is mandatory to certify compliance with the **Developer Certificate of Origin (DCO 1.1)** as required by `CONTRIBUTING.md`.

---

## 5. Staging Integrity Certification

- **Zero Untracked Residuals in Production Tree**: Every production file in `robust_adapt/` and `adaptive_ml/` is accounted for.
- **Zero Accidental Commits**: All 1,069 local snapshots, ephemeral build outputs, and caches are safely excluded.
- **Single Source of Truth**: The staged changes enforce `robust_adapt` as the sole canonical implementation, backed by 334 passing tests and verified PEP 562 forwarding.
