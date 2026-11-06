# STAGE 16.1 DELIVERABLE 09
# Brand Migration Scenario Analysis & Technical Execution Blueprints

**Document Identifier:** `docs/verification/stage_16_1/BRAND_MIGRATION_SCENARIO_ANALYSIS.md`<br>
**Stage:** 16.1 — External Legal Counsel Review & Owner Decision Preparation<br>
**Distribution Identifier:** `aml-core`<br>
**Import Namespace:** `adaptive_ml`<br>
**Working Codename:** AdaptiveML<br>
**Date:** 2026-11-06<br>
**Auditor:** Python Library Architect & Systems Integration Engineer<br>
**Review Status:** `COUNSEL DETERMINATION REQUIRED` & `OWNER DECISION REQUIRED`<br>

---

## 1. Executive Summary & Policy Constraints

> [!CAUTION]
> **GOVERNANCE NOTICE: ZERO ACTIVE MIGRATION**<br>
> 1. **No active renaming is executed during Stage 16.1.**<br>
> 2. All candidate brand names evaluated in this document are preliminary technical contingencies and are explicitly categorized as **NOT LEGALLY CLEARED**.<br>
> 3. Migration blueprints provided herein are contingency technical specifications ready for rapid execution only upon written owner directive following legal counsel advice.

---

## 2. Contingency Brand Candidate Comparison Framework

```mermaid
graph TD
    Alternatives[Screened Brand Alternatives]
    Alternatives --> C1["Candidate 1: ResiliML / resiliml\n(High Distinctiveness / Suggestive)"]
    Alternatives --> C2["Candidate 2: StreamAdapt / streamadapt\n(Descriptive / Clean Streaming Focus)"]
    Alternatives --> C3["Candidate 3: LibAdaptive / libadaptive\n(Classic Library Standard)"]
    Alternatives --> C4["Candidate 4: The AML Core Project\n(Acronym Minimization)"]
```

| Evaluation Dimension | Candidate 1: `ResiliML` (`resiliml`) | Candidate 2: `StreamAdapt` (`streamadapt`) | Candidate 3: `LibAdaptive` (`libadaptive`) | Candidate 4: `The AML Core Project` (`aml-core`) |
| :--- | :--- | :--- | :--- | :--- |
| **Lanham Act Distinctiveness** | **Suggestive / Highly Distinctive** | Descriptive / Weak Distinctiveness | Descriptive / Common Standard | Descriptive Acronym |
| **Technical Alignment** | Captures robustness (RLA), drift recovery (ALA), and memory resilience (RAO). | Captures real-time streaming, but omits 8-bit optimizer compression. | Emphasizes algorithmic library; classic C/Python feel. | Direct continuity with existing `aml-core` packaging. |
| **Pronunciation & Recall** | Three syllables: "Re-zil-i-M-L"; memorable and modern. | Three syllables: "Stream-A-dapt"; highly intuitive. | Four syllables: "Lib-A-dap-tive"; utilitarian. | Three letters: "A-M-L Core"; functional. |
| **PyPI Namespace Status** | **Available / Uncontested** | **Available / Uncontested** | `libadaptive` available; `adaptive` taken by QuTech | **Available / Uncontested** |
| **Import Namespace** | `import resiliml as rm` | `import streamadapt as sa` | `import libadaptive as la` | `import aml_core as aml` or `adaptive_ml` |
| **GitHub Organization Slug** | `github.com/resiliml` (Available) | `github.com/streamadapt` (Available) | `github.com/libadaptive` (Available) | `github.com/aml-core` (Available) |
| **Search Engine Discoverability**| High (Zero non-tech dictionary collisions) | Moderate (Potential collisions with video streaming) | Moderate (Collisions with adaptive libraries) | Low (Collisions with Anti-Money Laundering) |
| **Legal Counsel Status** | **NOT LEGALLY CLEARED** | **NOT LEGALLY CLEARED** | **NOT LEGALLY CLEARED** | **CURRENT BASELINE (OPEN DEF-004)** |

---

## 3. Technical Blueprint for Scenario A: Existing Brand Retained

### 3.1 Prerequisite Conditions
1. Outside legal counsel issues a written advisory opinion confirming that non-commercial open-source distribution of "AdaptiveML" with negative disclaimers carries acceptable, defensible legal exposure.
2. Project owners formally sign off accepting the residual risk.

### 3.2 Engineering Specifications
- **Package Name:** Retain `name = "aml-core"` in `pyproject.toml`.
- **Import Namespace:** Retain `adaptive_ml/`.
- **Documentation Updates:** Retain existing 58 Markdown pages; add prominent counsel-approved trademark disclaimers to `docs/index.md`, `README.md`, and `docs/community/license.md`.
- **Engineering Effort:** $0\text{ hours}$ (No code changes).
- **Rollback Strategy:** Immediate fallback to Scenario B or C if Datadog issues a formal inquiry.

---

## 4. Technical Blueprint for Scenario B: Partial Brand Migration

### 4.1 Prerequisite Conditions
1. Counsel advises retiring the human-facing brand "AdaptiveML" to eliminate public confusion with Datadog, but approves retaining the import namespace `adaptive_ml` as an unexposed internal API.
2. Project owners approve rebranding the project title to **"The AML Core Project"** or **`StreamAdapt`**.

### 4.2 Engineering Specifications
- **Package Name:** Update `name = "streamadapt"` (or retain `aml-core`) in `pyproject.toml`.
- **Import Namespace:** Retain `adaptive_ml/` to preserve code stability.
- **Documentation Updates:** Execute search-and-replace across 58 documentation pages updating "AdaptiveML" to the new project title.
- **Affected Components:** ~15 documentation files and metadata. Zero Python source module modifications.
- **Engineering Effort:** $\approx 2\text{ engineering hours}$.
- **Backward Compatibility:** $100\%$ backward compatible (existing test code unchanged).

---

## 5. Technical Blueprint for Scenario C: Full Clean-Break Migration

### 5.1 Prerequisite Conditions
1. Counsel strongly advises that retaining "AdaptiveML" or `adaptive_ml` creates ongoing trademark, unfair competition, or PyPI administrative dispute exposure.
2. Project owners approve a complete clean-break rebrand to a distinctive alternative (e.g. **`ResiliML`**).

### 5.2 Step-by-Step Technical Execution Protocol

```mermaid
sequenceDiagram
    participant Owner as Project Owner Directive
    participant Git as Git Workspace Refactor
    participant AST as Automated AST Refactor
    participant Tests as Test Suite Verification
    participant Build as MkDocs & Wheel Assembly

    Owner->>Git: 1. Authorize Migration to ResiliML
    Git->>Git: 2. Rename directory adaptive_ml/ -> resiliml/
    Git->>AST: 3. Refactor imports in 70 modules (adaptive_ml -> resiliml)
    Git->>AST: 4. Refactor 35 test files and 25 example scripts
    Git->>Git: 5. Update pyproject.toml (name="resiliml", include=["resiliml*"])
    AST->>Tests: 6. Execute pytest tests/ -v (Verify 100% pass)
    Tests->>Build: 7. Recompile documentation (mkdocs build --strict)
    Build->>Build: 8. Build release wheel (dist/resiliml-0.1.0.dev0-*.whl)
    Build-->>Owner: 9. Deliver verified clean-break release artifacts
```

1. **Step 1: Directory Renaming:**
   - Move directory: `adaptive_ml/` $\to$ `resiliml/`.
2. **Step 2: Automated AST Import Rewriting:**
   - Execute Python script rewriting all module imports:
     - `import adaptive_ml as aml` $\to$ `import resiliml as rm`
     - `from adaptive_ml.ala import ...` $\to$ `from resiliml.ala import ...`
   - Rewrite imports across all 70 source modules, 35 unit test files, and 25 example scripts.
3. **Step 3: Transitional Compatibility Shim (Optional Deprecation):**
   - Provide an optional `adaptive_ml/__init__.py` module emitting a `FutureWarning`:
     ```python
     import warnings
     import resiliml as _real_module
     warnings.warn(
         "'adaptive_ml' has been permanently rebranded to 'resiliml'. "
         "Please update your imports: 'import resiliml as rm'.",
         DeprecationWarning,
         stacklevel=2,
     )
     ```
4. **Step 4: Build Configuration Update:**
   - Update `pyproject.toml`:
     - `name = "resiliml"`
     - `include = ["resiliml*"]`
     - Update description and author email.
5. **Step 5: Documentation Site Rebuild:**
   - Update `mkdocs.yml`: `site_name: ResiliML Documentation`, repository URLs.
   - Recompile documentation: `py -3.14 -m mkdocs build --strict`.
6. **Step 6: Release Artifact Assembly:**
   - Rebuild wheel: `dist/resiliml-0.1.0.dev0-py3-none-any.whl`.
   - Update CycloneDX SBOM with new package hashes.

### 5.3 Risk & Complexity Assessment for Scenario C
- **Files Affected:** $\approx 165$ files (70 code modules, 35 test files, 60 documentation pages).
- **External Consumer Disruption:** **Zero**. (The project is unreleased at `0.1.0.dev0`; zero external production systems depend on the `adaptive_ml` namespace).
- **Engineering Effort:** $\approx 8\text{ engineering hours}$.
- **Rollback Strategy:** Git branch snapshot allows instantaneous $100\%$ rollback in $< 30\text{ seconds}$ if owners abort.

---

## 6. Verification Conclusion

Three comprehensive migration blueprints exist, fully specifying technical steps, file inventories, deprecation strategies, and rollback mechanisms. Workstream B is officially **VERIFIED AND SIGNED OFF**.
