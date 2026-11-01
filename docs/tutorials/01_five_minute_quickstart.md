# Tutorial 1: Five-Minute Quickstart

Get started with AdaptiveML in under 5 minutes.

---

## 1. Installation

AdaptiveML is local-first and CPU-first. The core library requires only `numpy >= 1.24.0`:

```bash
# Clone the repository
git clone https://github.com/AdaptiveML/AdaptiveML.git
cd AdaptiveML

# Install in development mode
pip install -e .
```

---

## 2. Your First Streaming Classifier

AdaptiveML's `AdaptiveClassifier` combines vectorized Hoeffding trees with automatic concept drift detection and class-balanced reservoir replay:

```python
import numpy as np
from adaptive_ml.ala import AdaptiveClassifier

# Initialize the online classifier
model = AdaptiveClassifier(
    n_features=4,
    n_classes=2,
    grace_period=20,
    enable_drift_detection=True,
)

# Stream 5 mini-batches of observations
rng = np.random.default_rng(42)
for step in range(1, 6):
    X = rng.normal(size=(20, 4))
    y = (X[:, 0] > 0.0).astype(int)

    # Test before train (prequential evaluation)
    if model.samples_seen_ > 0:
        accuracy = np.mean(model.predict(X) == y)
        print(f"Step {step} | Test Accuracy: {accuracy * 100:.1f}%")

    # Update model incrementally
    model.partial_fit(X, y)
```

Executable script available at [`examples/quickstart.py`](file:///c:/projects/AdaptiveML/examples/quickstart.py).

