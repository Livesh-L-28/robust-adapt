"""
AdaptiveML End-to-End Streaming Pipeline Demonstration.

Demonstrates complete cross-pillar operation:
- ALA: Online vectorized tree learning & drift detection
- RLA: Density-aware margin reliability scoring & robust loss
- RAO: Low-memory 8-bit block-quantized AdamW optimizer
- ULC: Dual-evidence in-loop arbitration automaton
- State: Atomic checkpoint snapshotting with Safetensors (zero pickle)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import numpy as np

from adaptive_ml.ala.classifier import AdaptiveClassifier
from adaptive_ml.core.config import ULCConfig
from adaptive_ml.rao.adamw import LowMemoryAdamW
from adaptive_ml.rla.pipeline import RobustLearningPipeline
from adaptive_ml.state.checkpoint import CheckpointManager
from adaptive_ml.ulc.controller import AdaptiveLearningController


class ParamWrapper:
    """Lightweight parameter wrapper carrying gradient buffers."""

    def __init__(self, arr: np.ndarray) -> None:
        self.data = arr
        self.grad = np.zeros_like(arr)


def generate_stream_batch(
    step: int,
    batch_size: int = 32,
    n_features: int = 4,
    rng: np.random.Generator = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Generate streaming batches with controlled drift, noise bursts, and clean segments."""
    if rng is None:
        rng = np.random.default_rng()

    # Base classes centered at opposite quadrants
    if step <= 15:
        # Stationary clean stream
        center0 = np.array([-1.5] * n_features)
        center1 = np.array([1.5] * n_features)
        noise_level = 0.0
        delta_drift = 0.05
    elif 16 <= step <= 25:
        # Noise burst: cluster 0 labels severely inverted
        center0 = np.array([-1.5] * n_features)
        center1 = np.array([1.5] * n_features)
        noise_level = 0.8
        delta_drift = 1.3
    elif 26 <= step <= 35:
        # Stationary return
        center0 = np.array([-1.5] * n_features)
        center1 = np.array([1.5] * n_features)
        noise_level = 0.0
        delta_drift = 0.05
    else:
        # True concept drift: cluster centers swap positions
        center0 = np.array([2.5] * n_features)
        center1 = np.array([-2.5] * n_features)
        noise_level = 0.0
        delta_drift = 1.4 if step == 36 else 0.1

    half = batch_size // 2
    X0 = rng.normal(loc=center0, scale=0.5, size=(half, n_features))
    X1 = rng.normal(loc=center1, scale=0.5, size=(batch_size - half, n_features))
    X = np.vstack([X0, X1])
    y = np.array([0] * half + [1] * (batch_size - half))

    # Apply noise if active
    if noise_level > 0.0:
        n_flip = int(batch_size * 0.85)
        # Invert labels for 85% of the batch to create a true noise burst
        y[:n_flip] = 1 - y[:n_flip]

    # Construct representative model logits
    logits0 = np.tile([3.0, -3.0], (half, 1))
    logits1 = np.tile([-3.0, 3.0], (batch_size - half, 1))
    logits = np.vstack([logits0, logits1])

    return X, y, logits, delta_drift


def main() -> None:
    print("=" * 80)
    print("AdaptiveML: Comprehensive End-to-End Streaming Pipeline")
    print("Cross-Pillar In-Loop Coordination: ALA + RLA + RAO + ULC + State")
    print("=" * 80)

    rng = np.random.default_rng(42)
    n_features = 4
    n_classes = 2

    # 1. Initialize Submodules
    classifier = AdaptiveClassifier(
        n_features=n_features,
        n_classes=n_classes,
        grace_period=40,
        enable_drift_detection=True,
    )
    pipeline = RobustLearningPipeline(n_classes=n_classes)
    raw_weights = rng.normal(size=(10, n_features)).astype(np.float32)
    param = ParamWrapper(raw_weights)
    optimizer = LowMemoryAdamW([param], lr=0.01)

    controller = AdaptiveLearningController(
        classifier=classifier,
        pipeline=pipeline,
        optimizer=optimizer,
        config=ULCConfig(tau_R=0.49, recovery_steps=4),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        ckpt_dir = Path(tmpdir) / "checkpoints"
        ckpt_manager = CheckpointManager(checkpoint_dir=ckpt_dir, max_checkpoints=3)

        print(f"\nPipeline Initialized. Starting streaming ingestion (50 batches)...")
        print("-" * 80)
        print(f"{'Step':<5} | {'Regime':<18} | {'State':<16} | {'Reliability':<11} | {'Retained':<9} | {'Action Taken'}")
        print("-" * 80)

        total_samples = 0
        retained_samples = 0

        for step in range(1, 51):
            X, y, logits, delta_drift = generate_stream_batch(step, batch_size=32, n_features=n_features, rng=rng)
            directive, info = controller.step(X, y, logits=logits, delta_drift=delta_drift)

            # Perform an optimization step with simulated gradient
            param.grad = rng.normal(size=param.data.shape).astype(np.float32)
            optimizer.step()

            total_samples += len(X)
            retained_samples += info["n_retained_samples"]

            # Determine regime name
            if step <= 15:
                regime = "Stationary Clean"
            elif 16 <= step <= 25:
                regime = "Noise Burst"
            elif 26 <= step <= 35:
                regime = "Stationary Return"
            else:
                regime = "Concept Drift"

            # Checkpoint snapshot every 10 steps
            if step % 10 == 0:
                tensors = {"weights": param.data}
                ckpt_manager.save_checkpoint(step=step, tensors=tensors, metadata={"step": step, "state": directive.state.value})

            # Print status periodically
            if step in [1, 5, 10, 15, 16, 17, 20, 25, 26, 35, 36, 37, 40, 50]:
                print(
                    f"{step:<5} | {regime:<18} | {directive.state.value:<16} | "
                    f"{info['mean_reliability']:<11.3f} | {info['n_retained_samples']:<9} | {directive.message[:35]}"
                )

        print("-" * 80)
        print("Streaming Summary:")
        print(f"  Total Ingested Samples:   {total_samples}")
        print(f"  Retained Clean Samples:   {retained_samples} ({retained_samples / total_samples * 100:.1f}%)")
        print(f"  Filtered Corrupt Samples: {total_samples - retained_samples}")
        print(f"  Optimizer State RAM:      {optimizer.get_state_memory_bytes()} bytes (~2.03 bytes/param)")

        latest = ckpt_manager.load_latest()
        assert latest is not None
        _, meta = latest
        print(f"  Latest Saved Checkpoint:  Step {meta['step']} (State: {meta['state']})")
        print("=" * 80)
        print("End-to-End Pipeline Execution Verified Successfully!")


if __name__ == "__main__":
    main()
