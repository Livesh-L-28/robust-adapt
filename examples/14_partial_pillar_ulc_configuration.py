"""Example 14: Partial-Pillar ULC Configuration & Modularity.

Problem Description:
-------------------
Demonstrates the architectural modularity of UnifiedLearningControllerV4_1 (ULC-v4.1).
In production, systems frequently operate with a subset of pillars active:
- Setup A: ALA + RLA (Adaptive + Robust, without RAO resource constraints).
- Setup B: ALA + RAO (Adaptive + Resource-Aware, assuming clean data without RLA).
- Setup C: Minimal Standalone ULC (Classifier-only, with external telemetry).

ULC-v4.1 gracefully detects which sub-components are present, safely defaults missing
telemetry channels, and emits deterministic action directives across all configurations.

Dataset:
--------
Synthetic 6-dimensional streaming data evaluated across all 3 partial pillar configurations.

Expected Output:
----------------
All 3 partial pillar configurations initialize and execute steps without error, emitting valid directives.

Limitations:
------------
Disabling RLA leaves the system vulnerable to noise bursts; disabling RAO removes memory budgeting.
"""

import sys
import time
import numpy as np
import robust_adapt as aml


def generate_batch(n_samples: int, n_features: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, n_features).astype(np.float64)
    weights = np.array([1.5, -1.2, 0.9, -0.7, 0.4, -0.3][:n_features], dtype=np.float64)
    y = (np.dot(X, weights) > 0.0).astype(np.int64)
    return X, y


def test_setup_a(X: np.ndarray, y: np.ndarray) -> str:
    """Setup A: ALA + RLA (Adaptive + Robust, RAO disabled)."""
    classifier = aml.AdaptiveClassifier(n_features=6, n_classes=2, random_state=42)
    prior_tracker = aml.OnlineClassPriorTracker(n_classes=2)
    threshold_mgr = aml.AdaptiveThresholdManager(n_classes=2)

    controller = aml.UnifiedLearningControllerV4_1(
        classifier=classifier,
        prior_tracker=prior_tracker,
        threshold_manager=threshold_mgr,
        budget_manager=None,   # RAO explicitly omitted
        optimizer=None        # RAO explicitly omitted
    )

    directive, telemetry = controller.step(X, y)
    return directive.state.value


def test_setup_b(X: np.ndarray, y: np.ndarray) -> str:
    """Setup B: ALA + RAO (Adaptive + Resource-Aware, RLA disabled)."""
    classifier = aml.AdaptiveClassifier(n_features=6, n_classes=2, random_state=42)
    budget_mgr = aml.DynamicResourceBudgetManager(max_step_time_ms=50.0)

    controller = aml.UnifiedLearningControllerV4_1(
        classifier=classifier,
        budget_manager=budget_mgr,
        prior_tracker=None,      # Minority/RLA omitted
        threshold_manager=None   # RLA omitted
    )

    directive, telemetry = controller.step(X, y)
    return directive.state.value


def test_setup_c(X: np.ndarray, y: np.ndarray) -> str:
    """Setup C: Minimal Classifier-Only ULC."""
    classifier = aml.AdaptiveClassifier(n_features=6, n_classes=2, random_state=42)

    controller = aml.UnifiedLearningControllerV4_1(
        classifier=classifier
    )

    directive, telemetry = controller.step(X, y)
    return directive.state.value


def main() -> int:
    print("=" * 70)
    print("ROBUST-ADAPT Example 14: Partial-Pillar ULC Configuration & Modularity")
    print("=" * 70)

    n_features = 6
    batch_size = 50
    X, y = generate_batch(batch_size, n_features, seed=42)

    start_time = time.perf_counter()

    # Test Setup A
    state_a = test_setup_a(X, y)
    print(f"Setup A (ALA + RLA, no RAO):      Directive State = {state_a}")

    # Test Setup B
    state_b = test_setup_b(X, y)
    print(f"Setup B (ALA + RAO, no RLA):      Directive State = {state_b}")

    # Test Setup C
    state_c = test_setup_c(X, y)
    print(f"Setup C (Minimal Classifier-Only):Directive State = {state_c}")

    elapsed = time.perf_counter() - start_time
    print("-" * 70)
    print(f"All Partial Pillar Configurations Verified in {elapsed * 1000:.2f} ms")
    print("=" * 70)

    valid_states = {"STABLE", "ELEVATED_VARIANCE", "WARNING", "CONFIRMED_DRIFT", "NOISE_BURST"}
    assert state_a in valid_states, f"Unexpected state in Setup A: {state_a}"
    assert state_b in valid_states, f"Unexpected state in Setup B: {state_b}"
    assert state_c in valid_states, f"Unexpected state in Setup C: {state_c}"

    print("STATUS: SUCCESS - Partial-pillar ULC configurations verified.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
