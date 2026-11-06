"""Example 15: ALA 3.0 Recurring Concept Adaptation & Episodic Memory Restoration.

Demonstrates:
- ReliabilityWeightedADWIN detecting cyclical drift between Concept A and Concept B
- ConceptFingerprinter computing spatial distribution centroids
- RecurringConceptMemory matching historical concepts and restoring previous states
- ClassBalancedReservoirReplay stabilizing prequential accuracy
"""

import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner


def main() -> None:
    print("=== Example 15: ALA 3.0 Recurring Concepts ===")
    rng = np.random.RandomState(42)

    learner = ALA30AdaptiveLearner(
        n_features=4,
        n_classes=2,
        grace_period=20,
        delta=0.005,
        max_concepts=5,
        similarity_threshold=0.80,
    )

    # 1. Concept A (separation on feature 0)
    print("\n--- Training on Concept A (Steps 1-20) ---")
    for step in range(20):
        X = rng.randn(30, 4)
        y = (X[:, 0] > 0).astype(int)
        telemetry = learner.update(X, y)
        if step % 5 == 0:
            print(f"Step {step:2d} | Action: {telemetry['action']:25s} | Acc: {telemetry['batch_acc']:.2f}")

    # 2. Concept B (abrupt shift to feature 1)
    print("\n--- Transition to Concept B (Steps 21-40) ---")
    for step in range(20, 40):
        X = rng.randn(30, 4)
        y = (X[:, 1] > 0).astype(int)
        telemetry = learner.update(X, y)
        if step % 5 == 0:
            print(f"Step {step:2d} | Action: {telemetry['action']:25s} | Acc: {telemetry['batch_acc']:.2f}")

    # 3. Concept A Re-introduction (cyclical recurrence)
    print("\n--- Re-introducing Concept A (Steps 41-60) ---")
    for step in range(40, 60):
        X = rng.randn(30, 4)
        y = (X[:, 0] > 0).astype(int)
        telemetry = learner.update(X, y)
        if "RECURRING_RESTORE" in telemetry["action"] or step % 5 == 0:
            print(f"Step {step:2d} | Action: {telemetry['action']:25s} | Sim: {telemetry['similarity']:.3f} | Acc: {telemetry['batch_acc']:.2f}")

    print(f"\nFinal Summary: Resets={learner.drift_resets}, Restorations={learner.recurring_restorations}")
    print("ALA 3.0 execution completed successfully.")


if __name__ == "__main__":
    main()
