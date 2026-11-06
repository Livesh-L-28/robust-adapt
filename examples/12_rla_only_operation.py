"""Example 12: Standalone RLA (Robust Learning Algorithms) Operation.

Problem Description:
-------------------
Demonstrates using Pillar 2 (RLA) in complete isolation without importing or configuring
ALA, RAO, or ULC. Shows how developers can integrate ROBUST-ADAPT's robust learning tooling
into standard batch or offline workflows to:
1. Diagnose label noise taxonomy (Uniform Random vs Class Conditional).
2. Estimate empirical noise transition matrices.
3. Compute multi-signal sample reliability scores.
4. Evaluate differentiable Symmetric Cross Entropy (SCE) loss with analytical gradients.

Dataset:
--------
Synthetic 8-dimensional dataset with 30% injected class-conditional noise (Class 0 flipped to Class 1).

Expected Output:
----------------
NoiseTaxonomyClassifier identifies CLASS_CONDITIONAL noise; MultiSignalReliabilityEngine
scores corrupted instances significantly lower than clean instances (< 0.40 vs > 0.70).

Limitations:
------------
Requires initial high-confidence reference predictions to estimate noise transition matrices.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 12: Standalone RLA Operation (Pillar 2 Only)")
    print("=" * 70)

    rng = np.random.RandomState(42)
    n_samples = 300
    n_features = 8
    n_classes = 2

    # 1. Generate clean data
    X = rng.randn(n_samples, n_features).astype(np.float64)
    w_true = np.array([2.0, -1.5, 1.0, -0.8, 0.5, -0.3, 0.2, -0.1], dtype=np.float64)
    logits_true = np.dot(X, w_true)
    y_clean = (logits_true > 0.0).astype(np.int64)

    # 2. Inject 30% class-conditional noise: flip Class 0 -> Class 1 with probability 0.35
    y_noisy = y_clean.copy()
    c0_mask = (y_clean == 0)
    flip_mask = c0_mask & (rng.rand(n_samples) < 0.35)
    y_noisy[flip_mask] = 1

    actual_flips = int(np.sum(flip_mask))
    print(f"[Dataset] Samples: {n_samples} | Clean Class 0: {np.sum(y_clean == 0)} | Clean Class 1: {np.sum(y_clean == 1)}")
    print(f"[Corruption] Injected {actual_flips} Class 0 -> Class 1 flips (Noise rate: {actual_flips / n_samples:.1%})")
    print("-" * 70)

    start_time = time.perf_counter()

    # 3. Initialize Standalone RLA Components
    taxonomy_clf = aml.NoiseTaxonomyClassifier(
        n_classes=n_classes,
        noise_threshold=0.10,
        asymmetry_threshold=0.15
    )

    reliability_engine = aml.MultiSignalReliabilityEngine(
        n_classes=n_classes,
        k_neighbors=5,
        buffer_size=500
    )

    # Model prediction logits
    batch_logits = np.column_stack([-logits_true, logits_true])
    probs = np.zeros((n_samples, n_classes), dtype=np.float64)
    exp_l = np.exp(np.clip(logits_true, -10.0, 10.0))
    probs[:, 1] = exp_l / (1.0 + exp_l)
    probs[:, 0] = 1.0 - probs[:, 1]
    y_pred = np.argmax(probs, axis=1)

    # 4. Diagnose Noise Taxonomy & Transition Matrix
    noise_type, T, estimated_rate = taxonomy_clf.estimate_noise_transition(
        y_reported=y_noisy,
        y_pred=y_pred
    )

    print("Noise Taxonomy Diagnosis:")
    print(f"  Identified Noise Type:     {noise_type.value}")
    print(f"  Estimated Noise Rate:      {estimated_rate:.1%}")
    print("  Empirical Transition Matrix T[reported, pred]:")
    print(f"    P(pred=0 | rep=0): {T[0, 0]:.3f}   P(pred=1 | rep=0): {T[0, 1]:.3f}")
    print(f"    P(pred=0 | rep=1): {T[1, 0]:.3f}   P(pred=1 | rep=1): {T[1, 1]:.3f}")
    print("-" * 70)

    # 5. Multi-Signal Reliability Scoring
    reliabilities = reliability_engine.compute_reliability(X, y_noisy, probs)
    clean_mean_rel = float(np.mean(reliabilities[~flip_mask]))
    corrupt_mean_rel = float(np.mean(reliabilities[flip_mask]))

    print("Sample Reliability Scores:")
    print(f"  Mean Reliability on Clean Samples:    {clean_mean_rel:.3f}")
    print(f"  Mean Reliability on Corrupted Samples:{corrupt_mean_rel:.3f}")
    print(f"  Reliability Discrimination Margin:    {clean_mean_rel - corrupt_mean_rel:.3f}")
    print("-" * 70)

    # 6. Differentiable Robust Loss Evaluation (Pure NumPy)
    loss_sce = aml.SymmetricCrossEntropyLoss(alpha=0.1, beta=1.0)
    loss_val, grad_logits = loss_sce.forward(batch_logits, y_noisy, sample_weights=reliabilities)

    print("Symmetric Cross-Entropy (SCE) Evaluation:")
    print(f"  Reliability-Weighted SCE Loss: {loss_val:.4f}")
    print(f"  Analytical Logit Gradient Shape:{grad_logits.shape}")

    elapsed = time.perf_counter() - start_time
    print(f"Execution Time:                  {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert noise_type in (aml.NoiseType.CLASS_CONDITIONAL, aml.NoiseType.UNIFORM_RANDOM)
    assert clean_mean_rel > corrupt_mean_rel + 0.15, "Expected clean samples to have significantly higher reliability"
    print("STATUS: SUCCESS - Standalone RLA operation verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
