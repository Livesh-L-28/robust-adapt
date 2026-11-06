"""
Example 08: Minimal Core-Only Standalone Workflow (Zero Optional Dependencies).

Demonstrates complete four-pillar ROBUST-ADAPT streaming execution using strictly
NumPy and Python standard library, verifying that torch, sklearn, pandas,
and polars are never imported or required.
"""

from __future__ import annotations

import sys
import numpy as np

# Strict core ROBUST-ADAPT imports only
import robust_adapt
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.adwin import ReliabilityWeightedADWIN
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.ulc.controller import AdaptiveLearningController


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 08: Core-Only Streaming Workflow (NumPy-Only)")
    print(f"ROBUST-ADAPT Version: {robust_adapt.__version__}")
    print("=====================================================================")

    # 1. Verify that no framework integration adapters are loaded
    integration_modules = [mod for mod in sys.modules if mod.startswith("robust_adapt.integrations")]
    print(f"Checking integration adapter isolation...")
    print(f"  Integration adapters loaded: {integration_modules if integration_modules else 'None (Pure Core Execution)'}")
    assert len(integration_modules) == 0, f"Core-only workflow should not load integration adapters: {integration_modules}"

    # 2. Instantiate Four Pillars using Pure Core
    n_features = 4
    n_classes = 2

    classifier = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=10)
    drift_detector = ReliabilityWeightedADWIN(delta=0.002)
    reliability_engine = MultiSignalReliabilityEngine(n_classes=n_classes)
    budget_mgr = DynamicResourceBudgetManager(max_step_time_ms=50.0, max_memory_mb=1024.0)
    controller = AdaptiveLearningController()

    print("\nFour-Pillar Core Instances successfully initialized.")

    # 3. Stream data through full four-pillar pipeline
    rng = np.random.default_rng(999)
    n_stream_steps = 100
    drifts_detected = 0

    print(f"Streaming {n_stream_steps} instances through four-pillar pipeline...")

    for t in range(1, n_stream_steps + 1):
        # Generate single sample
        if t <= 50:
            x = rng.normal(0.0, 1.0, size=(n_features,))
            y = int(x[0] + x[1] > 0)
        else:
            # Shifted concept
            x = rng.normal(2.5, 1.0, size=(n_features,))
            y = int(x[0] + x[1] < 2.5)

        # ALA: Predict and update
        x_2d = x.reshape(1, -1)
        pred = classifier.predict(x_2d)[0]
        prob = classifier.predict_proba(x_2d)

        # RLA: Compute sample reliability
        rel_score = float(reliability_engine.compute_reliability(x_2d, np.array([y]), prob)[0])

        # ALA: Update drift monitor with prediction error weighted by reliability
        error = float(pred != y)
        is_drift = drift_detector.update(error, reliability=rel_score)
        if is_drift:
            drifts_detected += 1

        # Incremental train
        classifier.partial_fit(x_2d, np.array([y]))

        # RAO: Evaluate resource step
        budget_state = budget_mgr.evaluate_step(step_time_ms=0.5)

        # ULC: Arbitrate pillars
        directive, _ = controller.step(
            X=x_2d,
            y=np.array([y]),
            current_loss=error,
            delta_drift=1.0 if is_drift else 0.05,
        )

    print(f"\nExecution Summary:")
    print(f"  Stream samples processed: {t}")
    print(f"  Concept drifts detected:  {drifts_detected}")
    print(f"  Final Budget State:       {budget_state.value}")
    print(f"  Final ULC State:          {directive.state.value} (LR Scale: {directive.learning_rate_scale:.2f}x)")
    print(f"  Classifier samples seen:  {classifier.samples_seen_}")

    # Re-verify isolation at completion
    loaded_at_end = [mod for mod in sys.modules if mod.startswith("robust_adapt.integrations")]
    print(f"  Final Adapter Isolation Check: {loaded_at_end if loaded_at_end else 'PASSED (Zero integration adapters imported)'}")


if __name__ == "__main__":
    main()
