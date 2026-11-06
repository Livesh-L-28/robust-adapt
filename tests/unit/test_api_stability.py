"""
Unit tests verifying public API stability and import signatures for ROBUST-ADAPT.
"""

from __future__ import annotations

import inspect
import pytest

import robust_adapt
from robust_adapt.core.exceptions import (
    AdaptiveMLError,
    ConfigurationError,
    DriftStateError,
    NumericalInstabilityError,
    QuantizationError,
    ResourceBudgetExceededError,
    SerializationError,
    ValidationError,
)
from robust_adapt.ala import (
    AdaptiveClassifier,
    ConceptMemory,
    DelayedLabelQueue,
    ReliabilityWeightedADWIN,
    VectorizedHoeffdingTree,
)
from robust_adapt.rla import (
    GeneralizedCrossEntropyLoss,
    MultiSignalReliabilityEngine,
    SymmetricCrossEntropyLoss,
)
from robust_adapt.rao import (
    DynamicResourceBudgetManager,
    LowMemoryAdamW,
)
from robust_adapt.ulc import (
    AdaptiveLearningController,
    ControllerDirective,
    ControllerState,
    UnifiedLearningControllerV4_1,
    ULCv41Config,
)
from robust_adapt.minority import (
    OnlineClassPriorTracker,
    AdaptiveThresholdManager,
)


class TestAPIStability:
    """Automated verification of public API contracts and signatures."""

    def test_version_string(self) -> None:
        """Verify package version string."""
        assert hasattr(robust_adapt, "__version__")
        assert robust_adapt.__version__ == "0.1.0.dev0"

    def test_core_exceptions_hierarchy(self) -> None:
        """Verify all custom exceptions inherit from AdaptiveMLError."""
        exceptions = [
            ConfigurationError,
            DriftStateError,
            NumericalInstabilityError,
            QuantizationError,
            ResourceBudgetExceededError,
            SerializationError,
            ValidationError,
        ]
        for exc_cls in exceptions:
            assert issubclass(exc_cls, AdaptiveMLError)
            assert issubclass(exc_cls, Exception)

    def test_root_namespace_exports(self) -> None:
        """Verify presence of all documented root exports."""
        expected_exports = [
            # Exceptions
            "AdaptiveMLError",
            "ValidationError",
            "ConfigurationError",
            "SerializationError",
            "ResourceBudgetExceededError",
            # ALA
            "AdaptiveClassifier",
            "VectorizedHoeffdingTree",
            "HoeffdingTree",
            "ReliabilityWeightedADWIN",
            "ADWIN",
            "ConceptMemory",
            "DelayedLabelQueue",
            # RLA
            "MultiSignalReliabilityEngine",
            "SymmetricCrossEntropyLoss",
            "GeneralizedCrossEntropyLoss",
            # RAO
            "LowMemoryAdamW",
            "DynamicResourceBudgetManager",
            "BudgetState",
            # ULC
            "AdaptiveLearningController",
            "UnifiedLearningControllerV4_1",
            "ULCv41Config",
            "ControllerDirective",
            "ControllerState",
            # Minority
            "OnlineClassPriorTracker",
            "AdaptiveThresholdManager",
        ]
        for sym in expected_exports:
            assert hasattr(robust_adapt, sym), f"Missing public symbol in root namespace: {sym}"

    def test_adaptive_classifier_signature(self) -> None:
        """Verify AdaptiveClassifier constructor signature and defaults."""
        sig = inspect.signature(AdaptiveClassifier.__init__)
        params = sig.parameters
        assert "n_features" in params
        assert "n_classes" in params
        assert "grace_period" in params
        assert params["grace_period"].default == 200
        assert "delta" in params
        assert params["delta"].default == 1e-5

    def test_adwin_signature(self) -> None:
        """Verify ReliabilityWeightedADWIN constructor signature and defaults."""
        sig = inspect.signature(ReliabilityWeightedADWIN.__init__)
        params = sig.parameters
        assert "delta" in params
        assert params["delta"].default == 0.002
        assert "min_subwindow_weight" in params
        assert params["min_subwindow_weight"].default == 5.0

    def test_dynamic_resource_budget_manager_signature(self) -> None:
        """Verify DynamicResourceBudgetManager constructor signature."""
        sig = inspect.signature(DynamicResourceBudgetManager.__init__)
        params = sig.parameters
        assert "max_step_time_ms" in params
        assert params["max_step_time_ms"].default == 100.0
        assert "max_memory_mb" in params
        assert params["max_memory_mb"].default == 2048.0

    def test_ulc_v4_1_controller_signature(self) -> None:
        """Verify UnifiedLearningControllerV4_1 constructor signature."""
        sig = inspect.signature(UnifiedLearningControllerV4_1.__init__)
        params = sig.parameters
        assert "config" in params
        assert "classifier" in params
        assert "optimizer" in params
        assert "adwin" in params
        assert "pipeline" in params

    def test_integrations_namespace_exports(self) -> None:
        """Verify presence of integration exports when optional dependencies are available."""
        import robust_adapt.integrations as ami
        expected_integrations = [
            "to_numpy",
            "to_tensor",
            "inspect_dataset_contract",
            "DatasetContract",
            "SklearnAdaptiveClassifier",
            "SklearnDriftDetectorTransformer",
            "SklearnReliabilityFilter",
            "TorchSymmetricCrossEntropyLoss",
            "TorchGeneralizedCrossEntropyLoss",
            "create_torch_low_memory_adamw",
            "TorchTrainingBudgetHook",
            "TorchCheckpointAdapter",
        ]
        for sym in expected_integrations:
            assert hasattr(ami, sym), f"Missing integration symbol: {sym}"
