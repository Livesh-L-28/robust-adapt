"""
Demo 01: Concept Drift Adaptation (ALA Pillar)
==============================================
Demonstrates how ROBUST-ADAPT handles sudden and gradual concept drift
in real-time data streams without requiring manual retraining.

Key Components:
- robust_adapt.ala.AdaptiveClassifier: Vectorized Hoeffding Tree with drift awareness
- robust_adapt.ala.ReliabilityWeightedADWIN: Dynamic windowing drift detector
"""

import os
from pathlib import Path
import numpy as np

# Ensure robust-adapt is imported from PyPI package
import robust_adapt
from robust_adapt.ala import AdaptiveClassifier

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def generate_drift_stream(n_samples: int = 1200, seed: int = 42):
    """
    Generates a 2D streaming dataset with 2 distinct concept drifts:
    - Phase 1 (0 to 400): Class 0 on left (X0 < 0), Class 1 on right (X0 >= 0)
    - Phase 2 (400 to 800): Sudden Drift! Boundary inverts (X0 < 0 is Class 1)
    - Phase 3 (800 to 1200): Secondary Drift (Diagonal boundary X0 + X1 > 0)
    """
    rng = np.random.default_rng(seed)
    X = rng.normal(0, 1.5, size=(n_samples, 2))
    y = np.zeros(n_samples, dtype=int)

    for i in range(n_samples):
        if i < 400:
            y[i] = 1 if X[i, 0] >= 0.0 else 0
        elif i < 800:
            # Sudden drift: boundary flips
            y[i] = 0 if X[i, 0] >= 0.0 else 1
        else:
            # Secondary drift: diagonal decision boundary
            y[i] = 1 if (X[i, 0] + X[i, 1]) >= 0.0 else 0

    return X, y


def main():
    print("=" * 70)
    print("DEMO 01: REAL-TIME CONCEPT DRIFT ADAPTATION (ALA)")
    print(f"ROBUST-ADAPT Library Version: {robust_adapt.__version__}")
    print("=" * 70)

    # 1. Initialize Adaptive Classifier with ADWIN drift detection
    clf = AdaptiveClassifier(
        n_features=2,
        n_classes=2,
        grace_period=25,
        enable_drift_detection=True,
        delta=0.002,
        random_state=42,
    )

    X, y = generate_drift_stream(n_samples=1200)

    # Simulation metrics
    batch_size = 20
    n_batches = len(X) // batch_size
    accuracies = []
    drifts_detected = []

    print("\nStreaming 1,200 events across 3 concept phases...")
    print(f"{'Batch':<8} | {'Events':<12} | {'Current Phase':<18} | {'Rolling Acc':<12} | {'Drifts':<8}")
    print("-" * 68)

    for b in range(n_batches):
        start = b * batch_size
        end = start + batch_size
        X_b, y_b = X[start:end], y[start:end]

        # Prequential evaluation: Test BEFORE Train
        preds = clf.predict(X_b)
        batch_acc = np.mean(preds == y_b)
        accuracies.append(batch_acc)

        # Train incrementally
        prev_drift_count = clf.drift_count_
        clf.partial_fit(X_b, y_b)
        drift_occurred = clf.drift_count_ > prev_drift_count

        if drift_occurred:
            drifts_detected.append(end)

        phase_name = "Phase 1: Baseline" if end <= 400 else ("Phase 2: Drift A" if end <= 800 else "Phase 3: Drift B")

        if (b + 1) % 5 == 0 or drift_occurred:
            rolling_acc = np.mean(accuracies[-5:]) * 100
            drift_str = f"*** DRIFT DETECTED (#{clf.drift_count_}) ***" if drift_occurred else f"{clf.drift_count_}"
            print(f"{b+1:<8} | {end:<12} | {phase_name:<18} | {rolling_acc:>10.1f}% | {drift_str}")

    overall_acc = np.mean(accuracies) * 100
    print("-" * 68)
    print(f"Final Stream Accuracy: {overall_acc:.2f}%")
    print(f"Total Concept Drifts Successfully Handled: {len(drifts_detected)} drifts at samples {drifts_detected}")
    print("Conclusion: The classifier adapted to boundary flips without manual retraining.")

    # Generate visual plot if matplotlib is available
    if HAS_MATPLOTLIB:
        out_plot = Path(__file__).parent / "01_concept_drift_result.png"
        plt.figure(figsize=(10, 4.5))
        plt.plot(np.arange(batch_size, len(X) + 1, batch_size), accuracies, label="ROBUST-ADAPT Rolling Accuracy", color="#1f77b4", lw=2)
        plt.axvline(400, color="crimson", linestyle="--", label="Drift 1 (Boundary Inversion)")
        plt.axvline(800, color="purple", linestyle="--", label="Drift 2 (Diagonal Shift)")
        for d in drifts_detected:
            plt.axvline(d, color="green", linestyle=":", alpha=0.7)
        plt.title("ROBUST-ADAPT (ALA): Real-Time Concept Drift Adaptation", fontsize=12, fontweight="bold")
        plt.xlabel("Streaming Sample Index")
        plt.ylabel("Prequential Accuracy")
        plt.ylim(0.0, 1.05)
        plt.grid(True, alpha=0.3)
        plt.legend(loc="lower left")
        plt.tight_layout()
        plt.savefig(out_plot, dpi=150)
        plt.close()
        print(f"[Plot Saved] Generated visualization at: {out_plot.name}")


if __name__ == "__main__":
    main()
