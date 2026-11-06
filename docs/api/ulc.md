# API Reference: Unified Learning Controller (`adaptive_ml.ulc`)

The `adaptive_ml.ulc` module houses the master hybrid controller coordinating all four pillars (ALA, RLA, RAO, ULC) and Minority Intelligence.

---

## 1. Class: `UnifiedLearningControllerV4_1`

```python
class UnifiedLearningControllerV4_1(
    config: Optional[ULCv41Config] = None,
    classifier: Optional[Any] = None,
    optimizer: Optional[Any] = None,
    adwin: Optional[Any] = None,
    pipeline: Optional[Any] = None,
    budget_manager: Optional[Any] = None,
    prior_tracker: Optional[Any] = None,
    threshold_manager: Optional[Any] = None,
    concept_memory: Optional[Any] = None,
    automaton: Optional[ArbitrationAutomatonV4] = None,
    generate_explanations: Optional[bool] = None,
)
```

Production-promoted master controller integrating spatial feature discordance gating, noise-gated prior tracking, maximum dwell timeout escape, and full checkpoint serialization.

### Parameters
- **`config`** (`Optional[ULCv41Config]`): Configuration dataclass.
- **`classifier`** (`Optional[Any]`): Streaming classifier instance.
- **`optimizer`** (`Optional[Any]`): Low-memory optimizer instance.
- **`adwin`** (`Optional[Any]`): Drift detector.
- **`pipeline`** (`Optional[Any]`): Robust learning pipeline.
- **`budget_manager`** (`Optional[Any]`): Dynamic resource budget manager.
- **`prior_tracker`** (`Optional[Any]`): Online class prior tracker.
- **`threshold_manager`** (`Optional[Any]`): Adaptive threshold manager.
- **`concept_memory`** (`Optional[Any]`): Concept memory instance.

### Methods
- **`step(X, y, sample_ids=None, logits=None, delta_drift=None, current_loss=None, observed_delay=0.0) -> Tuple[DirectiveV4, dict]`**: Executes coordinated streaming arbitration across all connected pillars; returns action directive and telemetry dictionary.
- **`explain_last_decision() -> dict`**: Emits complete on-demand explainability justification for the most recent step.
- **`state_dict() -> dict`**: Serializes full controller automaton, telemetry history, and ring-buffers.
- **`load_state_dict(state: dict) -> None`**: Restores controller state from checkpoint.

---

## 2. Configuration Dataclass: `ULCv41Config`

```python
@dataclass
class ULCv41Config:
    spatial_k: int = 5
    spatial_discordance_threshold: float = 0.25
    prior_freeze_threshold: float = 0.30
    tau_tie: float = 0.10
    gamma_smoothing: float = 0.50
    max_noise_dwell: int = 20
    max_history_len: int = 1000
    generate_explanations: bool = False
    cooldown_steps: int = 10
```

---

## 3. Function: `compute_spatial_discordance`

```python
def compute_spatial_discordance(
    X: np.ndarray,
    y: np.ndarray,
    k: int = 5,
) -> float
```

Computes geometric discordance $\mathcal{D}_s \in [0, 1]$ between feature space topology and reported labels via k-NN graph agreement.
- $\mathcal{D}_s \le 0.30$: Structured, localized transition (confirms true concept drift).
- $\mathcal{D}_s > 0.30$: Random, scattered corruption (confirms label noise burst).

---

## 4. Class: `UnifiedLearningControllerV5`

```python
class UnifiedLearningControllerV5(
    n_features: int,
    n_classes: int = 2,
    config: Optional[ULCv5Config] = None,
)
```

Turnkey multi-tier calibrated streaming controller integrating five-tier intervention hierarchy, expected utility scoring, episodic concept memory restoration, and dynamic RLA gating.

### Methods
- **`step(X_b: np.ndarray, y_b: np.ndarray) -> Tuple[ULCv5Directive, Dict[str, Any]]`**: Prequential evaluation, telemetry collection, utility-scored arbitration, and learning update.
- **`predict(X) -> np.ndarray`**: Predicts target labels.
- **`predict_proba(X) -> np.ndarray`**: Predicts class posterior probabilities.
- **`score(X, y) -> float`**: Computes mean classification accuracy.
- **`reset() -> None`**: Completely resets controller state.
- **`state_dict() -> Dict[str, Any]`**: Serializes complete controller state.
- **`load_state_dict(state: Dict[str, Any]) -> None`**: Restores complete controller state.

---

## 5. Class: `ULCv5Config`

```python
@dataclass
class ULCv5Config:
    grace_period: int = 50
    delta: float = 0.002
    similarity_threshold: float = 0.82
    base_cooldown: int = 5
    max_concepts: int = 5
    replay_capacity: int = 1000
    catastrophic_drift_threshold: float = 0.95
    gate_rla_on_clean_stream: bool = True
```

---

## 6. Enum: `InterventionTier`

```python
class InterventionTier(str, Enum):
    TIER_0_NOOP = "TIER_0_NOOP"
    TIER_1_PARAM_DAMPING = "TIER_1_PARAM_DAMPING"
    TIER_2_CONCEPT_RESTORE = "TIER_2_CONCEPT_RESTORE"
    TIER_3_SOFT_REPLAY_RESET = "TIER_3_SOFT_REPLAY_RESET"
    TIER_4_HARD_RESET = "TIER_4_HARD_RESET"
```

---

## 7. Class: `UtilityScorer`

```python
class UtilityScorer:
    @classmethod
    def score_action(
        cls,
        tier: InterventionTier,
        confidence: float,
        drift_magnitude: float,
        is_recurrent: bool,
    ) -> float
```

Computes scalar expected utility: $U = \text{Confidence} \times \text{Benefit} - \text{Cost}$.
