# Contributing to AdaptiveML (`aml-core`)

Thank you for your interest in contributing to AdaptiveML!

AdaptiveML is an open-source Python machine-learning library dedicated to adaptive, robust, and resource-efficient learning. We welcome code contributions, documentation improvements, issue reports, and research discussions.

---

## 1. Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](code-of-conduct.md). Please treat all members of the community with respect, constructive feedback, and professionalism.

---

## 2. Developer Certificate of Origin (DCO 1.1)

To ensure that all code in AdaptiveML has verifiable legal provenance and complies with our Apache-2.0 licensing, we require the standard **Linux Foundation Developer Certificate of Origin (DCO), Version 1.1**.

Every commit must include a `Signed-off-by` line in its commit message:

```bash
git commit -s -m "feat(ala): add sliding window variance filter to ADWIN"
```

Which produces:

```text
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
- Virtual environment tool (`venv`, `uv`, or `conda`).

### 4.2 Local Installation
```bash
# Clone the repository
git clone https://github.com/adaptiveml/adaptiveml.git
cd adaptiveml

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install editable development build with all test and documentation tools
pip install -e ".[dev,docs,all]"
```

### 4.3 Running Test Suite
```bash
# Run complete test suite with coverage
pytest tests/ -v --cov=adaptive_ml
```

### 4.4 Documentation Preview
```bash
# Launch live documentation preview server
mkdocs serve
```
