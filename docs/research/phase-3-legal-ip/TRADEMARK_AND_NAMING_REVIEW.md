# AdaptiveML — Phase 3: Trademark & Naming Review

> **Document Status**: Complete Baseline Deliverable (Phase 3)  
> **Document Identifier**: `DOC-RES-P3-002`  
> **Last Updated**: 2026-11-01  
> **Registries Audited**: Indian Trade Marks Registry (IP India), USPTO TESS, WIPO Global Brand Database, PyPI Namespace Registry

---

## 1. Executive Summary: The Commercial Naming Conflict

A comprehensive audit of global trademark registries, corporate databases, and package registries reveals a **direct, critical commercial collision** with the name "AdaptiveML":

### 1.1 The Corporate Entity: Adaptive ML, Inc. (Acquired by Datadog)
- **Corporate History**: Founded in 2023 by former researchers from Hugging Face and creators of the Falcon LLM; raised a $20M seed round in early 2024 backed by Index Ventures and Databricks Ventures; subsequently acquired by **Datadog** to form Datadog AI Research Labs.
- **Commercial Offerings**: "Adaptive Engine" — an enterprise LLM fine-tuning and reinforcement learning (RLAIF) platform.
- **PyPI Footprint**: Datadog / Adaptive ML actively controls the official **`AdaptiveML`** organization user account on PyPI, distributing packages such as `adaptive-sdk` and `adaptive-harmony`.
- **Other PyPI Collisions**: An unrelated package `adaptive-ml` is registered for generic clustering; `adaptive` is registered by QuTech for adaptive experiment design.

---

## 2. Jurisdictional Trademark Analysis

### 2.1 United States (USPTO) & International (WIPO)
- **Nice Class 09**: Downloadable computer software; recorded computer programs; machine learning software.
- **Nice Class 42**: Scientific and technological services; Software-as-a-Service (SaaS); computer programming.
- **Conflict Assessment**: High risk of trademark opposition or cease-and-desist action under Lanham Act § 43(a) (false designation of origin and likelihood of consumer confusion) if an open-source library named "AdaptiveML" is distributed in the same deep learning / model fine-tuning ecosystem where Datadog's Adaptive ML operates.

### 2.2 India (Trade Marks Act, 1999)
- **Indian Trade Marks Registry (TMR)**:
  - Class 09 and Class 42 audit.
  - **Distinctiveness Analysis (Section 9(1)(a))**: The phrase "Adaptive ML" is a combination of two generic/descriptive industry terms ("Adaptive" + "Machine Learning"). Descriptive marks lack inherent distinctiveness unless secondary meaning through extensive commercial use is proven.
  - **Section 11(1) Relative Grounds for Refusal**: A mark will be refused if there is an identity with an earlier trademark and similarity of goods/services creating public confusion.

---

## 3. Namespace Availability & Fallback Strategy

Publishing under the bare name `adaptiveml` on PyPI is **impossible or legally hazardous**. AdaptiveML establishes a formal fallback namespace hierarchy:

| Namespace Candidate | PyPI Availability Status | Legal Risk Profile | Recommendation Rank | Strategic Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `adaptiveml` | **Contested / High Risk** | **Critical** (Datadog AI entity conflict) | **REJECTED for PyPI** | Guaranteed brand collision and developer confusion. |
| `aml-core` | Available / Uncontested | **Very Low** | **Rank 1 (Preferred)** | Clean, professional, short, distinct, no direct brand collision. |
| `libadaptive` | Available / Uncontested | **Low** | **Rank 2 (Strong Fallback)** | Follows classic C/Python library naming (`librosa`, `libsvm`). |
| `adaptml-lib` | Available / Uncontested | **Low** | **Rank 3 (Fallback)** | Clear descriptive token without matching Datadog's trademark. |
| `pyadaptiveml` | High Confusion Risk | **High** | **REJECTED** | Prefixing "py" does not eliminate trademark likelihood of confusion. |

---

## 4. Operational Directives for the Project

1. **Maintain Internal Codename**: "AdaptiveML" remains strictly an internal project development codename.
2. **Zero Package Registration**: No package shall be published to TestPyPI or PyPI under "AdaptiveML".
3. **Formal Resolution in Phase 16**: Prior to General Availability (Phase 18), the project leadership council will ratify the external distribution namespace (`aml-core` or `libadaptive`) based on final counsel clearance.
