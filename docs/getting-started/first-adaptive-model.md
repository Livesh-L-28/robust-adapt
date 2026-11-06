# Your First Adaptive Model

In this guide, we dive deeper into configuring the `AdaptiveClassifier` and `ReliabilityWeightedADWIN` for real-time streaming adaptation.

---

## The Prequential Evaluation Protocol

Traditional machine learning uses a static train/test split (e.g., 80% train, 20% test). In streaming data, this is impossible because data arrives sequentially and indefinitely over time.

Instead, streaming systems use **Prequential Evaluation (Test-Then-Train)**:

```
[Incoming Sample (x_t, y_t)]
            |
            v
1. Predict: y_hat = model.predict(x_t)
            |
            v
2. Score:   loss = evaluate(y_hat, y_t)
            |
            v
3. Update:  model.partial_fit(x_t, y_t)
```

This guarantees an unbiased estimate of generalization performance without requiring a separate held-out test split.

---

## Configuring the Hoeffding Tree Classifier

`AdaptiveClassifier` is based on Hoeffding Trees (streaming decision trees that split nodes incrementally using the Hoeffding Bound theorem):

```python
from robust_adapt.ala import AdaptiveClassifier

clf = AdaptiveClassifier(
    n_features=10,        # Number of input dimensions
    n_classes=2,          # Target classes (binary or multi-class)
    grace_period=20,      # Number of samples between split attempts
    delta=0.001,          # Confidence parameter for Hoeffding bound
    tie_threshold=0.05,   # Split tie-breaking threshold
)
```

### Parameter Explanations
- **`grace_period`**: How many samples a leaf node must observe before attempting a split. Smaller values split faster but increase computation; larger values save CPU.
- **`delta`**: Probability that the chosen split attribute is not the true optimal attribute. Smaller delta values require more statistical evidence before splitting.

---

## Complete Working Example

```python
import numpy as np
from robust_adapt.ala import AdaptiveClassifier, ReliabilityWeightedADWIN

np.random.seed(101)
n_features = 5
clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=15)
adwin = ReliabilityWeightedADWIN(delta=0.005)

# Simulate 300 streaming events
for step in range(300):
    # Features
    x = np.random.randn(1, n_features)
    # Ground truth (class 1 if sum of features is positive)
    y = np.array([int(np.sum(x) > 0)])

    # 1. Prequential prediction
    probs = clf.predict_proba(x)
    pred = int(np.argmax(probs))

    # 2. Track drift
    adwin.update(float(pred != y[0]))

    # 3. Model learning update
    clf.partial_fit(x, y)

print("Classifier completed 300 steps cleanly.")
```
