# Recurring Concept Memory & Fingerprinting

`RecurringConceptMemory` manages a bounded repository of historical model snapshots and statistical concept signatures.

---

## 1. Lifecycle of a Concept Snapshot

```
1. Active Stream Processing
   [ Input Batch (X, y) ] ---> Compute ConceptFingerprint(X, y)
                                           |
2. Drift Triggered (ADWIN Alert)           |
   Query RecurringConceptMemory <----------+
            |
    +-------+-------+
    |               |
    v (Match found: Sim >= tau)   v (No match: Novel drift)
Restore Historical Snapshot       Save Current Concept Snapshot
Update Concept Metadata           Reset Active Tree (Seed from Replay)
Zero Retraining Overhead          Learn New Distribution
```

---

## 2. Using `RecurringConceptMemory` Programmatically

```python
import numpy as np
from robust_adapt.ala import RecurringConceptMemory, ConceptFingerprinter, AdaptiveClassifier

# Initialize components
memory = RecurringConceptMemory(max_concepts=5, similarity_threshold=0.80)
fingerprinter = ConceptFingerprinter(n_features=4, n_classes=2)
model = AdaptiveClassifier(n_features=4, n_classes=2)

# Simulate a learned concept
X_concept_A = np.random.randn(50, 4) + 2.0
y_concept_A = (X_concept_A[:, 0] > 0).astype(int)
model.partial_fit(X_concept_A, y_concept_A)

# 1. Store concept snapshot
fp_A = fingerprinter.compute_fingerprint(X_concept_A, y_concept_A)
snap = memory.store_concept(fingerprint=fp_A, model_state=model, step=50)
print(f"Stored Concept: {snap.concept_id}")

# 2. Query recurring concept memory with candidate stream data
X_candidate = np.random.randn(50, 4) + 1.9  # Similar distribution
y_candidate = (X_candidate[:, 0] > 0).astype(int)
fp_candidate = fingerprinter.compute_fingerprint(X_candidate, y_candidate)

matching_snap, similarity = memory.find_matching_concept(fp_candidate)
if matching_snap is not None:
    print(f"Recurring concept recognized: {matching_snap.concept_id} (Similarity: {similarity:.3f})")
    # Restore model state instantaneously
    restored_model = matching_snap.model_state
```

---

## 3. Eviction & Memory Boundedness

When the number of stored concepts exceeds `max_concepts`, `RecurringConceptMemory` automatically evicts the oldest / least-recently-matched concept. This guarantees strict $O(1)$ memory complexity regardless of how many concepts occur over time.
