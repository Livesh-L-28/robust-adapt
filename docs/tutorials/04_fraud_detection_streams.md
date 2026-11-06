# Tutorial 4: Preserving Minority Intelligence in Financial Fraud Streams

**Domain:** Banking, Payment Gateways & Fraud Detection<br>
**Algorithms:** `MinorityIntelligence20Learner`, `BetaBinomialPriorTracker`, `DynamicFPBudgetThresholdManager`<br>
**Execution Mode:** Highly imbalanced stream ($99.5\%$ majority vs. $0.5\%$ fraud)<br>

---

## 1. Problem Scenario

Financial fraud detection represents an extreme class-imbalance regime:
- Legitimate transactions account for $> 99.5\%$ of stream volume.
- Fraudulent transactions are rare, elusive, and evolve dynamically.
- Standard loss functions collapse into predicting the majority class, achieving $99.5\%$ nominal accuracy while detecting $0\%$ of fraud instances.
- Naive static cost weighting triggers thousands of false alarms, overwhelming compliance teams.

In this tutorial, you will use **Adaptive Minority Intelligence 2.0** to:
1. Track online class priors via a Bayesian **Beta-Binomial** prior tracker.
2. Apply sublinear cost scaling ($W_c = (1 / \hat{\pi}_c)^{0.52}$) to prevent gradient explosion.
3. Automatically modulate decision thresholds under a strict operational false-positive budget ($1.5\text{ FP per 1,000}$).

---

## 2. Complete Runnable Code

```python
import numpy as np
from robust_adapt.minority import MinorityIntelligence20Learner

np.random.seed(42)

def generate_fraud_stream(n_steps=12, batch_size=200, fraud_rate=0.01):
    """Generates continuous payment transaction stream with 1% fraud."""
    for step in range(n_steps):
        # 4 Transaction features: [amount, frequency, geo_distance, velocity]
        X = np.random.normal(loc=0.0, scale=1.0, size=(batch_size, 4))
        y = np.zeros(batch_size, dtype=int)

        # Inject rare fraud cases with distinct signatures
        n_fraud = max(1, int(batch_size * fraud_rate))
        fraud_indices = np.random.choice(batch_size, size=n_fraud, replace=False)
        X[fraud_indices, 0] += 3.5  # High amount
        X[fraud_indices, 2] += 2.8  # Unfamiliar location
        y[fraud_indices] = 1

        yield step, X, y

def main():
    print("--- Starting Fraud Detection Streaming Tutorial ---")

    # Initialize Minority Intelligence 2.0 Learner
    learner = MinorityIntelligence20Learner(
        target_fp_budget_per_1k=2.0,  # Cap false positives at 2 per 1,000 transactions
        sublinear_cost_power=0.52,     # Dampen minority sample weighting
        base_threshold=0.50,
        lr=0.02,
        minority_class=1,
    )

    total_fraud_detected = 0
    total_fraud_actual = 0

    for step, X_batch, y_batch in generate_fraud_stream():
        # Evaluate predictions prior to learning update
        preds = learner.predict(X_batch)

        actual_positives = np.sum(y_batch == 1)
        true_positives = np.sum((preds == 1) & (y_batch == 1))
        false_positives = np.sum((preds == 1) & (y_batch == 0))

        total_fraud_actual += int(actual_positives)
        total_fraud_detected += int(true_positives)

        # Update learner state and threshold
        telemetry = learner.fit_batch(X_batch, y_batch)

        print(
            f"Step {step:02d} | "
            f"Bayesian Prior: {telemetry['prior'] * 100:4.2f}% | "
            f"Threshold: {telemetry['active_threshold']:.3f} | "
            f"Fraud Found: {true_positives}/{actual_positives} | "
            f"False Alarms: {false_positives}"
        )

    recall = (total_fraud_detected / total_fraud_actual) * 100 if total_fraud_actual > 0 else 0.0
    print(f"\nFinal Stream Audit:")
    print(f"Total Transactions Processed: {learner.total_samples}")
    print(f"Total Fraud Cases Ingested: {total_fraud_actual}")
    print(f"Total Fraud Cases Successfully Flagged: {total_fraud_detected} ({recall:.1f}% Recall)")
    print("--- Tutorial Completed Successfully ---")

if __name__ == "__main__":
    main()
```

---

## 3. Key Observations

- The **Beta-Binomial conjugate prior** tracks the true moving frequency of fraud without sudden spikes or uncalibrated swings.
- The **Dynamic FP Budget Manager** continuously adjusts the decision threshold $\tau(t)$ based on the empirical false alarm rate.
- Sublinear cost weighting stabilizes gradient updates, preserving high fraud recall while enforcing strict false positive budgets.
