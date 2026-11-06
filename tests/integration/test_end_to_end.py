"""
ROBUST-ADAPT End-to-End Cross-Pillar Integration Tests.

Validates the full system behavior across ALA, RLA, RAO, and ULC,
as well as strict pillar decoupling and safe state persistence.
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pytest

from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.core.config import ULCConfig
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rla.pipeline import RobustLearningPipeline
from robust_adapt.state.checkpoint import CheckpointManager
from robust_adapt.ulc.controller import AdaptiveLearningController
from robust_adapt.ulc.directives import ControllerState


def test_strict_pillar_isolation() -> None:
    """Validate that ALA, RLA, and RAO have zero cross-pillar internal imports."""
    # Check ALA imports
    import robust_adapt.ala.classifier
    import robust_adapt.ala.tree
    import robust_adapt.ala.adwin

    # Check RLA imports
    import robust_adapt.rla.scorer
    import robust_adapt.rla.losses
    import robust_adapt.rla.pipeline

    # Check RAO imports
    import robust_adapt.rao.adamw
    import robust_adapt.rao.quantizer

    # Inspect sys.modules dependencies
    ala_code = Path("robust_adapt/ala").glob("*.py")
    for p in ala_code:
        text = p.read_text(encoding="utf-8")
        assert "robust_adapt.rla" not in text, f"{p} illegally imports RLA"
        assert "robust_adapt.rao" not in text, f"{p} illegally imports RAO"
        assert "robust_adapt.ulc" not in text, f"{p} illegally imports ULC"

    rla_code = Path("robust_adapt/rla").glob("*.py")
    for p in rla_code:
        text = p.read_text(encoding="utf-8")
        assert "robust_adapt.ala" not in text, f"{p} illegally imports ALA"
        assert "robust_adapt.rao" not in text, f"{p} illegally imports RAO"
        assert "robust_adapt.ulc" not in text, f"{p} illegally imports ULC"

    rao_code = Path("robust_adapt/rao").glob("*.py")
    for p in rao_code:
        text = p.read_text(encoding="utf-8")
        assert "robust_adapt.ala" not in text, f"{p} illegally imports ALA"
        assert "robust_adapt.rla" not in text, f"{p} illegally imports RLA"
        assert "robust_adapt.ulc" not in text, f"{p} illegally imports ULC"


def test_end_to_end_cross_pillar_streaming_workflow(tmp_path: Path) -> None:
    """Validate integrated execution of ALA + RLA + RAO + ULC over streaming data."""
    rng = np.random.default_rng(123)

    # 1. Setup All Pillars
    n_features = 4
    n_classes = 2

    classifier = AdaptiveClassifier(n_features=n_features, n_classes=n_classes, grace_period=20)
    pipeline = RobustLearningPipeline(n_classes=n_classes)
    opt_params = [rng.normal(size=(8, n_features)).astype(np.float32)]
    optimizer = LowMemoryAdamW(opt_params, lr=0.01)

    controller = AdaptiveLearningController(
        classifier=classifier,
        pipeline=pipeline,
        optimizer=optimizer,
        config=ULCConfig(tau_R=0.48, recovery_steps=3),
    )

    ckpt_manager = CheckpointManager(checkpoint_dir=tmp_path / "ckpts", max_checkpoints=3)

    # 2. Stream 25 batches through different conditions
    states_observed = set()

    for step in range(1, 26):
        # Generate batch
        if step <= 10:
            # Clean regime
            X = rng.normal(loc=1.0, scale=0.5, size=(20, n_features))
            y = np.zeros(20, dtype=np.int64)
            logits = np.tile([3.0, -3.0], (20, 1))
            delta = 0.1
        elif 11 <= step <= 15:
            # Noise burst: corrupted labels in dense region
            X = rng.normal(loc=1.0, scale=0.5, size=(20, n_features))
            y = np.ones(20, dtype=np.int64)  # flipped
            logits = np.tile([3.0, -3.0], (20, 1))
            delta = 1.3
        else:
            # True drift regime
            X = rng.normal(loc=-2.0, scale=0.5, size=(20, n_features))
            y = np.ones(20, dtype=np.int64)
            logits = np.tile([-3.0, 3.0], (20, 1))
            delta = 1.2 if step == 16 else 0.1

        directive, info = controller.step(X, y, logits=logits, delta_drift=delta)
        states_observed.add(directive.state)

        # Checkpoint every 5 steps
        if step % 5 == 0:
            tensors = {"param": opt_params[0]}
            ckpt_manager.save_checkpoint(step=step, tensors=tensors, metadata={"state": directive.state.value})

    # Verify key states were encountered
    assert ControllerState.STABLE in states_observed
    assert ControllerState.CONFIRMED_DRIFT in states_observed

    # Verify checkpoint manager retained latest snapshots
    saved_steps = ckpt_manager.list_checkpoints()
    assert saved_steps == [15, 20, 25]

    # Verify restoration
    tensors, meta = ckpt_manager.load_latest()
    assert meta["step"] == 25
    assert "param" in tensors
    assert tensors["param"].shape == (8, n_features)

