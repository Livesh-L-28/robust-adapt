# API Reference: Minority Intelligence (`adaptive_ml.minority`)

The `adaptive_ml.minority` module provides tools for maintaining predictive accuracy and recall on rare classes in streaming environments.

---

## 1. Class: `OnlineClassPriorTracker`

```python
class OnlineClassPriorTracker(
    n_classes: int = 2,
    alpha: float = 0.05,
    window_size: int = 500,
    smoothing: float = 1.0,
    imbalance_threshold: float = 0.20,
)
```

Maintains real-time class prior estimates using exponential moving averages and sliding window history with Laplace smoothing.

### Properties
- **`priors`** (`np.ndarray`): Current estimated prior probability vector of shape `(n_classes,)`.
- **`imbalance_ratio`** (`float`): Ratio of maximum to minimum class prior.
- **`minority_classes`** (`List[int]`): List of class indices classified as minority.

### Methods
- **`update(labels: np.ndarray) -> None`**: Updates prior estimates with newly observed target labels.

---

## 2. Class: `AdaptiveThresholdManager`

```python
class AdaptiveThresholdManager(
    n_classes: int = 2,
    mode: str = "dynamic",
    base_threshold: float = 0.5,
    gamma: float = 0.5,
    tau_min: float = 0.05,
    tau_max: float = 0.95,
    cost_matrix: Optional[np.ndarray] = None,
)
```

Dynamically optimizes decision thresholds $\tau_c(t)$ according to moving priors or misclassification cost matrices.

### Methods
- **`update_from_priors(priors: np.ndarray) -> np.ndarray`**: Updates operational decision thresholds based on current priors.
- **`predict(probas: np.ndarray) -> np.ndarray`**: Converts class posterior probabilities to integer predictions using active thresholds.

---

## 3. Class: `MinorityIntelligence20Learner`

```python
class MinorityIntelligence20Learner(
    target_fp_budget_per_1k: float = 1.5,
    sublinear_cost_power: float = 0.52,
    base_threshold: float = 0.5,
    min_threshold: float = 0.15,
    max_threshold: float = 0.85,
    lr: float = 0.01,
    minority_class: int = 1,
    random_state: Optional[int] = 42,
)
```

Turnkey Minority Intelligence 2.0 streaming learner integrating Beta-Binomial prior estimation, sublinear cost weighting, and PID false-positive budget thresholding.

### Methods
- **`fit_batch(X_batch, y_batch) -> Dict[str, Any]`**: Ingests batch, updates Bayesian prior, dynamically modulates threshold, and performs cost-weighted SGD update.
- **`partial_fit(X, y, sample_weight=None) -> MinorityIntelligence20Learner`**: Scikit-learn compatible incremental update.
- **`predict(X) -> np.ndarray`**: Predicts target labels using active PID threshold.
- **`predict_proba(X) -> np.ndarray`**: Computes posterior class probabilities.
- **`score(X, y) -> float`**: Computes mean classification accuracy.

---

## 4. Class: `BetaBinomialPriorTracker`

```python
class BetaBinomialPriorTracker(
    alpha_prior: float = 1.0,
    beta_prior: float = 100.0,
    decay: float = 0.995,
    minority_class: int = 1,
)
```

Maintains rolling Beta-Binomial Bayesian conjugate prior over non-stationary imbalanced streams.

---

## 5. Class: `DynamicFPBudgetThresholdManager`

```python
class DynamicFPBudgetThresholdManager(
    target_fp_budget_per_1k: float = 1.5,
    base_threshold: float = 0.5,
    min_threshold: float = 0.15,
    max_threshold: float = 0.85,
    kp: float = 0.08,
    ki: float = 0.01,
    kd: float = 0.02,
)
```

PID-regulated false-positive budget manager strictly constraining operational false alarms per thousand samples.

---

## 6. Function: `compute_sublinear_cost_weights`

```python
def compute_sublinear_cost_weights(
    imbalance_ratio: float,
    power: float = 0.52,
) -> Tuple[float, float]:
```

Computes sublinear cost weights $w_{\text{min}} = \text{ratio}^{\text{power}}$ to prevent gradient explosion under severe class imbalance.
