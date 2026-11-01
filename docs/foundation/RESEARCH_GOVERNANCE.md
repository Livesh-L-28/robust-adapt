# AdaptiveML: Research Governance & Evidence Standards

> **Document Status**: Approved Baseline (Phase 0 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-FDN-005`  
> **Last Updated**: 2026-11-01  
> **Target Audience**: Researchers, scientific advisory board, core engineers, external scientific contributors

---

## 1. Philosophical Foundations & Code of Scientific Integrity

The field of machine learning research is frequently burdened by unverified novelty claims, irreproducible benchmarks, selective data pruning, and exaggerated marketing. 

The core mission of **AdaptiveML** demands uncompromised scientific discipline. Every line of algorithmic code, mathematical formulation, and benchmark report must adhere to rigorous research governance.

---

## 2. The Ten Inviolable Research Governance Rules

Every contributor, maintainer, and scientific researcher working on AdaptiveML must comply with these ten mandatory rules:

### Rule 1: Strict Separation of Established Facts from Hypotheses
- Any scientific assertion must be explicitly categorized as an **Established Fact** (supported by verified peer-reviewed literature or formal mathematical proof) or a **Working Hypothesis** (an assumption or conjecture currently under empirical investigation).
- Language in documentation and papers must not conflate theoretical expectations with demonstrated empirical reality.

### Rule 2: Mandatory Citation of Original Research Sources
- No algorithmic concept, loss formulation, or optimization technique may be introduced into the repository without full bibliographic attribution to its original academic literature.
- Citations must include: Author(s), Title, Conference/Journal, Year, and DOI / ArXiv identifier. Derivative implementations must explicitly cite the foundational papers (e.g., Robbins-Monro, Polyak, Duchi et al., Kingma & Ba, Kirkpatrick et al., Zhang & Sabuncu, Northcutt et al.).

### Rule 3: Algorithmic Novelty Claim Restriction
- No author, pull request, or documentation page may claim "algorithmic novelty" without a formal, documented prior-art search across IEEE, ACM, NeurIPS, ICML, ICLR, and patent databases.
- Prior-art investigations are formally conducted during **Phase 2 (Novelty & Prior-Art Research)** and **Phase 4 (Comprehensive Literature Review)**. Until both phases are completed and signed off by the Technical Research Lead, all proposed algorithms are treated as research hypotheses or engineering adaptations.

### Rule 4: Algorithmic Superiority Claim Restriction
- No contributor or publication may assert that an AdaptiveML algorithm is "superior", "state-of-the-art", "faster", or "more accurate" than an existing baseline without:
  1. A statistically powered benchmark suite across standard public datasets.
  2. A minimum of 5 independent randomized seeds with reported standard errors / confidence intervals.
  3. Paired two-tailed statistical significance testing ($\alpha = 0.01$).
  4. Fully reproducible scripts, seeds, and hardware environment specifications documented in `benchmarks/`.

### Rule 5: Compulsory Preservation of Negative Experimental Results
- If an algorithm fails to converge, demonstrates inferior sample efficiency, underperforms standard baselines (e.g., standard Adam or standard ERM), or breaks under specific distributional shifts, this outcome **must not be suppressed or deleted**.
- Negative results must be cataloged in `docs/research/NEGATIVE_RESULTS_REGISTRY.md` with detailed analysis of the failure modes. Understanding failure regimes is as scientifically valuable as positive results.

### Rule 6: Prohibition Against Discarding Rare Samples
- In Pillar 2 (RLA) and Pillar 1 (ALA), algorithms must not treat difficult-to-learn or minority-class samples as "noise" or "outliers" simply because they exhibit high initial training loss.
- Algorithms must preserve valid tail distributions and extreme minority classes. Filtering mechanisms must be evaluated specifically for class-imbalance bias.

### Rule 7: Strict Independence of Algorithm Pillars
- Pillar 1 (ALA), Pillar 2 (RLA), and Pillar 3 (RAO) must remain strictly independent and usable in complete isolation.
- No algorithmic contribution in one pillar may introduce runtime imports, dependencies, or required configurations from another pillar. Synergies between pillars may only be explored through the Unified Learning Controller (ULC).

### Rule 8: Prohibition Against Mandatory Framework Dependencies
- Core algorithmic implementations must run using only Python standard library and NumPy.
- PyTorch, scikit-learn, SciPy, or other external frameworks must never be made mandatory runtime dependencies of the core package. Any framework-specific integrations must reside in dedicated optional adapter modules (`adaptiveml.integrations.*`) guarded by lazy import hooks.

### Rule 9: Prohibition Against Telemetry, Cloud Lock-In, or Mandatory Remote Services
- The codebase must never introduce phone-home telemetry, usage metrics tracking, remote license verification, or mandatory cloud infrastructure dependencies.
- Every algorithm must be executable entirely offline in an air-gapped, local-first environment on commodity CPU hardware.

### Rule 10: Legal, IP, and Trademark Findings Preliminary Disclaimer
- All findings regarding patents, copyright provenance, trademark availability, and licensing compatibility recorded in Phase 0 or subsequent technical documents are **preliminary engineering assessments**.
- No legal finding is binding until formally reviewed and ratified by qualified intellectual property legal counsel during Phase 3 and Phase 16.

---

## 3. Experimental Reproducibility Protocol

To ensure 100% scientific reproducibility, all experiments conducted in Phase 12 and beyond must adhere to the standardized Reproducibility Checklist:

```
+-------------------------------------------------------------------------------+
|                       REPRODUCIBILITY ARTIFACT BUNDLE                         |
+---------------------------------------+---------------------------------------+
| 1. Exact Environment Lockfile         | poetry.lock / requirements-lock.txt   |
| 2. Seed Specification                 | Array of explicit integer seeds       |
| 3. Raw Data Manifest                  | SHA-256 hashes of input datasets      |
| 4. Hardware & OS Telemetry            | CPU model, RAM, OS kernel, NumPy BLAS |
| 5. Unprocessed Raw Metrics            | JSON / CSV logs of all step metrics   |
| 6. Statistical Analysis Script        | R / Python script computing CI and p  |
+---------------------------------------+---------------------------------------+
```

### 3.1 Random Seed Control
- All benchmark drivers must execute across a fixed array of seeds: `[42, 1337, 2026, 9999, 88888]`.
- No global `random.seed()` or `np.random.seed()` pollution is permitted. Benchmarks must pass seed-specific `np.random.Generator` instances directly to estimators.

### 3.2 Hardware Environment Logging
- Every benchmark log must automatically record:
  - CPU model string and core count (e.g., `Intel Core i7-12700H, 14 cores` or `Apple M2 Pro, 10 cores`).
  - System physical RAM and swap configuration.
  - Operating system release and kernel version.
  - BLAS/LAPACK runtime library linked to NumPy (`numpy.show_config()`).

---

## 4. Enforcement & Review Process

- Any pull request violating these governance rules will be blocked by the Technical Research Lead.
- Violations of Rule 5 (suppression of negative results) or Rule 4 (unverified superiority claims) represent scientific misconduct under this charter and will require immediate retraction or remediation.

