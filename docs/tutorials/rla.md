# Pillar Tutorial: Robust Learning Algorithms (RLA)

This tutorial demonstrates how to train streaming models in the presence of corrupted labels, adversarial noise, and severe class imbalance using AdaptiveML's RLA pillar.

---

## 1. The Challenge of Noisy Labels in Continual Streams

When labels are subject to corruption (e.g., automated tagging errors, unreliable crowd workers, sensor malfunctions), standard adaptive models suffer from two critical failures:
1. **Model Poisoning**: The classifier learns erroneous decision boundaries based on corrupted targets.
2. **False Drift Triggering**: Standard drift detectors (such as ADWIN) interpret sudden bursts of label noise as distribution shifts, resetting and destroying healthy models.

AdaptiveML resolves this through three robust mechanisms:
- **Sample Reliability Scoring** ([`ReliabilityEstimator`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/reliability.py)): Quantifies instance credibility in $[0, 1]$.
- **Noise Filtering Classifier** ([`NoiseRobustClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/noise_classifier.py)): Filters or down-weights corrupted samples before model updates.
- **Robust Loss Functions** ([`SymmetricCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py), [`GeneralizedCrossEntropyLoss`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/losses.py)): Provides noise-tolerant gradients for neural networks.

---

## 2. Noise Detection & Reliability Scoring

[`ReliabilityEstimator`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/reliability.py) computes continuous reliability scores $\mathcal{R}(x, y) \in [0, 1]$ by evaluating:
- **Prediction Confidence**: Agreement between model output probabilities and reported labels.
- **Temporal Consistency**: Moving-window loss deviations compared to baseline statistics.

```python
import numpy as np
from robust_adapt import ReliabilityEstimator

estimator = ReliabilityEstimator(window_size=50, sensitivity=1.5)

# Update estimator with sample loss and predicted probability
sample_loss = 2.45
pred_prob = 0.12  # Model was 88% confident in the opposing class

reliability_score = estimator.update(loss=sample_loss, confidence=pred_prob)
print(f"Sample Reliability: {reliability_score:.2f}")

if reliability_score < 0.30:
    print("Sample flagged as high-probability label corruption. Down-weighting.")
```

---

## 3. Streaming Classification with Noise Filtering

The [`NoiseRobustClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/noise_classifier.py) automatically filters suspicious samples during `partial_fit`:

```python
from robust_adapt import NoiseRobustClassifier

clf = NoiseRobustClassifier(n_features=8, noise_threshold=0.55)

# Simulate a batch with 30% synthetic label flips
X = np.random.randn(60, 8).astype(np.float32)
y_clean = (X[:, 0] > 0.0).astype(np.int64)
y_noisy = y_clean.copy()

noise_mask = np.random.rand(60) < 0.30
y_noisy[noise_mask] = 1 - y_noisy[noise_mask]

# Partial fit on noisy stream
metrics = clf.partial_fit(X, y_noisy)
print(f"Processed: {len(X)} | Retained: {metrics['retained_samples']} | Filtered: {metrics['filtered_samples']}")
```

---

## 4. PyTorch Integration: Symmetric & Generalized Cross Entropy

For deep neural networks, standard cross-entropy loss overfits to corrupted labels. AdaptiveML provides differentiable noise-robust losses:

### 4.1 Symmetric Cross Entropy (SCE)
SCE combines standard Cross Entropy (CE) with Reverse Cross Entropy (RCE):
$$\mathcal{L}_{\text{SCE}} = \alpha \, \mathcal{L}_{\text{CE}}(p, q) + \beta \, \mathcal{L}_{\text{RCE}}(p, q)$$

```python
import torch
from robust_adapt import SymmetricCrossEntropyLoss

# Alpha: standard CE weight, Beta: reverse CE robust weight
criterion = SymmetricCrossEntropyLoss(alpha=0.1, beta=1.0)

logits = torch.randn(8, 2, requires_grad=True)
targets = torch.tensor([0, 1, 1, 0, 1, 0, 0, 1])

loss = criterion(logits, targets)
loss.backward()
print(f"SCE Loss: {loss.item():.4f}")
```

### 4.2 Generalized Cross Entropy (GCE)
GCE applies a Box-Cox transformation parameter $q \in (0, 1]$ bridging Mean Absolute Error (MAE, completely robust) and Cross Entropy (CE, fast convergence):

```python
from robust_adapt import GeneralizedCrossEntropyLoss

# q=0.7 balances convergence speed and noise robustness
gce_criterion = GeneralizedCrossEntropyLoss(q=0.7)
loss = gce_criterion(logits, targets)
print(f"GCE Loss: {loss.item():.4f}")
```

---

## 5. Minority Class Preservation

When noise is injected into highly imbalanced streams, naive filtering might discard critical minority instances:
- Use [`OnlineClassPriorTracker`](file:///c:/projects/AdaptiveML/adaptive_ml/minority/prior_tracker.py) to dynamically adjust reliability thresholds so rare class samples are not prematurely eliminated.
- Use [`MinorityAwareDriftDetector`](file:///c:/projects/AdaptiveML/adaptive_ml/minority/detector.py) to ensure drift detection operates fairly across class frequencies.
