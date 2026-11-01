# AdaptiveML — Public API Specification & Typed Protocols

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-004`  
> **Last Updated**: 2026-11-01  
> **Scope**: Concrete class signatures, type annotations, docstrings, and protocol definitions  
> **Target Downstream Phase**: Phase 8 (Core Algorithm Implementation)

---

## 1. Type Aliases & Standard Protocols

All signatures in AdaptiveML use explicit type definitions defined in `adaptive_ml.core.types`:

```python
from typing import TypeVar, Union, Optional, Tuple, Dict, Any, Sequence, Protocol
import numpy as np
import numpy.typing as npt

# Floating point and integer array aliases
FloatArray2D = npt.NDArray[np.floating[Any]]
FloatArray1D = npt.NDArray[np.floating[Any]]
IntArray1D = npt.NDArray[np.integer[Any]]
IntArray2D = npt.NDArray[np.integer[Any]]
ArrayLike = Union[FloatArray2D, FloatArray1D, Sequence[float], Sequence[int]]
```

---

## 2. ALA Public API: `AdaptiveClassifier`

```python
class AdaptiveClassifier:
    """Online streaming classifier combining vectorized Hoeffding trees with drift adaptation.
    
    Conforms fully to the scikit-learn BaseEstimator and ClassifierMixin protocols,
    supporting standard partial_fit pipelines and streaming workflows.
    
    Parameters
    ----------
    n_features : int
        The dimensionality of input feature space.
    n_classes : int
        The number of target classes.
    grace_period : int, default=200
        Number of instances a leaf must accumulate before evaluating split criteria.
    delta : float, default=1e-5
        Hoeffding split confidence parameter (1 - delta split confidence).
    tau_tie : float, default=0.05
        Tie-breaking threshold for Hoeffding bound evaluation.
    enable_drift_detection : bool, default=True
        Whether to monitor incoming loss streams with Reliability-Weighted ADWIN.
    replay_capacity : int, default=5000
        Maximum capacity of the class-balanced reservoir replay buffer.
    replay_ratio : float, default=0.2
        Fraction of incoming batch size sampled from replay buffer during updates.
    random_state : Optional[int], default=None
        Seed for reproducible random state initialization.
    """
    
    def __init__(
        self,
        n_features: int,
        n_classes: int,
        grace_period: int = 200,
        delta: float = 1e-5,
        tau_tie: float = 0.05,
        enable_drift_detection: bool = True,
        replay_capacity: int = 5000,
        replay_ratio: float = 0.2,
        random_state: Optional[int] = None,
    ) -> None: ...

    def fit(self, X: FloatArray2D, y: IntArray1D, classes: Optional[Sequence[int]] = None) -> "AdaptiveClassifier":
        """Fit the model on batch data by calling partial_fit repeatedly.
        
        Parameters
        ----------
        X : FloatArray2D of shape (n_samples, n_features)
            Training feature matrix.
        y : IntArray1D of shape (n_samples,)
            Target class labels.
        classes : Optional[Sequence[int]], default=None
            List of all target classes.
            
        Returns
        -------
        self : AdaptiveClassifier
            The fitted estimator.
        """
        ...

    def partial_fit(
        self,
        X: FloatArray2D,
        y: IntArray1D,
        sample_weight: Optional[FloatArray1D] = None,
    ) -> "AdaptiveClassifier":
        """Incrementally update the tree ensemble with a streaming mini-batch.
        
        Parameters
        ----------
        X : FloatArray2D of shape (n_samples, n_features)
            Streaming feature batch.
        y : IntArray1D of shape (n_samples,)
            Streaming class labels.
        sample_weight : Optional[FloatArray1D], default=None
            Per-sample reliability weights in [0.0, 1.0].
            
        Returns
        -------
        self : AdaptiveClassifier
            The updated estimator.
        """
        ...

    def predict(self, X: FloatArray2D) -> IntArray1D:
        """Predict class labels for input instances.
        
        Parameters
        ----------
        X : FloatArray2D of shape (n_samples, n_features)
            Input features.
            
        Returns
        -------
        y_pred : IntArray1D of shape (n_samples,)
            Predicted class indices.
        """
        ...

    def predict_proba(self, X: FloatArray2D) -> FloatArray2D:
        """Predict class posterior probabilities for input instances.
        
        Parameters
        ----------
        X : FloatArray2D of shape (n_samples, n_features)
            Input features.
            
        Returns
        -------
        probabilities : FloatArray2D of shape (n_samples, n_classes)
            Normalized probability distribution over classes.
        """
        ...
```

---

## 3. RLA Public API: `DensityAwareMarginScorer` & `SymmetricCrossEntropyLoss`

### 3.1 `DensityAwareMarginScorer`

```python
class DensityAwareMarginScorer:
    """Computes sample reliability by coupling signed logit margins with local k-NN feature density.
    
    Protects difficult minority-class instances from false-positive noise filtering.
    
    Parameters
    ----------
    n_classes : int
        Total number of target classes.
    n_neighbors : int, default=5
        Number of nearest neighbors evaluated for local density estimation.
    alpha : float, default=1.0
        Logit margin scaling sensitivity.
    gamma : float, default=0.5
        Density protection bonus coefficient for rare instances.
    min_reliability : float, default=1e-4
        Lower-bound epsilon guard on reliability scores.
    """
    
    def __init__(
        self,
        n_classes: int,
        n_neighbors: int = 5,
        alpha: float = 1.0,
        gamma: float = 0.5,
        min_reliability: float = 1e-4,
    ) -> None: ...

    def score_samples(
        self,
        X: FloatArray2D,
        logits: FloatArray2D,
        y: IntArray1D,
    ) -> FloatArray1D:
        """Compute density-aware reliability scores for a batch of instances.
        
        Parameters
        ----------
        X : FloatArray2D of shape (n_samples, n_features)
            Feature embeddings.
        logits : FloatArray2D of shape (n_samples, n_classes)
            Model logit outputs.
        y : IntArray1D of shape (n_samples,)
            Observed target labels.
            
        Returns
        -------
        reliabilities : FloatArray1D of shape (n_samples,)
            Per-sample reliability scores in [min_reliability, 1.0].
        """
        ...
```

### 3.2 `SymmetricCrossEntropyLoss`

```python
class SymmetricCrossEntropyLoss:
    """Symmetric Cross Entropy (SCE) loss combining CE and Reverse Cross Entropy (RCE).
    
    Parameters
    ----------
    alpha : float, default=1.0
        Weight factor for standard Cross Entropy term.
    beta : float, default=0.5
        Weight factor for bounded Reverse Cross Entropy term.
    eps_clip : float, default=1e-4
        Numerical clipping constant for RCE logarithm bounding.
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 0.5, eps_clip: float = 1e-4) -> None: ...

    def forward(
        self,
        logits: FloatArray2D,
        y: IntArray1D,
        sample_weights: Optional[FloatArray1D] = None,
    ) -> Tuple[float, FloatArray2D]:
        """Compute forward loss value and analytical logit gradients simultaneously.
        
        Parameters
        ----------
        logits : FloatArray2D of shape (n_samples, n_classes)
            Unnormalized model logits.
        y : IntArray1D of shape (n_samples,)
            Ground truth or observed labels.
        sample_weights : Optional[FloatArray1D], default=None
            Per-sample importance/reliability weights.
            
        Returns
        -------
        loss : float
            Scalar batch loss value.
        grad_logits : FloatArray2D of shape (n_samples, n_classes)
            Analytical gradients dL/dz for backpropagation.
        """
        ...
```

---

## 4. RAO Public API: `LowMemoryAdamW`

```python
class LowMemoryAdamW:
    """CPU-optimized block-quantized AdamW optimizer achieving 74.6% state memory reduction.
    
    Quantizes momentum states into signed int8 and variance states into unsigned uint8
    over non-overlapping blocks of size 256. Operates without C++ or CUDA compilation.
    
    Parameters
    ----------
    params : Sequence[Any]
        Iterable of model parameters (PyTorch Tensors or NumPy arrays).
    lr : float, default=1e-3
        Learning rate.
    betas : Tuple[float, float], default=(0.9, 0.999)
        Coefficients for computing running averages of gradient and its square.
    eps : float, default=1e-8
        Term added to the denominator to improve numerical stability.
    weight_decay : float, default=1e-2
        Decoupled weight decay coefficient.
    block_size : int, default=256
        Block size for dynamic dynamic scaling and quantization.
    """
    
    def __init__(
        self,
        params: Sequence[Any],
        lr: float = 1e-3,
        betas: Tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 1e-2,
        block_size: int = 256,
    ) -> None: ...

    def step(self, closure: Optional[Any] = None) -> Optional[float]:
        """Performs a single optimization step using block-quantized updates."""
        ...

    def zero_grad(self, set_to_none: bool = True) -> None:
        """Resets the gradients of all optimized parameters."""
        ...

    def state_dict(self) -> Dict[str, Any]:
        """Returns the optimizer state dictionary containing quantized buffers and scales."""
        ...

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Loads the optimizer state from a state dictionary."""
        ...
```

---

## 5. ULC Public API: `AdaptiveLearningController`

```python
class AdaptiveLearningController:
    """Optional cross-pillar coordinator executing dual-evidence drift-noise arbitration.
    
    Parameters
    ----------
    classifier : AdaptiveClassifier
        Underlying ALA streaming classifier.
    scorer : DensityAwareMarginScorer
        Underlying RLA reliability scorer.
    tau_R : float, default=0.65
        Reliability arbitration threshold separating drift from noise bursts.
    recovery_steps : int, default=100
        Number of steps to maintain post-drift adaptation recovery state.
    """
    
    def __init__(
        self,
        classifier: AdaptiveClassifier,
        scorer: DensityAwareMarginScorer,
        tau_R: float = 0.65,
        recovery_steps: int = 100,
    ) -> None: ...

    def step(
        self,
        X: FloatArray2D,
        y: IntArray1D,
    ) -> Dict[str, Any]:
        """Execute a coordinated learning step with drift-noise arbitration.
        
        Returns
        -------
        step_metrics : Dict[str, Any]
            Dictionary containing current automaton state, drift signal, mean reliability,
            and action directives applied.
        """
        ...
```
