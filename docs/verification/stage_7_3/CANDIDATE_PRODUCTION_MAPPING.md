# Candidate-to-Production Architectural Mapping: ULC-v4.1

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Source Candidate:** [`experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/candidate_controllers.py)<br>
**Target Package:** [`adaptive_ml/ulc/`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/)<br>
**Mapping Date:** 2026-11-06<br>
**Auditor:** Systems Architecture & Release Engineering Team<br>

---

## 1. Architectural Mapping Matrix

| Experimental Component | Production Destination | Dependencies | Public / Private | State Ownership | Serialization | Integration Risk & Mitigation |
|---|---|---|---|---|---|---|
| `compute_spatial_discordance` | [`adaptive_ml/ulc/spatial.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/spatial.py) | `numpy`, `check_array_2d`, `check_labels_1d` | **Public Function** | Stateless | None | Small batches ($n \le k$): return $0.0$; High dimensionality: validate numeric stability. |
| `Candidate1_LightweightEvidence` | Integrated in [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | `numpy`, `EvidenceSynthesizerV4`, `EvidenceVectorV4` | Private / Internal | Entropy cache, loss trend | Persisted in `state_dict` | Redundant code: incorporate as default lightweight synthesizer in controller. |
| `Candidate2_AdaptiveConfidence` | Integrated in [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | `ConfidenceEngine`, `ConfidenceScores`, `EvidenceVectorV4` | Private / Internal | Stateless | None | Maintain compatibility with baseline confidence formulas. |
| `Candidate3_AdaptiveArbitrator` | Integrated in [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | `MultiObjectiveArbitrator` | Private / Internal | Pareto weights | Serializable | Fall back to full Pareto optimization under active alerts. |
| `Candidate4_MinorityController` | Integrated in [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | Minority Prior Tracker, Threshold Manager | Private / Internal | Prior state, thresholds | Delegated to submodules | Safe handling when minority submodule is omitted (`None`). |
| `Candidate5_ConflictResolver` | Enhanced into [`adaptive_ml/ulc/conflict_resolver.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/conflict_resolver.py) | `CrossPillarConflictResolver`, `DirectiveV4`, `EvidenceVectorV4` | **Public Method Enhancement** | Stateless | None | Legacy v4 callers pass `spatial_discordance=None` to preserve legacy behavior. |
| `Candidate6_OnDemandExplainer` | Integrated in [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | `ULCExplainer` | Private / Internal | Template cache | None | Allow on-demand full narrative generation via `.explain()`. |
| `HybridMasterControllerV4_1` | [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) as `UnifiedLearningControllerV4_1` | All pillars (optional), `spatial.py`, `conflict_resolver.py`, `v4_automaton.py` | **Public Master Controller** | History ring-buffers, dwell counters, step counter | Full `state_dict()` & `load_state_dict()` via `adaptive_ml.state.serializer` | Default controller unchanged; exposed as explicit named candidate class. |
| Configuration Dataclass | [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) as `ULCv41Config` | `dataclasses.dataclass` | **Public Dataclass** | Immutable config | JSON-serializable in checkpoint metadata | Type and range validation on all hyperparameters. |

---

## 2. Production File Organization

To prevent namespace clutter, avoid circular dependencies, and maintain the clean structure of `adaptive_ml/ulc/`, the integration is partitioned into:

```
adaptive_ml/ulc/
├── __init__.py                 [MODIFIED] Exports UnifiedLearningControllerV4_1, ULCv41Config, compute_spatial_discordance
├── arbitrator.py               [PRESERVED] Multi-objective Pareto arbitrator
├── automaton.py                [PRESERVED] Baseline v1-v3 automaton
├── confidence.py               [PRESERVED] Confidence scoring engine
├── conflict_resolver.py        [ENHANCED] Added spatial_discordance parameter with legacy fallback
├── controller.py               [PRESERVED] Baseline v1-v3 controller
├── directives.py               [PRESERVED] Baseline v1-v3 directives
├── evidence.py                 [PRESERVED] Baseline v1-v3 evidence vector
├── explainer.py                [PRESERVED] Human-readable explainability engine
├── spatial.py                  [NEW] Vectorized spatial discordance calculation
├── v4_automaton.py             [PRESERVED] 12-state automaton and DirectiveV4 dataclass
├── v4_controller.py            [PRESERVED] Original ULC-v4 production controller
├── v4_evidence.py              [PRESERVED] 10D evidence synthesis and schema
└── v4_1_controller.py          [NEW] UnifiedLearningControllerV4_1 with full lifecycle & checkpointing
```

---

## 3. Detailed Component Specification

### 3.1. `adaptive_ml/ulc/spatial.py`
- **Function:** `compute_spatial_discordance(X: np.ndarray, y: np.ndarray, k: int = 5, metric: str = "euclidean") -> float`
- **Guarantees:**
  - Validates `X` is 2D float array, `y` is 1D int array of matching length.
  - If $n \le k$, returns $0.0$.
  - Computes pairwise Euclidean distances vectorially using broadcasting.
  - Excludes diagonal (self-distances) via `np.fill_diagonal(dist, np.inf)`.
  - Obtains $k$ nearest neighbors via `np.argpartition(dist, k, axis=1)[:, :k]`.
  - Calculates fraction of discordant neighbor labels:
    $$\text{discordance} = \frac{1}{n} \sum_{i=1}^n \frac{1}{k} \sum_{j \in \mathcal{N}_k(i)} \mathbb{I}(y_j \neq y_i)$$
  - Returns strictly bounded float in $[0.0, 1.0]$.
  - Zero memory leaks, pure NumPy operations.

### 3.2. `adaptive_ml/ulc/conflict_resolver.py`
- **Method:** `CrossPillarConflictResolver.resolve_conflicts(...)`
- **Enhanced Signature:**
  ```python
  @staticmethod
  def resolve_conflicts(
      directive: DirectiveV4,
      evidence: EvidenceVectorV4,
      confidence: ConfidenceScores,
      spatial_discordance: Optional[float] = None,
      noise_dwell: int = 0,
  ) -> Tuple[DirectiveV4, str]:
  ```
- **Backward Compatibility Guarantee:**
  - If `spatial_discordance is None`:
    Executes original legacy check `if evidence.delta_drift >= 1.0 and evidence.mean_reliability < 0.65:` $\rightarrow$ returns `NOISE_BURST`. Existing unit and integration tests remain $100\%$ unaffected.
  - If `spatial_discordance is not None`:
    - If `evidence.delta_drift >= 1.0`:
      - If `spatial_discordance > 0.25`:
        Confirmed label noise burst $\rightarrow$ returns `NOISE_BURST` with noise filtering.
      - If `spatial_discordance <= 0.25`:
        Confirmed genuine concept drift $\rightarrow$ returns `CONFIRMED_DRIFT` with model adaptation and momentum reset.
  - Also exposes alias `resolve_conflicts_v2` matching candidate controller conventions.

### 3.3. `adaptive_ml/ulc/v4_1_controller.py`
- **Class:** `UnifiedLearningControllerV4_1`
- **Configuration:** `ULCv41Config` dataclass with parameter validation:
  - `tau_tie: float = 0.10` (Hoeffding tie-breaking parameter)
  - `gamma_smoothing: float = 0.50` (Threshold smoothing)
  - `spatial_discordance_threshold: float = 0.25`
  - `prior_freeze_threshold: float = 0.30`
  - `max_noise_dwell: int = 20` (Timeout escaping noise states)
  - `generate_explanations: bool = False` (On-demand telemetry)
  - `max_history_len: int = 1000` (Bounded ring buffer)
  - `cooldown_steps: int = 10`
- **Lifecycle Methods:**
  - `__init__(self, config: Optional[ULCv41Config] = None, classifier=None, optimizer=None, pipeline=None, budget_manager=None, prior_tracker=None, threshold_manager=None, concept_memory=None, automaton=None)`
  - `step(self, X, y, logits=None, delta_drift=None, current_loss=None, observed_delay=0.0) -> Tuple[DirectiveV4, Dict[str, Any]]`
  - `explain(self, directive=None, evidence=None, scenario=None) -> Dict[str, Any]`
  - `get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]`
  - `state_dict(self) -> Dict[str, Any]` (Checkpoint export)
  - `load_state_dict(self, state: Dict[str, Any]) -> None` (Checkpoint recovery)
  - `reset(self) -> None` (Clean state reset)

---

## 4. Public API & Governance Audit

1. **Package Exports in [`adaptive_ml/ulc/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/__init__.py):**
   - Preserves all 20 existing exports.
   - Appends:
     - `"compute_spatial_discordance"`
     - `"ULCv41Config"`
     - `"UnifiedLearningControllerV4_1"`
2. **Default Controller Policy:**
   - The default controller for users constructing `UnifiedLearningControllerV4` or `AdaptiveLearningController` is **NOT altered**.
   - `UnifiedLearningControllerV4_1` is offered as an explicit class for users seeking ULC-v4.1 capabilities.
3. **Pillar Independence:**
   - Pillars ALA, RLA, RAO, and Minority remain $100\%$ decoupled. None import `adaptive_ml.ulc`.

---

## 5. Verification Mapping Checklist

- [x] Experimental Candidate classes mapped to production destinations.
- [x] Zero extraneous experimental scaffolding copied to production.
- [x] Backward compatibility preserved for all existing test callers.
- [x] State serialization and checkpointing designed with Safetensors/JSON standards.
- [x] Bounded memory constraints ($O(1)$) incorporated into controller architecture.
