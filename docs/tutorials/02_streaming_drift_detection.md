# Tutorial 2: Streaming Drift Detection with RW-ADWIN

Learn how AdaptiveML detects distributional shifts while ignoring noisy observations.

---

## 1. Why Standard ADWIN Fails Under Noise

Standard ADWIN partitions an active sliding window into two sub-windows $W = W_0 \cdot W_1$ and cuts the oldest window if:
$$|\mu_0 - \mu_1| \ge \epsilon_{\text{cut}}$$

When a burst of noisy labels arrives, raw variance spikes. Standard ADWIN misidentifies the noise as concept drift, wiping the model's memory (catastrophic forgetting).

---

## 2. Using ReliabilityWeightedADWIN

`ReliabilityWeightedADWIN` weights sub-window cuts by sample reliability $r_i \in [0, 1]$:

```python
from adaptive_ml.ala.adwin import ReliabilityWeightedADWIN

detector = ReliabilityWeightedADWIN(delta=0.002)

# Feed observations: loss and sample reliability
loss = 0.95        # High loss
reliability = 0.15 # Corrupted sample flagged by RLA

# Under low reliability, the detector downweights the error,
# suppressing false positive window cuts
drift_detected = detector.update(loss, reliability=reliability)
if drift_detected:
    print("True distributional shift detected!")
```

Executable demo available at [`examples/ala/streaming_classification_example.py`](file:///c:/projects/AdaptiveML/examples/ala/streaming_classification_example.py).
