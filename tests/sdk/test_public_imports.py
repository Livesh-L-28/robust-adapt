"""Test suite verifying public SDK imports and top-level export integrity."""

import importlib
import pytest
import robust_adapt as aml


def test_package_metadata():
    """Verify package version and namespace metadata."""
    assert hasattr(aml, "__version__")
    assert aml.__version__ == "0.1.0.dev0"
    assert hasattr(aml, "__all__")
    assert len(aml.__all__) >= 60


def test_top_level_exports_exist():
    """Verify that every symbol listed in __all__ is an attribute on robust_adapt."""
    missing = []
    for symbol_name in aml.__all__:
        if not hasattr(aml, symbol_name):
            missing.append(symbol_name)
    assert not missing, f"Symbols missing from top-level namespace: {missing}"


def test_core_classes_accessible():
    """Verify primary classes from all pillars can be accessed at root level."""
    # ALA
    assert aml.AdaptiveClassifier is not None
    assert aml.HoeffdingTree is not None
    assert aml.ADWIN is not None
    assert aml.ConceptMemory is not None
    assert aml.DelayedLabelQueue is not None

    # RLA
    assert aml.MultiSignalReliabilityEngine is not None
    assert aml.NoiseTaxonomyClassifier is not None
    assert aml.SymmetricCrossEntropyLoss is not None
    assert aml.ClassBalancedWeights is not None

    # RAO
    assert aml.LowMemoryAdamW is not None
    assert aml.BlockQuantizer is not None
    assert aml.DynamicResourceBudgetManager is not None

    # ULC
    assert aml.UnifiedLearningControllerV4_1 is not None
    assert aml.ULCv41Config is not None
    assert aml.DirectiveV4 is not None
    assert aml.AutomatonStateV4 is not None

    # Minority
    assert aml.OnlineClassPriorTracker is not None
    assert aml.AdaptiveThresholdManager is not None

    # Exceptions
    assert aml.RobustAdaptError is not None
    assert issubclass(aml.ConfigurationError, aml.RobustAdaptError)
    assert issubclass(aml.ValidationError, aml.RobustAdaptError)
    assert issubclass(aml.ResourceBudgetExceededError, aml.RobustAdaptError)
    assert issubclass(aml.ConfigurationError, aml.AdaptiveMLError)
    assert issubclass(aml.ValidationError, aml.AdaptiveMLError)
    assert issubclass(aml.ResourceBudgetExceededError, aml.AdaptiveMLError)


def test_submodule_independence():
    """Verify submodules can be imported independently without importing everything."""
    ala = importlib.import_module("robust_adapt.ala")
    assert hasattr(ala, "AdaptiveClassifier")

    rla = importlib.import_module("robust_adapt.rla")
    assert hasattr(rla, "MultiSignalReliabilityEngine")

    rao = importlib.import_module("robust_adapt.rao")
    assert hasattr(rao, "LowMemoryAdamW")

    ulc = importlib.import_module("robust_adapt.ulc")
    assert hasattr(ulc, "UnifiedLearningControllerV4_1")

    minority = importlib.import_module("robust_adapt.minority")
    assert hasattr(minority, "OnlineClassPriorTracker")
