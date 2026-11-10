"""Comprehensive test suite for ROBUST-ADAPT canonical package consolidation.

Verifies:
1. robust_adapt is the sole canonical package namespace.
2. adaptive_ml is completely removed and unimportable (raising ModuleNotFoundError).
3. Isolated subprocess execution confirms adaptive_ml is absent from the environment.
4. Canonical classes across all 5 research pillars instantiate and execute independently.
5. Submodule-level imports resolve without legacy dependencies.
6. Canonical exception hierarchy integrity and catchability.
7. Public API surface complete coverage (all symbols in robust_adapt.__all__).
8. Integration adapters load directly from robust_adapt.integrations.
9. Zero circular imports across the entire robust_adapt package tree.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
import warnings
import pytest


def test_robust_adapt_primary_import():
    """Verify robust_adapt can be imported cleanly without deprecation warnings."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        import robust_adapt
        assert robust_adapt.__version__ == "0.1.0.dev0"
        assert hasattr(robust_adapt, "RobustAdaptError")
        assert hasattr(robust_adapt, "AdaptiveMLError")
        assert hasattr(robust_adapt, "AdaptiveClassifier")
        assert hasattr(robust_adapt, "ADWIN")
        assert hasattr(robust_adapt, "HoeffdingTree")

    rebrand_warnings = [
        w for w in recorded if "rebranded to 'robust_adapt'" in str(w.message)
    ]
    assert len(rebrand_warnings) == 0


def test_legacy_adaptive_ml_unimportable():
    """Verify that adaptive_ml is completely absent and cannot be imported."""
    assert importlib.util.find_spec("adaptive_ml") is None
    with pytest.raises(ModuleNotFoundError):
        import adaptive_ml  # type: ignore[import-not-found]


def test_legacy_adaptive_ml_unimportable_subprocess():
    """Verify in an isolated subprocess that importing adaptive_ml raises ModuleNotFoundError."""
    cmd = [
        sys.executable,
        "-c",
        (
            "import importlib.util\n"
            "assert importlib.util.find_spec('adaptive_ml') is None\n"
            "try:\n"
            "    import adaptive_ml\n"
            "    sys.exit(1)\n"
            "except ModuleNotFoundError:\n"
            "    print('ADAPTIVE_ML_ABSENT_VERIFIED')\n"
        ),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "ADAPTIVE_ML_ABSENT_VERIFIED" in res.stdout


def test_canonical_core_classes_independent():
    """Verify robust_adapt core classes instantiate and execute independently."""
    import numpy as np
    import robust_adapt as ra

    # Core ALA
    clf = ra.AdaptiveClassifier(n_features=4, n_classes=2)
    X = np.random.randn(10, 4)
    y = np.array([0, 1] * 5)
    clf.partial_fit(X, y)
    probs = clf.predict_proba(X)
    assert probs.shape == (10, 2)

    # Core RLA
    scorer = ra.DensityAwareMarginScorer(n_classes=2)
    assert scorer is not None

    # Core RAO
    quantizer = ra.BlockQuantizer(block_size=32)
    assert quantizer is not None

    # Core ULC
    config = ra.ULCv5Config(grace_period=10, delta=0.01)
    controller = ra.UnifiedLearningControllerV5(n_features=4, n_classes=2, config=config)
    assert controller is not None

    # Core Minority
    tracker = ra.OnlineClassPriorTracker(n_classes=2)
    assert tracker is not None


def test_canonical_submodule_imports_direct():
    """Verify direct submodule-level imports resolve without legacy dependencies."""
    from robust_adapt.ala.classifier import AdaptiveClassifier
    from robust_adapt.rla.losses import ReliabilityWeightedLoss, FocalLoss
    from robust_adapt.rao.adamw import LowMemoryAdamW
    from robust_adapt.ulc.v5_controller import UnifiedLearningControllerV5
    from robust_adapt.minority.prior import OnlineClassPriorTracker

    assert AdaptiveClassifier is not None
    assert ReliabilityWeightedLoss is not None
    assert FocalLoss is not None
    assert LowMemoryAdamW is not None
    assert UnifiedLearningControllerV5 is not None
    assert OnlineClassPriorTracker is not None


def test_canonical_exception_hierarchy():
    """Verify canonical exception hierarchy and catchability."""
    import robust_adapt.core.exceptions as r_exc

    # 1. Base exception
    assert issubclass(r_exc.RobustAdaptError, Exception)
    assert r_exc.AdaptiveMLError is r_exc.RobustAdaptError

    # 2. Derived exceptions inherit from RobustAdaptError
    assert issubclass(r_exc.ConfigurationError, r_exc.RobustAdaptError)
    assert issubclass(r_exc.ValidationError, r_exc.RobustAdaptError)
    assert issubclass(r_exc.DriftStateError, r_exc.RobustAdaptError)
    assert issubclass(r_exc.ResourceBudgetExceededError, r_exc.RobustAdaptError)
    assert issubclass(r_exc.SerializationError, r_exc.RobustAdaptError)

    # 3. Polymorphic catchability
    caught = False
    try:
        raise r_exc.ConfigurationError("Invalid configuration")
    except r_exc.RobustAdaptError as e:
        caught = True
        assert "Invalid configuration" in str(e)
    assert caught is True


def test_canonical_full_public_api_surface():
    """Verify every symbol in robust_adapt.__all__ is present, valid, and clean."""
    import robust_adapt as ra

    assert len(ra.__all__) >= 89
    for symbol_name in ra.__all__:
        assert hasattr(ra, symbol_name), f"Symbol {symbol_name} missing from robust_adapt"
        obj = getattr(ra, symbol_name)
        assert obj is not None, f"Symbol {symbol_name} in robust_adapt is None"


def test_canonical_optional_integrations():
    """Verify integration adapters load directly from robust_adapt.integrations."""
    from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier
    from robust_adapt.integrations.torch_optim import (
        VectorizedLowMemoryAdamW,
        create_torch_low_memory_adamw,
    )

    assert SklearnAdaptiveClassifier is not None
    assert VectorizedLowMemoryAdamW is not None
    assert create_torch_low_memory_adamw is not None


def test_no_circular_imports_in_canonical_tree():
    """Verify all canonical modules can be imported with zero circular dependencies."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "robust_adapt")
    imported_count = 0

    for root, _, files in os.walk(base_dir):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, f), base_dir)
                parts = os.path.splitext(rel_path)[0].split(os.sep)
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                mod_name = "robust_adapt" if not parts else "robust_adapt." + ".".join(parts)
                mod = importlib.import_module(mod_name)
                assert mod is not None
                imported_count += 1

    assert imported_count >= 60
