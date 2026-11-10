# PHASE 20 DELIVERABLE 01 — DEVELOPER CONTRIBUTION GUIDE
## Contributor Onboarding, Development Environment Setup, Pull Request Lifecycle, and Testing Standards

**Document Identifier:** `docs/ecosystem/phase_20/DEVELOPER_CONTRIBUTION_GUIDE.md`<br>
**Phase:** 20 — Ecosystem Growth<br>
**Baseline Git Commit:** `master @ 67e9ef1b347ca223828a1f225e85e35a086a1f30`<br>
**Date:** 2026-11-06<br>
**Auditor:** Developer Experience Architect & Open-Source Community Lead<br>

---

## 1. Welcome & Open-Source Philosophy

Welcome to the AdaptiveML developer community. We are building a high-efficiency, mathematically grounded continual learning library designed to make adaptive artificial intelligence robust, resource-aware, and accessible on commodity hardware.

We welcome contributions across algorithmic innovation, framework adapters, performance profiling, documentation, and defect remediation.

---

## 2. Contributor Onboarding & Local Environment Setup

### 2.1 Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Git (Version 2.30+).
- C/C++ compiler is **not** strictly required for core streaming tabular modules; pure-Python and NumPy backends are provided.

### 2.2 Local Repository Setup
```bash
# Clone the repository
git clone https://github.com/[org]/AdaptiveML.git
cd AdaptiveML

# Create and activate an isolated virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install the package in editable mode with development dependencies
pip install -e ".[dev,test,docs]"
```

---

## 3. Coding Standards & Architectural Conventions

All code contributed to AdaptiveML must adhere to strict software engineering standards:

1. **Strict Type Annotations:** Every public class, method, function signature, and return value must include comprehensive Python type hints (`typing`).
2. **Pillar Decoupling:** Modules within `adaptive_ml/ala/`, `adaptive_ml/rla/`, `adaptive_ml/rao/`, and `adaptive_ml/minority/` must remain functional independently without requiring the `ulc` controller.
3. **Zero Arbitrary Pickle:** Never introduce `pickle.load` or `pickle.loads` in persistence or serialization pathways. Use `safetensors` or structured JSON.
4. **Defensive Input Validation:** Validate array shapes, reject non-finite inputs (NaNs, Infs), and check budget constraints before allocating memory.
5. **No Undocumented Cloud Dependencies:** Do not add mandatory cloud dependencies (AWS, GCP, Azure) to the core distribution.

---

## 4. Testing Standards & Quality Gates

Every pull request must pass the local test suite prior to review:

```bash
# Run full unit test suite
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run example execution tests
pytest tests/examples/

# Run static type checks and linting
mypy adaptive_ml/
ruff check adaptive_ml/
```

### Pull Request Acceptance Criteria:
- [ ] 100% of existing tests pass.
- [ ] New features include corresponding unit tests in `tests/unit/`.
- [ ] Complex multi-pillar interactions include integration tests in `tests/integration/`.
- [ ] Code passes static analysis without type errors or lint warnings.
- [ ] Public API methods are documented with Google-style docstrings.

---

## 5. Issue & Pull Request Templates

### 5.1 Bug Report Template
```markdown
### Bug Description
A clear and concise description of the defect.

### Reproduction Steps
1. Execute `from robust_adapt.ala import ...`
2. Pass streaming batch `...`
3. Error observed: `...`

### Expected Behavior
A concise description of what should happen.

### Environment
- Python Version:
- OS:
- Package Version:
```

### 5.2 Pull Request Checklist
- [ ] Feature branch created from `master`.
- [ ] Unit tests added/updated.
- [ ] Documentation updated in `docs/`.
- [ ] Verified local pass of `pytest`.
