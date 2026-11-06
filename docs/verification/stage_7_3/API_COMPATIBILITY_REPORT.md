# API Compatibility & Controller Versioning Report: ULC-v4.1

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Target Package:** [`adaptive_ml/ulc/`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/)<br>
**Report Date:** 2026-11-06<br>
**Auditor:** API Compatibility & Systems Architecture Team<br>

---

## 1. Executive Summary & Compatibility Policy

A primary governance directive for Stage 7.3 is **zero silent breaking changes**:
- The existing baseline controllers ([`AdaptiveLearningController`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py) for v1–v3 and [`UnifiedLearningControllerV4`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_controller.py) for v4) must remain $100\%$ operational with their original signatures and default behaviors.
- The default controller version across the library remains unchanged.
- ULC-v4.1 is introduced as an explicit, opt-in named class: [`UnifiedLearningControllerV4_1`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py#L76) alongside its configuration dataclass [`ULCv41Config`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py#L29) and the utility function [`compute_spatial_discordance`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/spatial.py#L12).
- Project Owner authorization is required before promoting ULC-v4.1 as the library-wide default controller.

---

## 2. Controller Version Portfolio & Taxonomy

| Controller Name | Module Path | Stability Status | Recommended Use Case | Known Limitations |
|---|---|---|---|---|
| **ULC-v1 / v2 / v3** (`AdaptiveLearningController`) | [`adaptive_ml/ulc/controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py) | **Stable (Legacy)** | Simple streaming pipelines requiring basic ADWIN drift detection and RLA noise filtering without advanced Pareto arbitration. | Lacks 10D evidence vector; cannot handle complex cross-pillar conflicts (e.g. Scenarios B–J). |
| **ULC-v4** (`UnifiedLearningControllerV4`) | [`adaptive_ml/ulc/v4_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_controller.py) | **Production (Active Default)** | Multi-pillar streaming environments requiring 12-state automaton arbitration across ALA, RLA, RAO, and Minority Intelligence. | Subject to Scenario A absorbing deadlock under abrupt concept drift when model margin drops below $0.65$. |
| **ULC-v4.1 Hybrid** (`UnifiedLearningControllerV4_1`) | [`adaptive_ml/ulc/v4_1_controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py) | **Production Candidate (Promoted)** | Production workloads subject to simultaneous concept drift, severe label noise bursts, extreme class imbalance, and resource constraints. | Requires sufficient batch size ($n > k$, default $k=5$) for spatial discordance calculation. |

---

## 3. Public API Changes & Enhancements

### 3.1. Package Root Exports in [`adaptive_ml/ulc/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/__init__.py)

All 20 previous exports remain intact. Three new symbols are exported:
1. `compute_spatial_discordance`: Public function calculating mean $k$-NN label discordance in feature space.
2. `ULCv41Config`: Strongly typed dataclass encapsulating all ULC-v4.1 hyperparameters with automatic validation.
3. `UnifiedLearningControllerV4_1`: Master hybrid controller class.

### 3.2. [`CrossPillarConflictResolver.resolve_conflicts()`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/conflict_resolver.py#L28)

**Signature Evolution:**
```python
# Legacy signature (ULC-v4):
@staticmethod
def resolve_conflicts(
    directive: DirectiveV4,
    evidence: EvidenceVectorV4,
    confidence: ConfidenceScores,
) -> Tuple[DirectiveV4, str]:

# Enhanced signature (ULC-v4.1 backward-compatible):
@staticmethod
def resolve_conflicts(
    directive: DirectiveV4,
    evidence: EvidenceVectorV4,
    confidence: ConfidenceScores,
    spatial_discordance: Optional[float] = None,
    noise_dwell: int = 0,
) -> Tuple[DirectiveV4, str]:
```

**Backward Compatibility Verification:**
- When `spatial_discordance is None`, legacy callers (including `TestULCv4ScenariosAthroughJ.test_scenario_a_drift_alarm_during_severe_noise_burst`) execute the exact legacy logic, returning `"Scenario A: Noise vs Drift"` and `AutomatonStateV4.NOISE_BURST`.
- When `spatial_discordance` is supplied (float in $[0, 1]$), the discriminator distinguishes genuine drift ($d \le 0.25 \implies \text{CONFIRMED\_DRIFT}$) from noise bursts ($d > 0.25 \implies \text{NOISE\_BURST}$).
- Added `resolve_conflicts_v2` classmethod alias to support experimental candidate script conventions directly.

### 3.3. Public Controller Interface (`UnifiedLearningControllerV4_1`)

The controller provides standard scikit-learn / AdaptiveML streaming conventions:
- `__init__(config=None, classifier=None, optimizer=None, pipeline=None, budget_manager=None, prior_tracker=None, threshold_manager=None, concept_memory=None, automaton=None, generate_explanations=None)`
- `step(X, y, sample_ids=None, logits=None, delta_drift=None, current_loss=None, observed_delay=0.0) -> Tuple[DirectiveV4, Dict[str, Any]]`
- `explain(directive=None, evidence=None, scenario=None) -> Dict[str, Any]`
- `get_history(limit=None) -> List[Dict[str, Any]]`
- `get_intervention_history(limit=None) -> List[Dict[str, Any]]`
- `reset() -> None`
- `state_dict() -> Dict[str, Any]`
- `load_state_dict(state_dict: Dict[str, Any]) -> None`

---

## 4. Migration & Transition Guide

### 4.1. Migrating from ULC-v4 to ULC-v4.1

To upgrade an existing ULC-v4 pipeline to ULC-v4.1, replace the controller instantiation:

```python
# Before (ULC-v4):
from adaptive_ml.ulc import UnifiedLearningControllerV4

controller = UnifiedLearningControllerV4(
    classifier=clf,
    optimizer=opt,
    pipeline=rla_pipe,
    prior_tracker=prior_trk,
)

# After (ULC-v4.1):
from adaptive_ml.ulc import UnifiedLearningControllerV4_1, ULCv41Config

config = ULCv41Config(
    spatial_k=5,
    spatial_discordance_threshold=0.25,
    max_noise_dwell=20,
    generate_explanations=False,  # High-throughput streaming mode
)

controller = UnifiedLearningControllerV4_1(
    config=config,
    classifier=clf,
    optimizer=opt,
    pipeline=rla_pipe,
    prior_tracker=prior_trk,
)
```

### 4.2. Safe Fallback & Coexistence

Both controllers can exist side-by-side in the same application. No global state or singleton registries are modified. Upgrading does not require schema changes to checkpoint data if versioned loader dispatch is used.

---

## 5. Compatibility Verification Summary

- [x] All 121 existing unit and integration tests pass without regression.
- [x] `UnifiedLearningControllerV4` retains 100% legacy behavior.
- [x] `CrossPillarConflictResolver` retains 100% backward compatibility when `spatial_discordance=None`.
- [x] New symbols added strictly via extension, zero deletions from `__all__`.
- [x] ULC remains strictly optional; all pillars remain independently functional.
