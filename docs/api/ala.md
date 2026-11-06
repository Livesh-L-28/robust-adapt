# Adaptive Learning API Reference (`adaptive_ml.ala`)

The `adaptive_ml.ala` subpackage provides streaming classification models, drift detectors, and concept memory components.

---

## 1. Classifiers & Learners

### `ALA30AdaptiveLearner`
Turnkey adaptive learning pipeline integrating Hoeffding tree induction, ADWIN drift detection, and recurring concept restoration:

```python
from robust_adapt.ala import ALA30AdaptiveLearner

learner = ALA30AdaptiveLearner(
    n_features: int,
    n_classes: int = 2,
    grace_period: int = 20,
    delta: float = 0.002,
    similarity_threshold: float = 0.75,
    max_concepts: int = 10,
    replay_capacity: int = 2000,
    cooldown_steps: int = 5,
)
```
- `partial_fit(X: np.ndarray, y: np.ndarray, sample_weight=None) -> ALA30AdaptiveLearner`: Ingests stream micro-batch.
- `predict(X: np.ndarray) -> np.ndarray`: Returns discrete class labels.
- `predict_proba(X: np.ndarray) -> np.ndarray`: Returns normalized class probabilities.
- `score(X: np.ndarray, y: np.ndarray) -> float`: Returns prequential classification accuracy.
- `state_dict() -> Dict[str, Any]` & `load_state_dict(state: Dict[str, Any])`: State serialization.

### `AdaptiveClassifier`
High-performance streaming decision tree estimator based on Hoeffding Bounds:
```python
from robust_adapt.ala import AdaptiveClassifier

clf = AdaptiveClassifier(
    n_features: int,
    n_classes: int = 2,
    grace_period: int = 20,
    delta: float = 0.001,
    tie_threshold: float = 0.05,
    random_state: Optional[int] = None,
)
```
Implements the standard Scikit-Learn estimator protocol: `fit`, `partial_fit`, `predict`, `predict_proba`, `score`, `get_params`, `set_params`.

---

## 2. Drift Detectors

### `ReliabilityWeightedADWIN`
Adaptive Windowing drift detector with optional sample reliability weighting:
```python
from robust_adapt.ala import ReliabilityWeightedADWIN

adwin = ReliabilityWeightedADWIN(
    delta: float = 0.002,
    min_subwindow_weight: float = 5.0,
    eps_r: float = 1e-4,
    max_buckets_per_level: int = 5,
)
```
- `update(loss: float, reliability: float = 1.0) -> bool`: Feeds a new observation. Returns `True` if statistically significant drift is detected.
- `reset()`: Reinitializes the internal bucket histogram.

---

## 3. Experience Replay & Concept Memory

### `RecurringConceptMemory`
Bounded snapshot repository for recognizing and restoring recurring concepts:
```python
from robust_adapt.ala import RecurringConceptMemory

memory = RecurringConceptMemory(
    max_concepts: int = 10,
    similarity_threshold: float = 0.75,
)
```
- `store_concept(fingerprint: np.ndarray, model_state: Any, step: int = 0) -> ConceptSnapshot`: Stores a snapshot.
- `find_matching_concept(fingerprint: np.ndarray) -> Tuple[Optional[ConceptSnapshot], float]`: Queries for recurring concept match.
- `n_stored`: Number of concept snapshots currently held in memory.

### `ClassBalancedReservoirReplay`
Bounded stratified reservoir replay buffer:
```python
from robust_adapt.ala import ClassBalancedReservoirReplay

replay = ClassBalancedReservoirReplay(
    capacity: int = 5000,
    n_classes: int = 2,
    random_state: Optional[int] = None,
)
```
- `add(X: np.ndarray, y: np.ndarray, weights=None)`: Inserts samples using class-balanced reservoir sampling.
- `sample(n: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]`: Draws a class-stratified random replay batch.
- `total_stored`: Total samples currently retained in buffer ($\le \text{capacity}$).
