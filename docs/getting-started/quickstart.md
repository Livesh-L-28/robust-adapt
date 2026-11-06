# 5-Minute Quickstart

This hands-on quickstart demonstrates how to train, evaluate, and monitor a continuous adaptive classifier in under five minutes.

---

## 1. Installation

Install the minimal core distribution:

```bash
pip install robust-adapt
```

---

## 2. Complete Runnable Script

Save the following code as `quickstart.py` and run it:

```python
import numpy as np
from robust_adapt import AdaptiveClassifier, ReliabilityWeightedADWIN

# 1. Generate synthetic stream with an abrupt concept inversion at step 200
np.random.seed(42)
n_samples = 400
n_features = 4

X = np.random.randn(n_samples, n_features)
# Early regime (steps 0-199): class 1 if feature 0 is positive
y_early = (X[:200, 0] > 0).astype(int)
# Drifted regime (steps 200-399): class 1 if feature 0 is negative (inversion)
y_drift = (X[200:, 0] < 0).astype(int)
y = np.concatenate([y_early, y_drift])

# 2. Initialize streaming classifier and statistical drift detector
clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=10)
detector = ReliabilityWeightedADWIN(delta=0.01)

print("Starting streaming prequential evaluation...")

# 3. Stream processing loop
detected_drifts = []
correct_predictions = 0

for i in range(n_samples):
    x_i = X[i : i + 1]
    y_i = y[i : i + 1]

    # Step A: Prequential prediction (test before train)
    prob = clf.predict_proba(x_i)
    pred = int(np.argmax(prob))

    if pred == y_i[0]:
        correct_predictions += 1

    # Step B: Monitor error rate for distribution drift
    is_error = float(pred != y_i[0])
    if detector.update(is_error):
        print(f"--> [ALERT] Concept drift statistically detected at sample {i}!")
        detected_drifts.append(i)

    # Step C: Incrementally update model on current sample
    clf.partial_fit(x_i, y_i)

accuracy = correct_predictions / n_samples
print("--------------------------------------------------")
print(f"Total Stream Samples:  {n_samples}")
print(f"Overall Accuracy:      {accuracy:.2%}")
print(f"Detected Drift Points: {detected_drifts}")
print("Quickstart completed successfully!")
```

---

## 3. Execution & Expected Output

Run the script from your terminal:

```bash
python quickstart.py
```

Expected output:
```text
Starting streaming prequential evaluation...
--> [ALERT] Concept drift statistically detected at sample 206!
--------------------------------------------------
Total Stream Samples:  400
Overall Accuracy:      91.50%
Detected Drift Points: [206]
Quickstart completed successfully!
```

### What Happened?
1. **Prequential Evaluation**: Each instance is tested first to measure real generalization error, then immediately used to update the decision tree.
2. **Instant Drift Detection**: At sample 200, the underlying ground truth inverted. By sample 206 (only 6 samples later), `ReliabilityWeightedADWIN` detected the statistically significant elevation in error rate and fired an alert.
3. **Rapid Adaptation**: The `AdaptiveClassifier` adjusted its Hoeffding Tree split statistics, recovering $>90\%$ overall streaming accuracy across the entire 400-sample run.
