# ROBUST-ADAPT Local Development & Engineering Guide

This guide describes how to set up, build, test, and contribute to **ROBUST-ADAPT** (`robust-adapt`).

---

## 1. Environment Setup

### 1.1 Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14 (Python 3.14 recommended).
- Git.
- C/C++ compiler is **not** required for core engine development (pure Python and NumPy).

### 1.2 Virtual Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/robust-adapt/robust-adapt.git
cd robust-adapt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development and documentation dependencies
pip install -e ".[dev,docs,all]"
```

---

## 2. Test Execution & Coverage

ROBUST-ADAPT uses `pytest` for all unit, integration, and property-based tests:

```bash
# Run all unit tests
pytest tests/ -v

# Run tests with code coverage report
pytest tests/ -v --cov=robust_adapt --cov-report=term-missing

# Run only integration tests
pytest tests/integrations/ -v
```

---

## 3. Code Style & Linters

ROBUST-ADAPT enforces strict type safety and code quality:

```bash
# Type checking via mypy
mypy robust_adapt/

# Code formatting and linting via ruff
ruff check robust_adapt/
ruff format --check robust_adapt/
```

---

## 4. Documentation Building

Documentation is authored in Markdown and built using MkDocs Material:

```bash
# Start live development documentation server with instant reload
mkdocs serve

# Verify strict build with zero warnings and zero broken links
mkdocs build --strict
```

---

## 5. Architectural Invariants for Contributors

When writing code for ROBUST-ADAPT, please maintain these strict rules:
1. **Core Zero-Dependency Guarantee:** Modules in `robust_adapt.ala`, `robust_adapt.rla`, `robust_adapt.minority`, `robust_adapt.rao`, `robust_adapt.ulc`, and `robust_adapt.core` must depend only on standard library and `numpy`.
2. **Framework Isolation:** PyTorch and Scikit-Learn imports belong strictly inside `robust_adapt.integrations` or inside runtime dependency guards (`try: import torch except ImportError:`).
3. **Zero-Pickle Invariant:** Never introduce `pickle.dump`, `pickle.load`, or `torch.save` without SafeTensors.
4. **Zero-PII Telemetry:** Telemetry and diagnostic registries must never log raw feature vectors or unaggregated patient/user identifiers.
