# Unified Learning Controller (ULC) User Guide

This guide covers coordinating ALA, RLA, RAO, and Minority Intelligence dynamically using both the baseline `AdaptiveLearningController` (ULC-v1–v3) and the promoted `UnifiedLearningControllerV4_1` (ULC-v4.1 Hybrid).

---

## 1. Controller Selection & Stability Taxonomy

AdaptiveML provides three tiers of Unified Learning Controllers:

1. **`AdaptiveLearningController` (ULC-v1–v3, Stable Baseline)**: Simple streaming coordinator for basic ADWIN drift detection and RLA noise filtering.
2. **`UnifiedLearningControllerV4` (ULC-v4, Production Default)**: Full 12-state automaton with 10D cross-pillar evidence vectors and Scenarios A–J conflict resolution.
3. **`UnifiedLearningControllerV4_1` (ULC-v4.1 Hybrid, Promoted Production Candidate)**: Remediates the Scenario A absorbing deadlock using spatial feature discordance, noise-gated minority prior tracking, and on-demand explainability.

---

## 2. ULC-v4.1 Quickstart & Four-Pillar Streaming Pipeline

```python
import numpy as np
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.ala.concept_memory import ConceptMemory
from robust_adapt.rla.pipeline import RobustLearningPipeline
from robust_adapt.rao.adamw import LowMemoryAdamW
from robust_adapt.rao.budget import DynamicResourceBudgetManager
from robust_adapt.minority import OnlineClassPriorTracker, AdaptiveThresholdManager
from robust_adapt.ulc import UnifiedLearningControllerV4_1, ULCv41Config

# 1. Configure ULC-v4.1
config = ULCv41Config(
    spatial_k=5,
    spatial_discordance_threshold=0.25,
    prior_freeze_threshold=0.30,
    max_noise_dwell=20,
    generate_explanations=False,  # High-throughput streaming mode
)

# 2. Initialize decoupled pillars
clf = AdaptiveClassifier(n_features=4, n_classes=2, grace_period=10)
pipeline = RobustLearningPipeline(n_classes=2)
budget = DynamicResourceBudgetManager(max_memory_mb=2048.0)
prior_tracker = OnlineClassPriorTracker(n_classes=2)
threshold_manager = AdaptiveThresholdManager(n_classes=2, gamma=0.50)
concept_memory = ConceptMemory(max_concepts=5)

# 3. Instantiate Master Controller
controller = UnifiedLearningControllerV4_1(
    config=config,
    classifier=clf,
    pipeline=pipeline,
    budget_manager=budget,
    prior_tracker=prior_tracker,
    threshold_manager=threshold_manager,
    concept_memory=concept_memory,
)

# 4. Stream processing loop
for step in range(50):
    X = np.random.randn(30, 4)
    y = np.random.choice([0, 1], size=30)

    directive, telemetry = controller.step(X, y)
    print(f"Step {step:02d} | State: {directive.state.value} | "
          f"Discordance: {telemetry['spatial_discordance']:.3f} | "
          f"Retained: {telemetry['n_retained_samples']}")
```

---

## 3. Optional Pillar & Standalone Usage

ULC-v4.1 does not require all pillars to be enabled simultaneously. Any pillar can be omitted (`None`):

```python
# Minimal controller with only classifier connected
controller = UnifiedLearningControllerV4_1(classifier=clf)

# Controller running without any submodules for telemetry arbitration
standalone_controller = UnifiedLearningControllerV4_1()
directive, telemetry = standalone_controller.step(X, y)
```

---

## 4. Diagnostics & On-Demand Explainability

To minimize streaming latency, ULC-v4.1 disables eager natural language string formatting by default. When an explanation is needed for auditing or root cause analysis:

```python
# Generate structured explanation narrative on demand
explanation = controller.explain()
print("Scenario:", explanation["scenario"])
print("State:", explanation["state"])
print("Narrative:", explanation["narrative"])
```

---

## 5. Checkpoint Serialization & Disaster Recovery

ULC-v4.1 implements native `state_dict()` and `load_state_dict()` compatible with `adaptive_ml.state.serializer`:

```python
from robust_adapt.state.serializer import save_state, load_state

# Save state securely without pickle
state = controller.state_dict()
save_state("checkpoints/controller_state", tensors={}, metadata=state)

# Restore state into a fresh controller
_, loaded_meta = load_state("checkpoints/controller_state")
new_controller = UnifiedLearningControllerV4_1()
new_controller.load_state_dict(loaded_meta)
```

---

## 6. ULC-v5 Multi-Tier Calibrated Controller & Migration Guide

### 6.1 Overview of ULC-v5
`UnifiedLearningControllerV5` (ULC-v5) introduces a **Five-Tier Intervention Hierarchy** governed by **Expected Utility Scoring** ($U = \text{Confidence} \times \text{Benefit} - \text{Cost}$) to eliminate unnecessary catastrophic resets on streaming data while maintaining robust recovery:

- **Tier 0 (`TIER_0_NOOP`)**: Incremental learning during normal operation or cooldown backoff.
- **Tier 1 (`TIER_1_PARAM_DAMPING`)**: Non-structural parameter damping for transient variance spikes.
- **Tier 2 (`TIER_2_CONCEPT_RESTORE`)**: High-utility restoration of historical concepts from episodic memory.
- **Tier 3 (`TIER_3_SOFT_REPLAY_RESET`)**: Structural soft reset seeded with rehearsal samples from reservoir replay.
- **Tier 4 (`TIER_4_HARD_RESET`)**: Protected emergency hard reset when drift confidence $\ge 0.95$ and damping fails repeatedly.

### 6.2 Quickstart with ULC-v5

```python
import numpy as np
from robust_adapt.ulc import UnifiedLearningControllerV5, ULCv5Config, InterventionTier

config = ULCv5Config(
    grace_period=20,
    delta=0.005,
    similarity_threshold=0.82,
    base_cooldown=3,
    catastrophic_drift_threshold=0.95,
)

controller = UnifiedLearningControllerV5(
    n_features=4,
    n_classes=2,
    config=config,
)

for step in range(100):
    X = np.random.randn(30, 4)
    y = np.random.choice([0, 1], size=30)
    directive, telemetry = controller.step(X, y)
    if directive.tier != InterventionTier.TIER_0_NOOP:
        print(f"Intervention at step {step}: {directive.action_name} (Utility: {directive.expected_utility:.2f})")
```

### 6.3 Migrating from ULC-v4.1 to ULC-v5

| Feature / Aspect | ULC-v4.1 Hybrid | ULC-v5 Calibrated |
|---|---|---|
| **Intervention Architecture** | Binary full reset on unmitigated drift | 5-tier graduated hierarchy (NOOP, Damping, Restore, Soft Reset, Hard Reset) |
| **Recurring Concepts** | External lookup | Native episodic memory with cosine fingerprinter |
| **Arbitration Mechanism** | Heuristic 12-state automaton | Expected utility scoring ($U = c \cdot B - C$) |
| **Thrashing Mitigation** | Static noise dwell counter | Recovery-aware exponential cooldown backoff |
| **Catastrophic Reset Policy** | Triggered frequently on drift | Protected emergency escalation ($\ge 0.95$ confidence) |
