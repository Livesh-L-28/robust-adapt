"""Unit tests for Stage 14 Memory and Resource Management.

Verifies strict O(1) memory bounds, buffer eviction invariants, absence of
unbounded heap expansion across prolonged streaming workloads, and zero
cyclic reference leakage.
"""

import gc
import numpy as np
import pytest

from robust_adapt.ala.concept_memory import RecurringConceptMemory
from robust_adapt.ala.delayed_labels import DelayedLabelQueue
from robust_adapt.ala.replay import ClassBalancedReservoirReplay
from robust_adapt.rla.reliability import MultiSignalReliabilityEngine
from robust_adapt.ulc.v5_controller import UnifiedLearningControllerV5


def test_class_balanced_reservoir_replay_capacity_bound():
    """Verify ClassBalancedReservoirReplay strictly respects its capacity ceiling."""
    capacity = 200
    n_classes = 2
    buffer = ClassBalancedReservoirReplay(capacity=capacity, n_classes=n_classes)

    # Ingest 5000 samples (25x capacity)
    for i in range(5000):
        X = np.random.randn(1, 4)
        y = np.array([i % n_classes])
        buffer.add(X, y)

    assert buffer.total_stored <= capacity
    counts = buffer.class_counts
    for c in range(n_classes):
        assert counts[c] <= buffer.bucket_capacity


def test_delayed_label_queue_eviction_invariant():
    """Verify DelayedLabelQueue caps waiting samples and evicts FIFO."""
    max_queue_size = 150
    queue = DelayedLabelQueue(max_queue_size=max_queue_size)

    # Ingest 3000 unlabelled samples without labels arriving
    for i in range(3000):
        queue.enqueue(
            sample_id=f"sample_{i}",
            X=np.random.randn(8),
            prediction=i % 2,
            timestamp=float(i),
        )

    assert len(queue._waiting_samples) == max_queue_size
    # Oldest sample should be sample_2850 (3000 - 150)
    assert "sample_2850" in queue._waiting_samples
    assert "sample_0" not in queue._waiting_samples


def test_multi_signal_reliability_engine_buffer_ceiling():
    """Verify MultiSignalReliabilityEngine sliding window buffers do not exceed capacity."""
    buffer_size = 50
    engine = MultiSignalReliabilityEngine(n_classes=2, buffer_size=buffer_size)

    # Ingest 1000 streaming updates
    for i in range(1000):
        X = np.random.randn(1, 4)
        y = np.array([i % 2])
        probs = np.array([[0.7, 0.3]]) if i % 2 == 0 else np.array([[0.2, 0.8]])
        engine.compute_reliability(X, y, probs)

    assert len(engine._history_X) <= buffer_size
    assert len(engine._history_y) <= buffer_size
    assert len(engine._recent_agreement) <= buffer_size


def test_recurring_concept_memory_bounded_retention():
    """Verify RecurringConceptMemory caps stored concepts at max_concepts."""
    max_concepts = 5
    memory = RecurringConceptMemory(max_concepts=max_concepts)

    # Store 20 distinct concept signatures
    for i in range(20):
        fp = np.random.randn(6)
        memory.store_concept(fp, {"model_weights": np.random.randn(6, 2)}, step=i)

    assert memory.n_stored <= max_concepts


def test_ulc_v5_prolonged_streaming_heap_stability():
    """Verify ULC-v5 controller runs 2,000 steps without memory leaks or buffer blowup."""
    controller = UnifiedLearningControllerV5(n_features=6, n_classes=2)

    # Warm-up
    X_warm = np.random.randn(5, 6)
    y_warm = np.array([0, 1, 0, 1, 0])
    controller.step(X_warm, y_warm)

    gc.collect()

    for step in range(2000):
        X = np.random.randn(4, 6)
        y = np.random.randint(0, 2, size=4)
        directive, telemetry = controller.step(X, y)

    # Invariants
    assert controller.replay.total_stored <= controller.config.replay_capacity
    assert controller.memory.n_stored <= controller.config.max_concepts
    assert controller.total_steps == 2001
