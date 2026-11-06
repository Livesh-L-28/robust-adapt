# Pillar Tutorial: Adaptive Learning Algorithms (ALA)

This tutorial provides a comprehensive guide to building streaming classification pipelines that continuously detect and adapt to concept drift using AdaptiveML's ALA pillar.

---

## 1. Overview of Adaptive Learning in AdaptiveML

Streaming data frequently violates the standard i.i.d. (independent and identically distributed) assumption. Concept drift occurs when the statistical relationship between input features $\mathbf{x}$ and target labels $y$ changes over time:

$$P_{t_1}(\mathbf{x}, y) \ne P_{t_2}(\mathbf{x}, y)$$

AdaptiveML provides four interconnected components to handle non-stationary streams:
1. **Incremental Hoeffding Trees** ([`HoeffdingTree`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/tree.py)): Sample-by-sample decision trees with provable convergence bounds.
2. **ADWIN Drift Detection** ([`ADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py)): Statistically grounded sliding window for rate-of-change detection.
3. **Concept Memory** ([`ConceptMemory`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/concept_memory.py)): Fast retrieval and re-activation of previously learned concept models.
4. **Delayed Label Handling** ([`DelayedLabelBuffer`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/delayed_labels.py)): Ingestion buffering when ground-truth labels arrive with variable latency.

---

## 2. Streaming Classification & ADWIN Drift Detection

The [`AdaptiveClassifier`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py) integrates streaming Hoeffding trees with an internal ADWIN detector. When accuracy drops significantly, ADWIN triggers an adaptation event:

```python
import numpy as np
from robust_adapt import AdaptiveClassifier, ADWINConfig

# Create an adaptive classifier with custom ADWIN sensitivity
classifier = AdaptiveClassifier(
    n_features=6,
    max_depth=8,
    grace_period=40,
    adwin_config=ADWINConfig(delta=0.005)
)

# Ingest streaming data across a synthetic abrupt drift
for t in range(100):
    # 20 samples per streaming step
    X_step = np.random.randn(20, 6).astype(np.float32)

    # Abrupt concept drift occurs at step 50
    if t < 50:
        y_step = (X_step[:, 0] + X_step[:, 1] > 0.0).astype(np.int64)
    else:
        y_step = (X_step[:, 2] - X_step[:, 3] > 0.0).astype(np.int64)

    metrics = classifier.partial_fit(X_step, y_step)
    if metrics.get("drifts", 0) > 0:
        print(f"[Step {t}] Concept Drift Alert! Model adapted.")
```

---

## 3. Recurring Drift with Concept Memory

In recurring drift environments (such as seasonal shopping patterns or day/night cycles), discarding previous trees on every drift causes wasteful re-learning.

[`ConceptMemory`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/concept_memory.py) maintains an indexed repository of concept signatures:

```python
from robust_adapt import ConceptMemory

# Initialize concept repository capable of holding up to 5 concepts
memory = ConceptMemory(max_concepts=5, similarity_threshold=0.85)

# Save active model snapshot for "winter_concept"
memory.store_concept(concept_id="winter", state_dict=classifier.state_dict(), signature=X_step.mean(axis=0))

# Later in the stream, when similar distribution reappears:
best_id, match_score = memory.query_similarity(X_step.mean(axis=0))
if match_score >= 0.85:
    print(f"Recognized recurring concept '{best_id}' (score: {match_score:.2f}). Restoring saved state.")
    classifier.load_state_dict(memory.get_concept_state(best_id))
```

---

## 4. Handling Delayed Labels

In real-world applications (fraud detection, click-through prediction), user features arrive in real time, but true labels only arrive minutes, hours, or days later.

[`DelayedLabelBuffer`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/delayed_labels.py) pairs delayed arrival labels with historical feature predictions:

```python
from robust_adapt import DelayedLabelBuffer

buffer = DelayedLabelBuffer(max_buffer_size=1000, timeout_steps=500)

# 1. Feature arrives at time t=10
sample_id = "tx_98412"
features = np.random.randn(6).astype(np.float32)
pred = classifier.predict(features.reshape(1, -1))[0]

buffer.push_prediction(sample_id=sample_id, features=features, prediction=pred, timestamp=10)

# 2. True label arrives at time t=65
true_label = 1
paired_sample = buffer.resolve_label(sample_id=sample_id, true_label=true_label, timestamp=65)

if paired_sample is not None:
    # Model learns on verified delayed sample
    classifier.partial_fit(paired_sample.features.reshape(1, -1), np.array([paired_sample.label]))
    print(f"Sample {sample_id} resolved with delay {paired_sample.delay_steps} steps and trained.")
```

---

## 5. Summary & Best Practices

- Use `grace_period` between 25 and 100 for responsive streaming tree splits.
- For streams with recurring patterns, combine `AdaptiveClassifier` with `ConceptMemory` to avoid catastrophic forgetting.
- Use `DelayedLabelBuffer` to prevent label leakage and ensure models are only trained on verified ground truth.
