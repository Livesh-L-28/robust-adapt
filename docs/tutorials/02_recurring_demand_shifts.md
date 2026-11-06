# Tutorial 2: Adapting to Recurring Concept Shifts in Retail Demand

**Domain:** E-Commerce & Retail Demand Streams<br>
**Algorithms:** `ALA30AdaptiveLearner`, `RecurringConceptMemory`, `ConceptFingerprinter`<br>
**Execution Mode:** Cyclical concept stream with episodic memory restoration<br>

---

## 1. Problem Scenario

E-commerce consumer behaviors fluctuate predictably between recurring patterns (e.g., Weekday work commutes vs. Weekend leisure browsing, or Promotional flash sales vs. Baseline periods).

When a stream drifts back to an earlier regime, standard drift-adaptation algorithms trigger a blind reset, discarding valuable learned parameters and suffering severe transient error penalties while re-learning.

In this tutorial, you will use **ALA 3.0** to:
1. Ingest streaming data alternating between two cyclical regimes ($A \to B \to A \to B$).
2. Automatically fingerprint concept distributions in memory.
3. Detect recurring drift and immediately restore historical concept snapshots via `RecurringConceptMemory`.

---

## 2. Complete Runnable Code

```python
import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner

np.random.seed(42)

def generate_cyclical_demand_stream(cycles=2, steps_per_regime=10, batch_size=40):
    """Generates stream alternating between Regime A and Regime B."""
    step = 0
    for c in range(cycles):
        # Regime A: Weekday Pattern
        for _ in range(steps_per_regime):
            X = np.random.normal(loc=0.0, scale=1.0, size=(batch_size, 4))
            y = (X[:, 0] + X[:, 1] > 0.0).astype(int)
            yield step, "Regime_A", X, y
            step += 1

        # Regime B: Weekend Pattern
        for _ in range(steps_per_regime):
            X = np.random.normal(loc=2.0, scale=1.0, size=(batch_size, 4))
            y = (X[:, 2] - X[:, 3] > 0.0).astype(int)
            yield step, "Regime_B", X, y
            step += 1

def main():
    print("--- Starting Recurring Demand Shifts Tutorial ---")

    # Initialize ALA 3.0 Learner with Recurring Concept Memory
    learner = ALA30AdaptiveLearner(
        n_features=4,
        n_classes=2,
        grace_period=20,
        delta=0.005,
        max_concepts=5,
        similarity_threshold=0.80,
    )

    for step, regime, X_batch, y_batch in generate_cyclical_demand_stream(cycles=2, steps_per_regime=12):
        telemetry = learner.update(X_batch, y_batch)

        # Monitor drift interventions
        if telemetry["drift_detected"] or step in (0, 11, 12, 23, 24, 35, 47):
            print(
                f"Step {step:02d} [{regime}] | "
                f"Action: {telemetry['action']:22s} | "
                f"Batch Acc: {telemetry['batch_acc'] * 100:5.1f}% | "
                f"Stored Concepts: {telemetry['stored_concepts']} | "
                f"Restorations: {learner.recurring_restorations}"
            )

    print(f"\nFinal Stream Audit:")
    print(f"Total Steps Processed: {learner.total_steps}")
    print(f"Drift Resets (Novel Concepts): {learner.drift_resets}")
    print(f"Recurring Concept Restorations: {learner.recurring_restorations}")
    print("--- Tutorial Completed Successfully ---")

if __name__ == "__main__":
    main()
```

---

## 3. Key Observations

- When the stream transitions to Regime B for the first time (step 12), ALA 3.0 recognizes it as a **novel concept**, snapshots Regime A into memory, and initializes a fresh tree for Regime B.
- When the stream transitions back to Regime A (step 24), the cosine fingerprint matches the stored Regime A concept ($\text{sim} > 0.80$).
- Instead of resetting, ALA 3.0 triggers an instantaneous `RECURRING_RESTORE`, preserving full predictive accuracy without transient learning decay.
