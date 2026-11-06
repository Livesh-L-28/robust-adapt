# Getting Started — 5-Minute Quickstart

This quickstart demonstrates streaming classification, concept drift adaptation, robust noise filtering, and resource-efficient optimization in under 5 minutes.

---

## 1. Top-Level Convenience Import

With AdaptiveML Stage 8 SDK standardization, all core classes and controllers can be imported directly from `adaptive_ml`:

```python
import numpy as np
import robust_adapt as aml

print(f"AdaptiveML Version: {aml.__version__}")
```

---

## 2. Streaming Classification with Adaptive Drift Handling (ALA)

The [`AdaptiveClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py) integrates streaming Hoeffding trees with ADWIN drift detection to continuously update models as data distributions shift:

```python
import numpy as np
from robust_adapt import AdaptiveClassifier

# Initialize adaptive classifier with 8 features
clf = AdaptiveClassifier(n_features=8, max_depth=6, grace_period=25)

# Simulate 5 sequential mini-batches with concept drift at step 3
for step in range(1, 6):
    X = np.random.randn(50, 8).astype(np.float32)
    # Concept switch: decision boundary flips
    if step < 3:
        y = (X[:, 0] + X[:, 1] > 0.0).astype(np.int64)
    else:
        y = (X[:, 2] - X[:, 3] > 0.0).astype(np.int64)

    metrics = clf.partial_fit(X, y)
    print(f"Batch {step} | Accuracy: {metrics['accuracy']:.1%} | Drifts: {metrics.get('drifts', 0)}")

# Inference on unseen samples
X_test = np.random.randn(5, 8).astype(np.float32)
preds = clf.predict(X_test)
probs = clf.predict_proba(X_test)

print("Predictions:", preds)
print("Class Probabilities (first sample):", probs[0])
```

---

## 3. Robust Learning under Label Noise (RLA)

When labels contain corruption, use [`NoiseRobustClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/noise_classifier.py) to assess sample credibility and down-weight noisy instances:

```python
from robust_adapt import NoiseRobustClassifier

# Initialize noise-robust classifier
rla_clf = NoiseRobustClassifier(n_features=8, noise_threshold=0.6)

# Ingest batches with corrupted labels
for step in range(1, 4):
    X = np.random.randn(50, 8).astype(np.float32)
    y = (X[:, 0] > 0.0).astype(np.int64)
    # Inject 20% random label flips
    flip_mask = np.random.rand(50) < 0.20
    y[flip_mask] = 1 - y[flip_mask]

    metrics = rla_clf.partial_fit(X, y)
    print(f"Step {step} | Filtered noisy samples: {metrics.get('filtered_samples', 0)}")
```

---

## 4. Resource-Aware 8-Bit Optimization (RAO)

Train with 73.4% less optimizer state memory using [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py):

```python
import torch
import torch.nn as nn
from robust_adapt import LowMemoryAdamW

# Neural network
model = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, 2))

# 8-bit optimizer
optimizer = LowMemoryAdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)

inputs = torch.randn(16, 8)
targets = torch.randint(0, 2, (16,))
criterion = nn.CrossEntropyLoss()

optimizer.zero_grad()
loss = criterion(model(inputs), targets)
loss.backward()
optimizer.step()

print(f"Training step completed with 8-bit AdamW. Loss: {loss.item():.4f}")
```

---

## 5. Unified Multi-Pillar Coordination (ULC-v4.1)

Coordinate ALA, RLA, and RAO with the [`UnifiedLearningControllerV4_1`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) to prevent false drift resets caused by label noise:

```python
from robust_adapt import UnifiedLearningControllerV4_1, Directive

controller = UnifiedLearningControllerV4_1()

# Streaming step with spatial discordance and reliability telemetry
directive, explain_info = controller.step(
    metric_delta=0.15,
    sample_entropy=0.72,
    spatial_discordance=0.35,
    reliability_score=0.88
)

print("Arbitrated Directive:", directive.name)
print("Confidence:", explain_info["confidence"])
```
