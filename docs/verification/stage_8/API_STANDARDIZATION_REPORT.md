# API Standardization Report: Developer Experience & Consistency

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Report Date:** 2026-11-06<br>
**Auditor:** API Design Specialist & Python Library Architect<br>
**Artifact Path:** [API_STANDARDIZATION_REPORT.md](file:///c:/projects/AdaptiveML/docs/verification/stage_8/API_STANDARDIZATION_REPORT.md)<br>

---

## 1. Principles of API Standardization

In designing the standardized developer surface for AdaptiveML:
1. **Zero Breaking Changes**: Every existing public import path (`adaptive_ml.ala`, `adaptive_ml.rla`, `adaptive_ml.rao`, `adaptive_ml.ulc`, `adaptive_ml.minority`, `adaptive_ml.state`, `adaptive_ml.core`) remains $100\%$ backward-compatible.
2. **Top-Level Convenience**: Common entry points are accessible directly from `adaptive_ml` without deep nested package navigation.
3. **Lazy & Non-Intrusive**: Top-level imports execute in $< 5\text{ms}$ and do not eagerly load heavyweight optional packages like PyTorch, Scikit-learn, or Safetensors.
4. **Consistent Conventions**: Parameter names align with standard scientific Python conventions (`X`, `y`, `n_features`, `n_classes`, `random_state`, `lr`, `batch_size`).

---

## 2. Standardized Public Import Surface

### 2.1. Top-Level Convenience Exports in `adaptive_ml`

To provide an ergonomic developer experience, [`adaptive_ml/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/__init__.py) is standardized to export primary classes directly:

```python
# Standard Developer Usage
import adaptive_ml as aml

# 1. Primary Estimators & Detectors (ALA)
clf = aml.AdaptiveClassifier(n_features=10, n_classes=2)
tree = aml.VectorizedHoeffdingTree(n_features=10, n_classes=2)
adwin = aml.ReliabilityWeightedADWIN(delta=0.002)

# 2. Robust Learning (RLA)
pipeline = aml.RobustLearningPipeline(n_classes=2)
loss = aml.SymmetricCrossEntropyLoss(alpha=1.0, beta=1.0)

# 3. Resource-Aware Optimization (RAO)
optimizer = aml.LowMemoryAdamW(params, lr=0.001)
budget = aml.DynamicResourceBudgetManager(max_memory_mb=2048.0)

# 4. Minority Intelligence
prior_tracker = aml.OnlineClassPriorTracker(n_classes=2)
threshold_manager = aml.AdaptiveThresholdManager(n_classes=2)

# 5. Controllers (ULC)
controller = aml.UnifiedLearningControllerV4_1(classifier=clf)
config = aml.ULCv41Config(spatial_discordance_threshold=0.25)

# 6. Safe Serialization (State)
aml.save_state("model_checkpoint", tensors, metadata)
```

---

## 3. Parameter Naming Standardization Matrix

| Parameter Domain | Standard Name | Discouraged / Legacy Variants | Rationale & Scikit-learn Alignment |
|---|---|---|---|
| Feature Count | `n_features` | `max_features`, `num_features`, `dim` | Matches `sklearn.base.BaseEstimator.n_features_in_`. |
| Class Count | `n_classes` | `num_classes`, `n_labels` | Matches `sklearn` multi-class naming conventions. |
| Learning Rate | `lr` | `learning_rate`, `eta`, `step_size` | Matches PyTorch `torch.optim.Optimizer` convention (`param_groups[0]['lr']`). |
| Random Number Seed | `random_state` | `seed`, `random_seed` | Standard across Scikit-learn estimators. |
| Stream Batch Size | `batch_size` | `chunk_size`, `n_samples` | Standard streaming micro-batch naming. |
| Nearest Neighbors | `k` or `n_neighbors` | `knn`, `num_neighbors` | Matches `NearestNeighbors` parameter naming. |
| Decision Threshold | `threshold` | `cutoff`, `decision_boundary` | Standard classification threshold naming. |

---

## 4. Return Structure Standardization

All streaming steps across AdaptiveML adhere to predictable return tuples:
- **`step(...) -> Tuple[Directive, Dict[str, Any]]`**:
  - First element: strongly typed action directive (`DirectiveV4` or `ControllerDirective`).
  - Second element: comprehensive telemetry dictionary containing:
    - `"step"`: Integer cumulative step counter.
    - `"state"`: String identifier of automaton state.
    - `"scenario"`: Cross-pillar arbitration scenario string.
    - `"spatial_discordance"`: Float $[0.0, 1.0]$.
    - `"evidence"`: Serialized 10D evidence dictionary.
    - `"explanation"`: On-demand structured diagnostic summary.
    - `"n_retained_samples"`: Number of samples retained for training.

---

## 5. Backward Compatibility Guarantee

No existing public API was renamed, moved, or deleted. All previous imports:
```python
from adaptive_ml.ala import AdaptiveClassifier
from adaptive_ml.rla import RobustLearningPipeline
from adaptive_ml.rao import LowMemoryAdamW
from adaptive_ml.ulc import UnifiedLearningControllerV4
from adaptive_ml.minority import OnlineClassPriorTracker
```
remain completely valid. Top-level imports exist as purely additive developer conveniences.
