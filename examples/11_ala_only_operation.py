"""Example 11: Standalone ALA (Adaptive Learning Algorithms) Operation.

Problem Description:
-------------------
Demonstrates using Pillar 1 (ALA) in complete isolation without importing or configuring
RLA, RAO, or ULC. This highlights ROBUST-ADAPT's modular decoupled architecture: developers
needing only streaming Hoeffding trees, ADWIN drift detection, and Concept Memory for
recurring concept re-identification can run ALA with zero external overhead.

Dataset:
--------
Synthetic 6-dimensional streaming data featuring a recurring concept schedule:
- Steps 1-20: Concept A ("Summer")
- Steps 21-40: Concept B ("Winter")
- Steps 41-60: Recurring Concept A ("Summer" returns)

Expected Output:
----------------
Concept memory stores Concept A at step 20; recognizes recurring Concept A at step 41;
restores previous state instantly without re-training from scratch.

Limitations:
------------
Pure ALA assumes clean labels (does not filter adversarial label corruption).
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_batch(n_samples: int, n_features: int, concept: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    if concept == "A":
        # Concept A: mean offset +0.5 on features 0, 1
        X[:, 0] += 0.5
        X[:, 1] += 0.5
        weights = np.array([2.0, -1.8, 0.0, 0.0, 0.5, -0.4][:n_features], dtype=np.float64)
    else:
        # Concept B: mean offset -0.5 on features 2, 3
        X[:, 2] -= 0.5
        X[:, 3] -= 0.5
        weights = np.array([0.0, 0.0, 2.0, -1.8, 0.5, -0.4][:n_features], dtype=np.float64)

    y = (np.dot(X, weights) > 0.0).astype(np.int64)
    return X, y


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 11: Standalone ALA Operation (Pillar 1 Only)")
    print("=" * 70)

    n_features = 6
    n_classes = 2
    batch_size = 50

    # 1. Instantiate pure ALA components
    classifier = aml.AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=15,
        delta=1e-3,
        random_state=42
    )

    concept_memory = aml.ConceptMemory(max_concepts=5, similarity_threshold=0.75)

    print("[Config] Modular ALA | Recurring Stream: Concept A -> Concept B -> Concept A")
    print("-" * 70)

    start_time = time.perf_counter()
    restored_step = None

    # Phase 1: Train on Concept A (Steps 1-20)
    for step in range(1, 21):
        X_batch, y_batch = generate_batch(batch_size, n_features, concept="A", seed=1100 + step)
        classifier.partial_fit(X_batch, y_batch)

    # Checkpoint Concept A snapshot in concept memory
    concept_memory.store_concept(
        concept_id="concept_A",
        model_state=classifier.state_dict(),
        X=X_batch,
        y=y_batch,
        n_classes=n_classes
    )
    print(f"Phase 1 Complete | Stored 'concept_A' in ConceptMemory (Stored: {concept_memory.n_stored})")

    # Phase 2: Abrupt drift to Concept B (Steps 21-40)
    classifier._init_components()
    for step in range(21, 41):
        X_batch, y_batch = generate_batch(batch_size, n_features, concept="B", seed=1100 + step)
        classifier.partial_fit(X_batch, y_batch)

    print(f"Phase 2 Complete | Trained on Concept B | Current Samples Seen: {classifier.samples_seen_}")

    # Phase 3: Concept A returns (Steps 41-60)
    X_return, y_return = generate_batch(batch_size, n_features, concept="A", seed=1150)

    # Query concept memory for recurring concept matching X_return
    match = concept_memory.query_recurring(X_return, y_return)

    if match is not None:
        best_match_id, saved_state, sim_score = match
        print(f"Phase 3 Concept Reappearance | Matched: '{best_match_id}' (Similarity: {sim_score:.2f})")
        if best_match_id == "concept_A":
            classifier.load_state_dict(saved_state)
            restored_step = 41
            print("-> Successfully restored 'concept_A' state from ConceptMemory instantly!")
    else:
        print("Phase 3: No matching concept found in memory.")

    elapsed = time.perf_counter() - start_time

    # Evaluate on Concept A test set
    X_test_a, y_test_a = generate_batch(300, n_features, concept="A", seed=999)
    test_acc_a = classifier.score(X_test_a, y_test_a)

    print("-" * 70)
    print(f"Restored Concept A Accuracy:   {test_acc_a:.2%}")
    print(f"Total Concept Memory Entries:  {concept_memory.n_stored}")
    print(f"Execution Time:                {elapsed * 1000:.2f} ms")
    print("=" * 70)

    assert test_acc_a >= 0.70, f"Expected restored test accuracy >= 70%, got {test_acc_a:.2%}"
    assert restored_step == 41, "Expected concept_A to be restored from memory"
    print("STATUS: SUCCESS - Standalone ALA operation verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
