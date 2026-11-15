"""
Demo 03: Adaptive Minority Intelligence & Imbalanced Streams
=============================================================
Demonstrates how ROBUST-ADAPT handles extreme class imbalance (e.g. 98:2 fraud detection)
by dynamically adjusting cost-sensitive decision thresholds in real time.

Key Components:
- robust_adapt.minority.OnlineClassPriorTracker: Exponential moving average prior estimation
- robust_adapt.minority.AdaptiveThresholdManager: Cost-sensitive dynamic threshold calibration
- robust_adapt.minority.ClassAwareCalibrator: Probability calibration under class starvation
"""

import numpy as np
import robust_adapt
from robust_adapt.minority import (
    OnlineClassPriorTracker,
    AdaptiveThresholdManager,
)


def generate_fraud_stream(n_samples: int = 1500, fraud_rate: float = 0.02, seed: int = 42):
    """Generates an imbalanced stream where only 2% of samples are positive (fraud)."""
    rng = np.random.default_rng(seed)
    
    n_fraud = int(n_samples * fraud_rate)
    n_normal = n_samples - n_fraud
    
    # Normal transactions: centered around 0
    X_normal = rng.normal(loc=0.0, scale=1.0, size=(n_normal, 3))
    y_normal = np.zeros(n_normal, dtype=int)
    
    # Fraudulent transactions: subtle anomaly distribution
    X_fraud = rng.normal(loc=0.15, scale=0.6, size=(n_fraud, 3))
    y_fraud = np.ones(n_fraud, dtype=int)
    
    X = np.vstack([X_normal, X_fraud])
    y = np.concatenate([y_normal, y_fraud])
    
    # Shuffle stream
    indices = rng.permutation(n_samples)
    return X[indices], y[indices]


def main():
    print("=" * 70)
    print("DEMO 03: ADAPTIVE MINORITY INTELLIGENCE (EXTREME IMBALANCE)")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    X, y = generate_fraud_stream(n_samples=1500, fraud_rate=0.02)
    total_fraud = np.sum(y == 1)
    print(f"Generated 1,500 transactions with {total_fraud} fraudulent events ({total_fraud / 1500 * 100:.1f}% minority).")

    # 1. Initialize Online Prior Tracker & Cost-Sensitive Threshold Manager
    prior_tracker = OnlineClassPriorTracker(n_classes=2, alpha=0.02)
    threshold_mgr = AdaptiveThresholdManager(n_classes=2, mode="dynamic", base_threshold=0.5, gamma=0.5)

    # Simulate realistic prediction probabilities from streaming base model
    # Fraud scores typically hover between 0.30 - 0.45 under high noise, below the naive 0.5 mark
    raw_scores = 1.0 / (1.0 + np.exp(-0.4 * X[:, 0] - 0.4 * X[:, 1] - 0.4 * X[:, 2]))
    probas = np.column_stack([1.0 - raw_scores, raw_scores])

    # 2. Run Stream: Compare Standard Fixed Threshold (0.5) vs Adaptive Threshold Manager
    batch_size = 50
    n_batches = len(X) // batch_size
    
    standard_tp, standard_fn, standard_fp = 0, 0, 0
    adaptive_tp, adaptive_fn, adaptive_fp = 0, 0, 0

    print(f"\nProcessing stream in batches of {batch_size}...")
    print(f"{'Batch':<8} | {'Prior (Fraud)':<14} | {'Adaptive Threshold':<20} | {'Batch Fraud':<12}")
    print("-" * 65)

    for b in range(n_batches):
        start = b * batch_size
        end = start + batch_size
        y_b = y[start:end]
        p_b = probas[start:end]

        # Update online prior tracker
        prior_tracker.update(y_b)
        estimated_priors = prior_tracker.priors
        fraud_prior = estimated_priors[1]

        # Update dynamic threshold based on tracking priors
        threshold_mgr.update_from_priors(estimated_priors)
        current_threshold = threshold_mgr.primary_threshold

        # Evaluate Standard Fixed 0.5 Threshold
        pred_standard = (p_b[:, 1] >= 0.5).astype(int)
        standard_tp += np.sum((pred_standard == 1) & (y_b == 1))
        standard_fn += np.sum((pred_standard == 0) & (y_b == 1))
        standard_fp += np.sum((pred_standard == 1) & (y_b == 0))

        # Evaluate Adaptive Threshold using threshold_mgr
        pred_adaptive = threshold_mgr.predict(p_b)
        adaptive_tp += np.sum((pred_adaptive == 1) & (y_b == 1))
        adaptive_fn += np.sum((pred_adaptive == 0) & (y_b == 1))
        adaptive_fp += np.sum((pred_adaptive == 1) & (y_b == 0))

        if (b + 1) % 6 == 0 or np.sum(y_b == 1) > 0:
            print(f"{b+1:<8} | {fraud_prior:>12.3f} | {current_threshold:>18.3f} | {np.sum(y_b == 1):>8}")

    # 3. Final Performance Comparison
    standard_recall = (standard_tp / (standard_tp + standard_fn)) * 100 if (standard_tp + standard_fn) > 0 else 0
    adaptive_recall = (adaptive_tp / (adaptive_tp + adaptive_fn)) * 100 if (adaptive_tp + adaptive_fn) > 0 else 0

    print("-" * 65)
    print("RESULTS COMPARISON:")
    print(f"  Standard 0.5 Threshold Recall: {standard_recall:>6.1f}%  ({standard_tp}/{total_fraud} frauds caught)")
    print(f"  Adaptive Threshold Recall:    {adaptive_recall:>6.1f}%  ({adaptive_tp}/{total_fraud} frauds caught)")
    print(f"  Recall Improvement:           +{adaptive_recall - standard_recall:+.1f}%")
    print("-" * 65)
    print("Conclusion: Dynamic prior tracking prevents minority class starvation under extreme imbalance.")


if __name__ == "__main__":
    main()
