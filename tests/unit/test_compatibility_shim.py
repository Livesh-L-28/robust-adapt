"""Comprehensive regression test suite for ROBUST-ADAPT compatibility forwarding.

Verifies:
1. robust_adapt is the single canonical source of truth.
2. adaptive_ml acts as a pure forwarding proxy.
3. 100% object identity parity (class is class, exception is exception).
4. Cross-namespace exception handling and instance polymorphism.
5. Deprecation warning emission on legacy import.
6. Zero duplicate class definitions and zero circular imports.
"""

from __future__ import annotations

import importlib
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


def test_adaptive_ml_compatibility_shim_warning():
    """Verify adaptive_ml emits a FutureWarning explaining the rebranding."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        if "adaptive_ml" in sys.modules:
            import adaptive_ml
            importlib.reload(adaptive_ml)
        else:
            import adaptive_ml

        rebrand_warnings = [
            w for w in recorded if "rebranded to 'robust_adapt'" in str(w.message)
        ]
        assert len(rebrand_warnings) >= 1
        assert issubclass(rebrand_warnings[0].category, FutureWarning)
        assert "robust_adapt" in str(rebrand_warnings[0].message)


def test_class_identity_exact():
    """Verify exact object identity between robust_adapt and adaptive_ml classes."""
    import robust_adapt as ra
    import adaptive_ml as aml

    # Core ALA
    assert ra.AdaptiveClassifier is aml.AdaptiveClassifier
    assert ra.HoeffdingTree is aml.HoeffdingTree
    assert ra.ReliabilityWeightedADWIN is aml.ReliabilityWeightedADWIN
    assert ra.RecurringConceptMemory is aml.RecurringConceptMemory
    assert ra.ClassBalancedReservoirReplay is aml.ClassBalancedReservoirReplay

    # RLA
    assert ra.MultiSignalReliabilityEngine is aml.MultiSignalReliabilityEngine
    assert ra.DensityAwareMarginScorer is aml.DensityAwareMarginScorer
    assert ra.SymmetricCrossEntropyLoss is aml.SymmetricCrossEntropyLoss
    assert ra.GeneralizedCrossEntropyLoss is aml.GeneralizedCrossEntropyLoss

    # RAO
    assert ra.LowMemoryAdamW is aml.LowMemoryAdamW
    assert ra.VectorizedLowMemoryAdamW is aml.VectorizedLowMemoryAdamW
    assert ra.BlockQuantizer is aml.BlockQuantizer
    assert ra.DynamicResourceBudgetManager is aml.DynamicResourceBudgetManager

    # ULC
    assert ra.UnifiedLearningControllerV5 is aml.UnifiedLearningControllerV5
    assert ra.UnifiedLearningControllerV4_1 is aml.UnifiedLearningControllerV4_1
    assert ra.ArbitrationAutomatonV4 is aml.ArbitrationAutomatonV4

    # Minority Intelligence
    assert ra.OnlineClassPriorTracker is aml.OnlineClassPriorTracker
    assert ra.AdaptiveThresholdManager is aml.AdaptiveThresholdManager


def test_submodule_class_identity_exact():
    """Verify submodule-level imports also have 100% object identity parity."""
    from robust_adapt.ala.classifier import AdaptiveClassifier as C_canonical
    from adaptive_ml.ala.classifier import AdaptiveClassifier as C_legacy
    assert C_canonical is C_legacy

    from robust_adapt.rla.scorer import DensityAwareMarginScorer as S_canonical
    from adaptive_ml.rla.scorer import DensityAwareMarginScorer as S_legacy
    assert S_canonical is S_legacy

    from robust_adapt.rao.adamw import LowMemoryAdamW as O_canonical
    from adaptive_ml.rao.adamw import LowMemoryAdamW as O_legacy
    assert O_canonical is O_legacy

    from robust_adapt.ulc.v5_controller import UnifiedLearningControllerV5 as U_canonical
    from adaptive_ml.ulc.v5_controller import UnifiedLearningControllerV5 as U_legacy
    assert U_canonical is U_legacy


def test_exception_identity_and_catching():
    """Verify exact exception identity and cross-namespace catchability."""
    import robust_adapt.core.exceptions as r_exc
    import adaptive_ml.core.exceptions as a_exc

    # 1. Base exception identity
    assert r_exc.RobustAdaptError is r_exc.AdaptiveMLError
    assert a_exc.AdaptiveMLError is r_exc.RobustAdaptError
    assert a_exc.RobustAdaptError is r_exc.RobustAdaptError

    # 2. Derived exception identity
    assert r_exc.ConfigurationError is a_exc.ConfigurationError
    assert r_exc.ValidationError is a_exc.ValidationError
    assert r_exc.DriftStateError is a_exc.DriftStateError
    assert r_exc.ResourceBudgetExceededError is a_exc.ResourceBudgetExceededError
    assert r_exc.SerializationError is a_exc.SerializationError

    # 3. Polymorphic catchability: legacy handler catches canonical exception
    caught = False
    try:
        raise r_exc.ConfigurationError("Test configuration error")
    except a_exc.AdaptiveMLError as e:
        caught = True
        assert "Test configuration error" in str(e)
    assert caught is True


def test_mixed_namespace_interoperability():
    """Verify instances created via legacy namespace are valid canonical instances."""
    import adaptive_ml as aml
    import robust_adapt as ra
    import numpy as np

    # Instantiate via legacy namespace
    clf = aml.AdaptiveClassifier(n_features=4, n_classes=2)

    # Validate instance against canonical class
    assert isinstance(clf, ra.AdaptiveClassifier)
    assert isinstance(clf, aml.AdaptiveClassifier)

    # Execute prequential methods
    X = np.random.randn(5, 4)
    y = np.array([0, 1, 0, 1, 0])
    clf.partial_fit(X, y)
    probs = clf.predict_proba(X)
    assert probs.shape == (5, 2)


def test_full_public_api_parity():
    """Verify that every single symbol in robust_adapt.__all__ is identically exposed in adaptive_ml."""
    import robust_adapt as ra
    import adaptive_ml as aml

    assert len(ra.__all__) >= 89
    for symbol_name in ra.__all__:
        assert hasattr(aml, symbol_name), f"Symbol {symbol_name} missing from adaptive_ml"
        ra_obj = getattr(ra, symbol_name)
        aml_obj = getattr(aml, symbol_name)
        assert ra_obj is aml_obj, f"Object {symbol_name} divergence: {ra_obj} is not {aml_obj}"


def test_optional_integrations_identity():
    """Verify integration adapters share identical object identity across namespaces."""
    from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier as S_ra
    from adaptive_ml.integrations.sklearn import SklearnAdaptiveClassifier as S_aml
    assert S_ra is S_aml

    from robust_adapt.integrations.torch_optim import VectorizedLowMemoryAdamW as T_ra
    from adaptive_ml.integrations.torch_optim import VectorizedLowMemoryAdamW as T_aml
    assert T_ra is T_aml

    from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw as F_ra
    from adaptive_ml.integrations.torch_optim import create_torch_low_memory_adamw as F_aml
    assert F_ra is F_aml


def test_no_circular_imports_in_compatibility_tree():
    """Verify all 70 compatibility modules can be imported with zero circular dependencies."""
    import os

    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "adaptive_ml")
    imported_count = 0

    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, f), base_dir)
                parts = os.path.splitext(rel_path)[0].split(os.sep)
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                mod_name = "adaptive_ml" if not parts else "adaptive_ml." + ".".join(parts)
                mod = importlib.import_module(mod_name)
                assert mod is not None
                imported_count += 1

    assert imported_count == 70
