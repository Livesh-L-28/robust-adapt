# Asymmetric Noise Transitions & Defense

Symmetric noise assumes all classes flip into each other with equal probability. In operational data streams, this assumption is almost universally violated.

---

## 1. Asymmetric Transition Matrix

Consider a binary fraud detection system ($0 = \text{Legitimate}, 1 = \text{Fraud}$):
- Legitimate transactions are verified automatically:
  $$P(\tilde{y} = 1 \mid y = 0) = 0.01$$
- Fraudulent transactions actively mimic legitimate patterns, tricking automated annotators:
  $$P(\tilde{y} = 0 \mid y = 1) = 0.35$$

The transition matrix $T$ is asymmetric:

$$T = \begin{bmatrix} 0.99 & 0.01 \\ 0.35 & 0.65 \end{bmatrix}$$

Standard robust algorithms designed for symmetric noise fail under asymmetric corruption because they falsely penalize genuine minority samples that look like majority instances.

---

## 2. Asymmetric Defense Protocol

`AsymmetricTransitionDetector` tracks class-conditional prediction errors to dynamically estimate the transition matrix $\hat{T}$:

```python
from robust_adapt.rla import AsymmetricTransitionDetector

detector = AsymmetricTransitionDetector(n_classes=2, window_size=500)

# Feed predicted probabilities and reported labels
# detector.update(y_true_observed, y_predicted_prob)
```

### Mitigations
1. **Class-Conditional Re-Weighting**: Scales sample weights inversely with class-conditional corruption rates:
   $$w_i = \frac{1}{1 - \hat{T}_{y_i, 1 - y_i}}$$
2. **Minority Protection Policy**: Disables hard abstention on protected minority classes unless neighborhood agreement is zero.
