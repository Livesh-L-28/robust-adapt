# Tutorial 3: Robust Learning Under Extreme Label Corruption

**Domain:** Crowdsourced Labeling, Clickstream Logs & Noisy Telemetry<br>
**Algorithms:** `RLA30RobustLearner`, `MultiSignalReliabilityEngine`, `SymmetricCrossEntropyLoss`<br>
**Execution Mode:** Micro-batch stream with 35% synthetic asymmetric label flip corruption<br>

---

## 1. Problem Scenario

Real-world streaming labels are frequently corrupt:
- Crowdsourced annotators click through tasks carelessly.
- Automated heuristics misclassify ambiguous edge cases.
- Sensor threshold glitches invert signal polarity.

Standard cross-entropy loss rapidly overfits and memorizes these inverted labels. In this tutorial, you will use **RLA 3.0** to:
1. Stream instances with a high noise corruption rate ($35\%$).
2. Compute continuous composite sample reliability scores $r_i \in [0, 1]$.
3. Abstain from learning on corrupt outliers while training stably on retained high-reliability samples.

---

## 2. Complete Runnable Code

```python
import numpy as np
from robust_adapt.rla import RLA30RobustLearner

np.random.seed(42)

def generate_noisy_stream(n_steps=15, batch_size=60, noise_rate=0.35):
    """Generates synthetic stream where noise_rate of labels are flipped."""
    for step in range(n_steps):
        X = np.random.randn(batch_size, 4)
        # Ground truth separable boundary
        y_true = (X[:, 0] + 0.5 * X[:, 1] > 0.0).astype(int)

        # Corrupt labels
        y_noisy = y_true.copy()
        n_corrupt = int(batch_size * noise_rate)
        flip_indices = np.random.choice(batch_size, size=n_corrupt, replace=False)
        y_noisy[flip_indices] = 1 - y_noisy[flip_indices]

        yield step, X, y_noisy, y_true

def main():
    print("--- Starting Extreme Label Noise Tutorial ---")

    # Initialize RLA 3.0 Robust Learner
    learner = RLA30RobustLearner(
        n_features=4,
        n_classes=2,
        lr=0.05,
        reliability_threshold=0.35,  # Abstain from samples scoring r_i < 0.35
        security_mode="standard",
    )

    for step, X_batch, y_noisy, y_true in generate_noisy_stream():
        # Ingest noisy batch through RLA 3.0 pipeline
        metrics = learner.fit_batch(X_batch, y_noisy)

        # Evaluate true accuracy against uncorrupted ground truth
        true_accuracy = learner.score(X_batch, y_true)

        print(
            f"Step {step:02d} | "
            f"Retained: {metrics['retained']:2d}/{len(y_noisy)} | "
            f"Abstained: {metrics['abstained']:2d} | "
            f"Mean Reliability: {metrics['mean_reliability']:.3f} | "
            f"True Acc: {true_accuracy * 100:5.1f}%"
        )

    print(f"\nFinal Stream Audit:")
    print(f"Total Samples Seen: {learner.total_samples_seen}")
    print(f"Total Samples Retained: {learner.retained_samples}")
    print(f"Total Corrupt Samples Filtered Out: {learner.abstained_samples}")
    print("--- Tutorial Completed Successfully ---")

if __name__ == "__main__":
    main()
```

---

## 3. Key Observations

- In the initial steps ($0-2$), the internal reliability engine collects baseline feature neighborhood statistics.
- As the model stabilizes, the multi-signal engine flags corrupted instances whose labels disagree with spatial $k$-NN neighbors and have negative prediction margins.
- By abstaining from backpropagating through low-reliability instances, RLA 3.0 protects model parameters from noisy gradient corruption.
