# API Reference: Robust Learning Algorithms (`adaptive_ml.rla`)

The `adaptive_ml.rla` module provides multi-signal reliability estimation, noise taxonomy diagnostics, and noise-robust loss functions.

---

## 1. Class: `MultiSignalReliabilityEngine`

```python
class MultiSignalReliabilityEngine(
    n_classes: int = 2,
    k_neighbors: int = 5,
    buffer_size: int = 500,
    weight_margin: float = 0.40,
    weight_neighbor: float = 0.40,
    weight_temporal: float = 0.20,
)
```

Computes composite sample reliability scores $r_i \in [0, 1]$ combining prediction margin/entropy, spatial k-NN neighborhood agreement, and temporal moving consistency.

### Methods
- **`compute_reliability(X: np.ndarray, y: np.ndarray, probas: np.ndarray) -> np.ndarray`**: Computes continuous reliability scores $r_i \in [0, 1]$ for all instances in batch.

---

## 2. Class: `NoiseTaxonomyClassifier`

```python
class NoiseTaxonomyClassifier(
    n_classes: int = 2,
    noise_threshold: float = 0.15,
    asymmetry_threshold: float = 0.20,
)
```

Diagnoses noise taxonomy (`CLEAN`, `UNIFORM_RANDOM`, `CLASS_CONDITIONAL`, `INSTANCE_DEPENDENT`) and discriminates between corrupt outliers and rare valid minority patterns.

### Methods
- **`estimate_noise_transition(y_reported, y_pred) -> Tuple[NoiseType, np.ndarray, float]`**: Computes empirical transition matrix $T[j, k] = P(\text{pred}=k \mid \text{reported}=j)$ and categorizes noise taxonomy.
- **`discriminate_sample(x_candidate, y_candidate, prototypes, variances=None, margin_score=0.5) -> PatternType`**: Categorizes candidate instance as `INLIER`, `RARE_VALID_PATTERN`, or `CORRUPT_OUTLIER`.

---

## 3. Class: `ClassBalancedWeights`

```python
class ClassBalancedWeights(beta: float = 0.999)
```

Computes inverse effective-sample weights $W_c = \frac{1 - \beta}{1 - \beta^{n_c}}$ normalized so that $\bar{W} = 1.0$.

### Methods
- **`compute_weights(class_counts: np.ndarray) -> np.ndarray`**: Computes normalized weight vector of shape `(n_classes,)`.

---

## 4. Class: `SymmetricCrossEntropyLoss`

```python
class SymmetricCrossEntropyLoss(
    alpha: float = 1.0,
    beta: float = 0.5,
    eps_clip: float = 1e-4,
)
```

Differentiable loss formulation combining standard Cross Entropy (CE) with bounded Reverse Cross Entropy (RCE):
$$\mathcal{L}_{\text{SCE}} = \alpha \, \mathcal{L}_{\text{CE}} + \beta \, \mathcal{L}_{\text{RCE}}$$

### Methods
- **`forward(logits, y, sample_weights=None) -> Tuple[float, np.ndarray]`**: Computes scalar loss and analytical logit gradients $\frac{\partial \mathcal{L}}{\partial z}$.

---

## 5. Class: `RLA30RobustLearner`

```python
class RLA30RobustLearner(
    n_features: int,
    n_classes: int = 2,
    lr: float = 0.05,
    reliability_threshold: float = 0.35,
    security_mode: str = "standard",
    minority_class: int = 1,
    random_state: Optional[int] = 42,
)
```

Turnkey RLA 3.0 streaming learner integrating asymmetric transition detection, class-conditional reliability estimation, and security modes (`"standard"`, `"high_security_evasion"`, `"conservative_abstain"`).

### Methods
- **`fit_batch(X_batch, y_batch) -> Dict[str, Any]`**: Streams batch, applies abstention filtering, and executes noise-discounted SGD.
- **`partial_fit(X, y, sample_weight=None) -> RLA30RobustLearner`**: Scikit-learn compatible incremental update.
- **`predict(X) -> np.ndarray`**: Predicts target labels.
- **`predict_proba(X) -> np.ndarray`**: Predicts class posterior probabilities.
- **`score(X, y) -> float`**: Computes mean classification accuracy.

---

## 6. Class: `AsymmetricTransitionDetector`

```python
class AsymmetricTransitionDetector(
    n_classes: int = 2,
    window_size: int = 100,
)
```

Maintains rolling contingency matrix of prediction-vs-label transitions to detect directional noise attacks and evasion patterns.

---

## 7. Class: `ClassConditionalReliabilityEstimator`

```python
class ClassConditionalReliabilityEstimator(
    n_classes: int = 2,
    momentum: float = 0.95,
)
```

Tracks running class-conditional margin means and variances to evaluate sample reliability without spatial cluster collapse.
