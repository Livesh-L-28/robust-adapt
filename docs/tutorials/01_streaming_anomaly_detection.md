# Tutorial 1: Streaming Anomaly & Drift Detection in IoT Sensors

**Domain:** IoT Industrial Telemetry & Sensor Monitoring<br>
**Algorithms:** `ALA30AdaptiveLearner`, `ADWIN`, `to_numpy`<br>
**Execution Mode:** Micro-batch streaming with prequential accuracy tracking<br>

---

## 1. Problem Scenario

Industrial machinery continuously outputs high-frequency telemetry (vibration, temperature, power draw). When operating conditions shift (e.g. ambient temperature drops, machine enters high-load mode), sensor distributions drift. A static ML model experiences silent accuracy degradation.

In this tutorial, you will build an adaptive streaming pipeline that:
1. Ingests simulated sensor telemetry in micro-batches of 50 samples.
2. Evaluates prequential classification accuracy before each learning update.
3. Automatically detects distribution shifts using ADWIN.
4. Adapts decision boundaries in real time while tracking drift events.

---

## 2. Complete Runnable Code

```python
import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner

# Set random seed for reproducibility
np.random.seed(42)

def generate_sensor_stream(n_steps=20, batch_size=50):
    """Generates synthetic sensor stream with a sudden drift at step 10."""
    for step in range(n_steps):
        # Step 0-9: Normal baseline regime
        if step < 10:
            X = np.random.normal(loc=0.0, scale=1.0, size=(batch_size, 4))
            y = (X[:, 0] + X[:, 1] > 0.0).astype(int)
        # Step 10-19: Abrupt drift (sensor calibration shift)
        else:
            X = np.random.normal(loc=1.5, scale=1.2, size=(batch_size, 4))
            y = (X[:, 2] - X[:, 3] > 0.5).astype(int)
        yield step, X, y

def main():
    print("--- Starting IoT Sensor Streaming Tutorial ---")

    # Initialize ALA 3.0 Adaptive Learner
    learner = ALA30AdaptiveLearner(
        n_features=4,
        n_classes=2,
        grace_period=25,     # Check split heuristics every 25 samples
        delta=0.005,         # ADWIN drift detection sensitivity
    )

    prequential_accuracies = []

    for step, X_batch, y_batch in generate_sensor_stream():
        # 1. Prequential Evaluation (Test before Train)
        if learner.total_steps > 0:
            preds = learner.predict(X_batch)
            step_acc = float(np.mean(preds == y_batch))
        else:
            step_acc = 0.50  # Baseline prior to training

        prequential_accuracies.append(step_acc)

        # 2. Incremental Training & Adaptation
        metrics = learner.update(X_batch, y_batch)

        # 3. Log progress
        if step in (0, 9, 10, 11, 19):
            print(
                f"Step {step:02d} | "
                f"Prequential Acc: {step_acc * 100:5.1f}% | "
                f"Batch Fit Acc: {metrics['batch_acc'] * 100:5.1f}% | "
                f"Drift Resets: {learner.drift_resets}"
            )

    print(f"\nFinal State: Total stream steps: {learner.total_steps}")
    print(f"Total drift events detected and adapted: {learner.drift_resets}")
    print("--- Tutorial Completed Successfully ---")

if __name__ == "__main__":
    main()
```

---

## 3. Expected Output

When executed, the prequential accuracy temporarily dips immediately after the abrupt drift at step 10, and quickly recovers as ADWIN detects the cut and resets the Hoeffding tree:

```text
--- Starting IoT Sensor Streaming Tutorial ---
Step 00 | Prequential Acc:  50.0% | Batch Fit Acc:  72.0% | Drift Resets: 0
Step 09 | Prequential Acc:  86.0% | Batch Fit Acc:  88.0% | Drift Resets: 0
Step 10 | Prequential Acc:  48.0% | Batch Fit Acc:  64.0% | Drift Resets: 0
Step 11 | Prequential Acc:  74.0% | Batch Fit Acc:  82.0% | Drift Resets: 1
Step 19 | Prequential Acc:  90.0% | Batch Fit Acc:  92.0% | Drift Resets: 1

Final State: Total stream steps: 20
Total drift events detected and adapted: 1
--- Tutorial Completed Successfully ---
```
