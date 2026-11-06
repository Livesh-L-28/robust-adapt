"""AdaptiveML Framework Integrations.

Provides optional integration adapters for scikit-learn, PyTorch, and DataFrames (pandas/Polars)
without imposing mandatory dependencies on the core library.
"""

from __future__ import annotations

from robust_adapt.integrations.data import (
    DatasetContract,
    inspect_dataset_contract,
    to_numpy,
    to_tensor,
)
from robust_adapt.integrations.sklearn import (
    SklearnAdaptiveClassifier,
    SklearnDriftDetectorTransformer,
    SklearnReliabilityFilter,
)
from robust_adapt.integrations.torch_callback import (
    TorchCheckpointAdapter,
    TorchTrainingBudgetHook,
)
from robust_adapt.integrations.torch_module import (
    TorchGeneralizedCrossEntropyLoss,
    TorchSymmetricCrossEntropyLoss,
)
from robust_adapt.integrations.torch_optim import (
    VectorizedLowMemoryAdamW,
    create_torch_low_memory_adamw,
)

__all__ = [
    # Data Interoperability
    "to_numpy",
    "to_tensor",
    "inspect_dataset_contract",
    "DatasetContract",
    # scikit-learn
    "SklearnAdaptiveClassifier",
    "SklearnDriftDetectorTransformer",
    "SklearnReliabilityFilter",
    # PyTorch
    "TorchSymmetricCrossEntropyLoss",
    "TorchGeneralizedCrossEntropyLoss",
    "VectorizedLowMemoryAdamW",
    "create_torch_low_memory_adamw",
    "TorchTrainingBudgetHook",
    "TorchCheckpointAdapter",
]
