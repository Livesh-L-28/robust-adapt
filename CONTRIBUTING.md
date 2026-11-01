# Contributing to AdaptiveML (`aml-core`)

Thank you for your interest in contributing to AdaptiveML! 

AdaptiveML is an open-source Python machine-learning library dedicated to adaptive, robust, and resource-efficient learning. We welcome code contributions, documentation improvements, issue reports, and research discussions.

---

## 1. Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all members of the community with respect, constructive feedback, and professionalism.

---

## 2. Developer Certificate of Origin (DCO 1.1)

To ensure that all code in AdaptiveML has verifiable legal provenance and complies with our Apache-2.0 licensing, we require the standard **Linux Foundation Developer Certificate of Origin (DCO), Version 1.1**.

Every commit must include a `Signed-off-by` line in its commit message:

```bash
git commit -s -m "feat(ala): add sliding window variance filter to ADWIN"
```

Which produces:

```
Signed-off-by: Jane Developer <jane.developer@example.com>
```

By adding this line, you certify that:
1. The contribution was created in whole or in part by you, and you have the right to submit it under the Apache-2.0 license; OR
2. The contribution is based on previous work covered under an appropriate permissive open-source license; OR
3. The contribution was provided directly to you by a person who certified points 1 or 2.

---

## 3. Clean-Room Implementation Rules

AdaptiveML maintains strict clean-room implementation governance:
- **No Proprietary Code**: Do not submit code derived from proprietary libraries, past employment under restrictive IP agreements, or decompiled binary sources.
- **Academic Grounding**: Algorithms must be implemented from published academic papers, patents in the public domain, or original derivations.
- **Traceable Citations**: Always document the mathematical reference (DOI / arXiv ID) in the module docstring.

---

## 4. Development Setup

### 4.1 Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Git.
- Virtual environment tool (`venv`, `conda`, or `virtualenv`).

### 4.2 Local Installation
```bash
# Clone the repository
git clone https://github.com/adaptiveml/adaptiveml.git
cd adaptiveml

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development and integration extras
python -m pip install -e ".[dev,all]"
```

---

## 5. Coding Standards & Quality Gates

All pull requests must satisfy the following criteria:

1. **Type Annotations**: 100% strict type hints across all function and class definitions.
2. **Minimal Core Dependencies**: Core modules in `adaptive_ml/core/`, `ala/`, `rla/`, `rao/`, and `ulc/` must depend **strictly** on standard library and `numpy`.
3. **Lazy Framework Integrations**: Integrations in `adaptive_ml/integrations/` must use lazy imports and fail gracefully with informative error messages when optional frameworks are absent.
4. **Testing**: All features must include comprehensive unit and property tests under `tests/`. Run the full test suite before submitting:
   ```bash
   pytest tests/
   ```
5. **No Dangerous Deserialization**: Never use Python's `pickle` on untrusted external data. Use `Safetensors` or structured JSON.

---

## 6. Pull Request Process

1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/my-feature-name
   ```
2. Write clean, modular code with accompanying unit tests and docstrings.
3. Verify that all 44 regression tests pass:
   ```bash
   pytest tests/ -v
   ```
4. Commit with DCO sign-off (`git commit -s`).
5. Open a Pull Request on GitHub. Clearly describe the motivation, mathematical references, and test validation results.

---

## 7. Reporting Issues

- **Bug Reports**: Open an issue detailing the Python version, operating system, exact code snippet to reproduce, and traceback.
- **Feature Requests**: Open an issue describing the mathematical rationale, practical use case, and proposed API design.
- **Security Vulnerabilities**: Please review our [Security Policy](SECURITY.md) for responsible disclosure. Do not file public issues for active security vulnerabilities.
