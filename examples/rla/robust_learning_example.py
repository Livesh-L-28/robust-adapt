"""Executable example for Phase 9: Robust Learning Algorithms (RLA).

Demonstrates:
1. Scoring instance reliability with DensityAwareMarginScorer.
2. Protecting isolated tail minority instances against noise deletion.
3. Computing Symmetric Cross Entropy loss and bounded gradients.
"""

import numpy as np
from robust_adapt.rla import DensityAwareMarginScorer, SymmetricCrossEntropyLoss, ClassBalancedWeights


def run_rla_demo() -> None:
    print("=" * 60)
    print("ROBUST-ADAPT — Phase 9 RLA Robust Learning Demo")
    print("=" * 60)

    rng = np.random.default_rng(42)
    n_samples = 30
    n_features = 4
    n_classes = 3

    # Dense majority cluster for class 0
    X_dense = rng.normal(loc=0.0, scale=0.3, size=(25, n_features))
    logits_dense = np.tile([3.0, -1.0, -1.0], (25, 1))
    y_dense = np.zeros(25, dtype=np.int64)
    # Corrupt 2 dense instances with class 1 label
    y_dense[23] = 1
    y_dense[24] = 1

    # Isolated minority instances for class 2
    X_rare = rng.normal(loc=5.0, scale=0.3, size=(5, n_features))
    logits_rare = np.tile([-1.0, -1.0, 1.5], (5, 1))
    y_rare = np.full(5, 2, dtype=np.int64)

    X = np.vstack([X_dense, X_rare])
    logits = np.vstack([logits_dense, logits_rare])
    y = np.concatenate([y_dense, y_rare])

    # 1. Scorer Evaluation
    scorer = DensityAwareMarginScorer(n_classes=n_classes, n_neighbors=5, gamma=1.0)
    reliabilities = scorer.score_samples(X, logits, y)

    print("\n1. Sample Reliability Scoring:")
    print(f"Clean Majority Mean Reliability:    {np.mean(reliabilities[:23]):.4f}")
    print(f"Corrupted Majority Mean Reliability: {np.mean(reliabilities[23:25]):.4f}")
    print(f"Isolated Rare Minority Reliability:  {np.mean(reliabilities[25:]):.4f}")

    # 2. Class Balanced Weights
    class_counts = np.array([23, 2, 5], dtype=np.float64)
    cb = ClassBalancedWeights(beta=0.99)
    weights = cb.compute_weights(class_counts)
    print("\n2. Class-Balanced Effective Sample Weights:")
    for c in range(n_classes):
        print(f"Class {c} (count={int(class_counts[c])}): Weight = {weights[c]:.4f}")

    # 3. Symmetric Cross Entropy Loss Evaluation
    sce = SymmetricCrossEntropyLoss(alpha=1.0, beta=0.5)
    loss, grads = sce.forward(logits, y, sample_weights=reliabilities)
    grad_norm = float(np.linalg.norm(grads))
    print("\n3. Robust Loss Computation:")
    print(f"Symmetric Cross Entropy Loss: {loss:.4f}")
    print(f"Logit Gradient Frobenius Norm: {grad_norm:.4f}")

    print("\nRLA Demonstration successfully completed.")


if __name__ == "__main__":
    run_rla_demo()

