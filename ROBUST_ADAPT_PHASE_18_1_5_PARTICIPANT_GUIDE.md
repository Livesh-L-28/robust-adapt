# ROBUST-ADAPT — Phase 18.1.5: External Beta Participant Guide

**Project:** ROBUST-ADAPT (`robust-adapt`)<br>
**Target Release Candidate:** `1.0.0rc1`<br>
**Target Cohort:** External Independent Python / Machine-Learning Practitioners<br>
**Phase:** 18.1 — Gate 18.1.5: Participant Testing Guide<br>
**Status:** READY FOR DISTRIBUTION

---

## 1. Welcome to the ROBUST-ADAPT Beta Program

Thank you for volunteering to evaluate **ROBUST-ADAPT** as an independent Beta tester!

### What is ROBUST-ADAPT?
ROBUST-ADAPT is a modular Python machine-learning research library designed to enhance learning under changing data distributions (concept drift), corrupted training labels (label noise), and extreme resource constraints (CPU/edge execution).

It is designed to **complement** existing ML frameworks (NumPy, scikit-learn, PyTorch), not replace them.

**Core Philosophy:**
- **Local-first & CPU-first:** No cloud GPU clusters or external server connectivity required.
- **Minimal Dependencies:** Mandatory core requires only `numpy>=1.24.0`.
- **Zero Telemetry:** No tracking, usage analytics, or remote calls. Your data stays completely on your local workstation.

---

## 2. Getting Started in 3 Steps

### Step 1: Create an Isolated Virtual Environment
Open a terminal and create a clean Python virtual environment (Python 3.10, 3.11, 3.12, or 3.13):

```bash
# Linux / macOS
python3 -m venv robust_beta_env
source robust_beta_env/bin/activate

# Windows (PowerShell)
python -m venv robust_beta_env
.\robust_beta_env\Scripts\Activate.ps1
```

Verify your Python version:
```bash
python --version  # Must be >= 3.10 and < 3.14
```

### Step 2: Install the Release Candidate Wheel
Install the provided pre-release candidate wheel:

```bash
pip install robust_adapt-1.0.0rc1-py3-none-any.whl
```

Verify the installation:
```bash
python -c "import robust_adapt; print('Installed ROBUST-ADAPT version:', robust_adapt.__version__)"
```

### Step 3: Run the 30-Second Quick Start
Create a file named `quickstart.py` and run it:

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier

# Create synthetic streaming data
X = np.random.randn(100, 4)
y = np.random.randint(0, 2, size=100)

# Initialize and train adaptive streaming classifier
clf = AdaptiveClassifier(n_features=4, n_classes=2)
clf.fit(X, y)

# Predict on new instances
predictions = clf.predict(X[:5])
print("Adaptive Classifier Predictions:", predictions)
```

---

## 3. Recommended Evaluation Workflows

You are invited to test any or all of the five research pillars according to your interests:

### Workflow A: Adaptive Learning Algorithms (ALA)
- **Goal:** Test concept drift detection and streaming adaptation.
- **Classes to explore:** `ReliabilityWeightedADWIN`, `VectorizedHoeffdingTree`, `DelayedLabelQueue`, `ConceptMemory`.
- **Key question:** Does the classifier recover accuracy after you shift the data distribution?

### Workflow B: Robust Learning Algorithms (RLA)
- **Goal:** Test learning under severe label corruption.
- **Classes to explore:** `MultiSignalReliabilityEngine`, `SymmetricCrossEntropyLoss`, `FocalLoss`, `EvidenceBasedLabelCorrector`.
- **Key question:** Does reliability weighting protect your model when 20%–40% of labels are randomly flipped?

### Workflow C: Resource-Aware Optimization (RAO)
- **Goal:** Test 8-bit dynamic block quantization on CPU memory.
- **Classes to explore:** `BlockQuantizer`, `LowMemoryAdamW`, `DynamicResourceBudgetManager`.
- **Key question:** Does `LowMemoryAdamW` reduce optimizer state memory while maintaining convergence?

### Workflow D: Unified Learning Controller (ULC)
- **Goal:** Coordinate drift detection, noise filtering, and memory throttling simultaneously.
- **Classes to explore:** `AdaptiveLearningController`.

### Workflow E: Adaptive Minority Intelligence
- **Goal:** Maximize minority recall under extreme class imbalance (e.g. 1% minority).
- **Classes to explore:** `MinorityIntelligence20Learner`, `OnlineClassPriorTracker`.

### Workflow F: Scikit-Learn Ecosystem Integration
- **Goal:** Integrate ROBUST-ADAPT into a scikit-learn Pipeline.
- **Classes to explore:** `from robust_adapt.integrations.sklearn import ScikitLearnAdaptiveClassifier`.

---

## 4. Standardized Feedback Templates

### 4.1 Bug Report Template
If you encounter an error or unexpected crash, please share:

```text
[BUG REPORT]
Participant Identifier: (Pseudonym or Initials)
Operating System: (e.g., Ubuntu 24.04, Windows 11, macOS 14 Sonoma)
Python Version: (e.g., Python 3.11.9)
Component: (e.g., ALA / DelayedLabelQueue)

Minimal Reproducible Code:
```python
# Insert your minimal code snippet here
```

Expected Behavior:
(What you expected to happen)

Actual Behavior / Error Traceback:
(Paste the full Python error traceback here)
```

### 4.2 Usability Rating Scale (1 to 5)
1. **Installation & Setup:** [ 1 = Broken / Confusing | 5 = Flawless / Fast ]
2. **Documentation & Examples:** [ 1 = Incomprehensible | 5 = Crystal Clear ]
3. **API Ergonomics & Naming:** [ 1 = Confusing / Rigid | 5 = Intuitive / Pythonic ]
4. **Error Messages:** [ 1 = Unhelpful | 5 = Highly Actionable ]
5. **Overall Adoption Interest:** [ 1 = Would not use | 5 = Excited to adopt ]

