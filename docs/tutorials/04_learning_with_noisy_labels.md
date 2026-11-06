# Tutorial 04: Learning with Noisy Labels

**Objective**: Train a noise-resilient model on corrupted annotations using Symmetric Cross-Entropy (`SymmetricCrossEntropyLoss`).

---

## 1. Setup & Imports

```python
import numpy as np
from robust_adapt.rla.losses import SymmetricCrossEntropyLoss

# Alpha controls CE weight, Beta controls Reverse CE weight
loss_fn = SymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)
```

---

## 2. Gradient Boundedness Under Symmetric Label Noise

```python
# Simulate predictions: Model predicts Class 0 with 99.9% confidence
# Target is mislabeled as Class 1
logits = np.array([[10.0, -10.0]], dtype=np.float32)
noisy_target = np.array([1], dtype=np.int64)

# Compute loss and gradient
loss_val = loss_fn(logits, noisy_target)
grad = loss_fn.backward(logits, noisy_target)

print("Loss on corrupted sample:", loss_val)
print("Gradient vector:", grad)
print("Max absolute gradient:", np.max(np.abs(grad)))
```

Notice that standard Cross-Entropy would produce a severe gradient magnitude ($\approx 1.0$), while Reverse Cross-Entropy bounds the gradient, preventing network parameters from being destabilized by label errors.
