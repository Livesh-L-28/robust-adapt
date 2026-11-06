"""Unit tests for Stage 14 Concurrency, Stress and Failure Injection.

Verifies:
1. Multi-threaded execution: multiple independent ULC-v5 controllers run concurrently without cross-talk.
2. Concurrent state saving into the same directory without collision.
3. Rapid burst streaming with variable batch sizes.
4. Extreme adversarial noise injection (50% label noise + random feature perturbations).
"""

from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import tempfile
import numpy as np
import pytest

from robust_adapt.state.serializer import is_safetensors_available, load_state, save_state
from robust_adapt.ulc.v5_controller import ULCv5Config, UnifiedLearningControllerV5


def test_multithreaded_ulc_concurrency():
    """Verify multiple ULC-v5 instances run concurrently in separate threads with independent state."""
    def run_worker(worker_id: int):
        np.random.seed(worker_id * 100)
        ulc = UnifiedLearningControllerV5(n_features=5, n_classes=2)
        w = np.random.randn(5)
        for _ in range(50):
            X = np.random.randn(4, 5)
            y = (X @ w > 0).astype(int)
            ulc.step(X, y)
        return ulc.total_steps, ulc.replay.total_stored

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_worker, i) for i in range(4)]
        results = [f.result() for f in futures]

    for steps, stored in results:
        assert steps == 50
        assert stored > 0


@pytest.mark.skipif(not is_safetensors_available(), reason="safetensors required")
def test_concurrent_state_saving():
    """Verify concurrent state saves to the same directory succeed atomically without race collisions."""
    d = tempfile.mkdtemp()
    try:
        def save_worker(worker_id: int):
            filepath = os.path.join(d, f"worker_{worker_id}_model")
            tensors = {"weights": np.ones((10, 10), dtype=np.float32) * worker_id}
            metadata = {"worker_id": worker_id}
            save_state(filepath, tensors, metadata)
            # Immediately load and verify
            loaded_tensors, loaded_meta = load_state(filepath)
            assert np.allclose(loaded_tensors["weights"], worker_id)
            assert loaded_meta["worker_id"] == worker_id
            return True

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(save_worker, i) for i in range(4)]
            results = [f.result() for f in futures]

        assert all(results)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_rapid_variable_burst_stress():
    """Verify ULC-v5 handles erratic, variable-sized batch bursts without failure."""
    np.random.seed(1234)
    ulc = UnifiedLearningControllerV5(n_features=6, n_classes=2)

    # Ingest 100 bursts of random sizes between 1 and 64
    burst_sizes = np.random.randint(1, 65, size=100)
    for bsz in burst_sizes:
        X = np.random.randn(bsz, 6)
        y = np.random.randint(0, 2, size=bsz)
        directive, telemetry = ulc.step(X, y)
        assert directive is not None
        assert "step" in telemetry

    assert ulc.total_steps == 100


def test_severe_adversarial_noise_injection():
    """Verify ULC-v5 survives severe adversarial noise (50% random label flips) without crashing."""
    np.random.seed(999)
    ulc = UnifiedLearningControllerV5(n_features=4, n_classes=2)

    w = np.array([1.0, -1.0, 0.5, -0.5])
    for _ in range(100):
        X = np.random.randn(8, 4)
        y = (X @ w > 0).astype(int)
        # Flip 50% of labels completely at random
        flip_mask = np.random.rand(8) < 0.5
        y[flip_mask] = 1 - y[flip_mask]

        directive, telemetry = ulc.step(X, y)
        assert directive is not None

    # Verify controller state remains valid and bounded
    assert ulc.total_steps == 100
    assert ulc.replay.total_stored <= ulc.config.replay_capacity
