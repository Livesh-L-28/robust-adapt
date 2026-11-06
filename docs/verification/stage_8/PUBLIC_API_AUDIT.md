# Public API Audit: AdaptiveML Architecture

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Audit Date:** 2026-11-06<br>
**Auditor:** Principal Python SDK Architect & API Design Specialist<br>
**Artifact Path:** [PUBLIC_API_AUDIT.md](file:///c:/projects/AdaptiveML/docs/verification/stage_8/PUBLIC_API_AUDIT.md)<br>

---

## 1. Executive Summary

This document performs an exhaustive audit of every public class, function, dataclass, and exception currently exported by AdaptiveML across its core modules:
1. **ALA (Adaptive Learning Algorithms)**
2. **RLA (Robust Learning Algorithms)**
3. **RAO (Resource-Aware Optimization)**
4. **Minority Intelligence**
5. **ULC & ULC-v4.1 (Unified Learning Controller)**
6. **State & Serialization**
7. **Core & Validation**

---

## 2. Pillar-by-Pillar Public API Inventory

### 2.1. Adaptive Learning Algorithms (ALA) — `adaptive_ml.ala`

| Class / Function | Module | Purpose | Parameters & Defaults | Return Type | Stability | Optional Deps |
|---|---|---|---|---|---|---|
| `AdaptiveClassifier` | `ala.classifier` | High-level streaming classifier wrapping Hoeffding Tree, ADWIN, and replay buffer. | `n_features: int = 10`, `n_classes: int = 2`, `grace_period: int = 200`, `delta: float = 1e-5`, `tau_tie: float = 0.05`, `replay_capacity: int = 1000`, `replay_ratio: float = 0.2`, `enable_drift_detection: bool = True`, `random_state: Optional[int] = None` | Instance | Stable | None |
| `VectorizedHoeffdingTree` | `ala.tree` | Very Fast Decision Tree (VFDT) with vectorized attribute histogram split tests. | `n_features: int`, `n_classes: int`, `grace_period: int = 200`, `delta: float = 1e-5`, `tau_tie: float = 0.05`, `n_bins: int = 32`, `min_leaf_samples: int = 10`, `max_depth: int = 20` | Instance | Stable | None |
| `ReliabilityWeightedADWIN` | `ala.adwin` | Adaptive sliding window drift detector weighted by sample reliability. | `delta: float = 0.002`, `min_subwindow_weight: float = 5.0`, `eps_r: float = 1e-4` | Instance | Stable | None |
| `CUSUMDetector` | `ala.detector` | Cumulative Sum control chart for abrupt distribution shift detection. | `target: float = 0.5`, `delta: float = 0.005`, `threshold: float = 5.0` | Instance | Stable | None |
| `PageHinkleyDetector` | `ala.detector` | Sequential analysis drift detector with directional change thresholding. | `delta: float = 0.005`, `threshold: float = 50.0`, `alpha: float = 0.9999` | Instance | Stable | None |
| `MultiDetectorConsensus` | `ala.detector` | Majority-vote consensus aggregator across diverse drift detectors. | `detectors: Optional[List[BaseDriftDetector]] = None`, `consensus_rule: str = "majority"` | Instance | Stable | None |
| `DriftClassifier` | `ala.drift_classifier` | Classifies drift events into abrupt, gradual, incremental, or virtual. | `window_size: int = 100`, `slope_threshold: float = 0.01` | Instance | Stable | None |
| `ConceptMemory` | `ala.concept_memory` | Memory store for prototypes of recurring concepts for instant recovery. | `similarity_threshold: float = 0.75`, `max_concepts: int = 10` | Instance | Stable | None |
| `DelayedLabelQueue` | `ala.delayed_labels` | FIFO matching queue pairing delayed labels with unconfirmed predictions. | `max_delay_steps: int = 1000`, `ttl_seconds: float = 3600.0` | Instance | Stable | None |
| `ClassBalancedReservoirReplay` | `ala.replay` | Stratified streaming reservoir buffer maintaining class parity. | `capacity: int = 5000`, `replay_ratio: float = 0.2` | Instance | Stable | None |

### 2.2. Robust Learning Algorithms (RLA) — `adaptive_ml.rla`

| Class / Function | Module | Purpose | Parameters & Defaults | Return Type | Stability | Optional Deps |
|---|---|---|---|---|---|---|
| `RobustLearningPipeline` | `rla.pipeline` | Coordinates reliability scoring, loss computation, and sample weighting. | `n_classes: int = 2`, `loss_type: str = "sce"`, `alpha: float = 1.0`, `beta: float = 1.0`, `min_reliability: float = 1e-4` | Instance | Stable | None |
| `MultiSignalReliabilityEngine` | `rla.reliability` | Synthesizes prediction margin, local feature density, and loss trend into reliability. | `n_classes: int = 2`, `n_neighbors: int = 5`, `margin_weight: float = 0.5`, `density_weight: float = 0.5` | Instance | Stable | None |
| `DensityAwareMarginScorer` | `rla.scorer` | Evaluates sample confidence scaled by local neighborhood kernel density. | `n_classes: int = 2`, `n_neighbors: int = 5`, `alpha: float = 1.0`, `gamma: float = 0.5` | Instance | Stable | None |
| `SymmetricCrossEntropyLoss` | `rla.losses` | Robust loss balancing cross-entropy with reverse cross-entropy ($L = \alpha \text{CE} + \beta \text{RCE}$). | `alpha: float = 1.0`, `beta: float = 1.0`, `eps: float = 1e-7` | Instance | Stable | `torch` (optional) |
| `GeneralizedCrossEntropyLoss` | `rla.losses` | Negative Box-Cox transformation bounding gradients on corrupt samples. | `q: float = 0.7`, `eps: float = 1e-7` | Instance | Stable | `torch` (optional) |
| `FocalLoss` | `rla.losses` | Modulated loss focusing learning on hard, clean boundary instances. | `gamma: float = 2.0`, `alpha: Optional[float] = None` | Instance | Stable | `torch` (optional) |
| `ReliabilityWeightedLoss` | `rla.losses` | Multiplies loss and finite-difference gradients by sample reliability scores. | `base_loss: Any`, `min_weight: float = 0.0` | Instance | Stable | None |
| `ClassBalancedWeights` | `rla.weighting` | Computes effective number of samples weighting: $W_c = (1 - \beta) / (1 - \beta^{n_c})$. | `beta: float = 0.9999` | Instance | Stable | None |
| `EvidenceBasedLabelCorrector` | `rla.label_correction` | Auditable probabilistic label correction with automatic rollback safeguards. | `confidence_threshold: float = 0.85`, `rollback_window: int = 100` | Instance | Stable | None |

### 2.3. Resource-Aware Optimization (RAO) — `adaptive_ml.rao`

| Class / Function | Module | Purpose | Parameters & Defaults | Return Type | Stability | Optional Deps |
|---|---|---|---|---|---|---|
| `LowMemoryAdamW` | `rao.adamw` | 8-bit block-quantized AdamW optimizer saving $75\%$ first and second momentum memory. | `params: Any`, `lr: float = 0.001`, `betas: Tuple[float, float] = (0.9, 0.999)`, `eps: float = 1e-8`, `weight_decay: float = 0.01`, `block_size: int = 256` | Instance | Stable | `torch` (optional) |
| `BlockQuantizer` | `rao.quantizer` | Symmetric block-wise FP32 to INT8 quantizer and dequantizer. | `block_size: int = 256` | Instance | Stable | None |
| `DynamicResourceBudgetManager` | `rao.budget` | Multi-dimensional constraint manager monitoring step time (ms) and RAM (MB). | `max_step_time_ms: float = 100.0`, `max_memory_mb: float = 2048.0`, `min_batch_size: int = 16`, `max_batch_size: int = 512`, `warning_threshold: float = 0.80` | Instance | Stable | `psutil` (optional) |
| `ExecutionProfiler` | `rao.profiler` | Low-overhead execution timer recording mean, P50, P95, and P99 latency percentiles. | `history_len: int = 1000` | Instance | Stable | None |
| `DeviceCapabilityDetector` | `rao.device` | Probes host CPU cores, memory limits, and accelerator availability (CUDA/ROCm). | None | Instance | Stable | None |
| `ResilientCheckpointManager` | `rao.recovery` | High-frequency atomic checkpointing with automatic pruning and recovery hooks. | `checkpoint_dir: str`, `max_checkpoints: int = 3` | Instance | Stable | `safetensors` (optional) |

### 2.4. Adaptive Minority Intelligence — `adaptive_ml.minority`

| Class / Function | Module | Purpose | Parameters & Defaults | Return Type | Stability | Optional Deps |
|---|---|---|---|---|---|---|
| `OnlineClassPriorTracker` | `minority.prior` | Exponential moving average class prior tracking with Laplace smoothing. | `n_classes: int = 2`, `alpha: float = 0.05`, `window_size: int = 500`, `smoothing: float = 1.0`, `imbalance_threshold: float = 0.20` | Instance | Stable | None |
| `AdaptiveThresholdManager` | `minority.threshold` | Calibrates decision thresholds dynamically to optimize F1 / recall under imbalance. | `n_classes: int = 2`, `gamma: float = 0.50`, `cost_ratio: float = 1.0` | Instance | Stable | None |
| `MinorityAwareReplayBuffer` | `minority.replay` | Dedicated quota-guaranteed experience replay buffer for underrepresented classes. | `capacity: int = 1000`, `minority_quota: float = 0.50` | Instance | Stable | None |
| `ClassAwareCalibrator` | `minority.calibration` | Streaming isotonic probability calibration adjusted for class imbalance. | `n_bins: int = 10` | Instance | Stable | None |

### 2.5. Unified Learning Controller (ULC) — `adaptive_ml.ulc`

| Class / Function | Module | Purpose | Parameters & Defaults | Return Type | Stability | Optional Deps |
|---|---|---|---|---|---|---|
| `AdaptiveLearningController` | `ulc.controller` | Baseline ULC (v1-v3) dual-evidence finite state arbitrator. | `classifier=None`, `rla_pipeline=None`, `optimizer=None`, `tau_R: float = 0.65`, `cooldown_steps: int = 10` | Instance | Stable (Legacy) | None |
| `UnifiedLearningControllerV4` | `ulc.v4_controller` | ULC-v4 12-state automaton with 10D evidence vector and Scenarios A-J arbitration. | `classifier=None`, `optimizer=None`, `adwin=None`, `pipeline=None`, `budget_manager=None`, `prior_tracker=None`, `threshold_manager=None`, `concept_memory=None` | Instance | Stable (Default) | None |
| `UnifiedLearningControllerV4_1` | `ulc.v4_1_controller` | ULC-v4.1 Hybrid resolving Scenario A deadlock via spatial discordance gating. | `config: Optional[ULCv41Config] = None`, `classifier=None`, `optimizer=None`, `adwin=None`, `pipeline=None`, `budget_manager=None`, `prior_tracker=None`, `threshold_manager=None`, `concept_memory=None` | Instance | Promoted Candidate | None |
| `ULCv41Config` | `ulc.v4_1_controller` | Strongly validated hyperparameter configuration dataclass for ULC-v4.1. | `spatial_k: int = 5`, `spatial_discordance_threshold: float = 0.25`, `prior_freeze_threshold: float = 0.30`, `tau_tie: float = 0.10`, `gamma_smoothing: float = 0.50`, `max_noise_dwell: int = 20`, `max_history_len: int = 1000`, `generate_explanations: bool = False`, `cooldown_steps: int = 10` | Dataclass | Promoted Candidate | None |
| `compute_spatial_discordance` | `ulc.spatial` | Mean $k$-NN label discordance in feature space ($[0, 1]$). | `X: np.ndarray`, `y: np.ndarray`, `k: int = 5`, `metric: str = "euclidean"` | `float` | Promoted Candidate | None |

---

## 3. Discovered API Inconsistencies & Remedies

1. **Top-Level Package Namespace Inaccessibility:**
   - *Issue:* Top-level [`adaptive_ml/__init__.py`](file:///c:/projects/AdaptiveML/adaptive_ml/__init__.py) does not expose core classes. Users must import from deep submodules (`adaptive_ml.ala.classifier.AdaptiveClassifier`).
   - *Remedy:* Standardize top-level exports in `adaptive_ml` to expose key classes lazily or directly without adding heavy runtime import overhead.
2. **Optimizer Parameter Naming:**
   - *Issue:* `AdaptiveClassifier` uses `n_features`, but early tests confused it with `max_features`. `LowMemoryAdamW` uses `lr`, while some user code assumed `learning_rate`.
   - *Remedy:* Preserve canonical `lr` and `n_features`, add property alias or explicit validation messages.
3. **Configuration Object Diversity:**
   - *Issue:* `TreeConfig` and `ADWINConfig` in `core.config` are frozen dataclasses, while `ULCv41Config` is mutable with `__post_init__` validation.
   - *Remedy:* Create a consistent configuration paradigm: dataclasses with clear parameter validation, serialization via `asdict()`, and clear defaults.
4. **Exception Hierarchy Completeness:**
   - *Issue:* `adaptive_ml.core.exceptions` defines 8 exception classes, but some submodules raised generic `ValueError` or `AttributeError` for domain-specific errors.
   - *Remedy:* Document the full exception tree and map errors to `AdaptiveMLError` subclasses.

---

## 4. API Audit Conclusion

AdaptiveML has a remarkably comprehensive and sound underlying algorithm implementation across all four pillars. The primary requirement for Stage 8 is unifying the developer import surface, creating unified top-level SDK access, and providing clear, executable tutorials and documentation.
