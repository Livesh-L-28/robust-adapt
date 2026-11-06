# Configuration Design & Developer Experience: AdaptiveML

**Project:** AdaptiveML / aml-core (`0.1.0.dev0`)<br>
**Workspace:** `C:\projects\AdaptiveML`<br>
**Report Date:** 2026-11-06<br>
**Auditor:** Principal Python SDK Architect & Configuration Systems Engineer<br>
**Artifact Path:** [CONFIGURATION_DESIGN.md](file:///c:/projects/AdaptiveML/docs/verification/stage_8/CONFIGURATION_DESIGN.md)<br>

---

## 1. Executive Summary & Configuration Philosophy

AdaptiveML rejects monolithic, opaque configuration files. Instead, it employs:
1. **Decoupled Dataclasses**: Each pillar has dedicated, strongly typed configuration objects with automatic validation in `__post_init__`.
2. **Sensible Defaults**: Every component can be instantiated with zero arguments (`AdaptiveClassifier()`) and immediately runs with scientifically sound defaults.
3. **Explicit Validation Errors**: Out-of-bounds parameters raise actionable `ConfigurationError` or `ValueError` immediately upon initialization.
4. **Zero Hidden Cloud Requirements**: All configurations operate 100% locally on standard CPU hardware without remote API keys or network dependencies.
5. **Lossless JSON / Dataclass Serialization**: All configs can be exported via `asdict()` or loaded from JSON metadata.

---

## 2. Pillar Configuration Catalog

### 2.1. Vectorized Hoeffding Tree Config ([`TreeConfig`](file:///c:/projects/AdaptiveML/adaptive_ml/core/config.py#L12))
```python
from adaptive_ml.core import TreeConfig

cfg = TreeConfig(
    n_features=10,
    n_classes=2,
    grace_period=200,     # Batches between Hoeffding split attempts
    delta=1e-5,           # Confidence bound probability (1 - delta)
    tau_tie=0.05,         # Threshold tie-breaking parameter
    n_bins=32,            # Vectorized histogram bin count
    min_leaf_samples=10,  # Minimum instances before leaf split
    max_depth=20,         # Maximum tree depth guard
)
```

### 2.2. Reliability-Weighted ADWIN Config ([`ADWINConfig`](file:///c:/projects/AdaptiveML/adaptive_ml/core/config.py#L26))
```python
from adaptive_ml.core import ADWINConfig

cfg = ADWINConfig(
    delta=0.002,               # Statistical significance false alarm bound
    min_subwindow_weight=5.0,  # Minimum subwindow mass
    eps_r=1e-4,                # Minimum reliability floor
)
```

### 2.3. Low-Memory Quantized AdamW Config ([`AdamWConfig`](file:///c:/projects/AdaptiveML/adaptive_ml/core/config.py#L54))
```python
from adaptive_ml.core import AdamWConfig

cfg = AdamWConfig(
    lr=0.001,
    betas=(0.9, 0.999),
    eps=1e-8,
    weight_decay=0.01,
    block_size=256,       # 8-bit quantization block size
)
```

### 2.4. ULC-v4.1 Hybrid Controller Config ([`ULCv41Config`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py#L29))
```python
from adaptive_ml.ulc import ULCv41Config

cfg = ULCv41Config(
    spatial_k=5,                           # Nearest neighbors for spatial coherence
    spatial_discordance_threshold=0.25,     # Threshold discriminating noise from drift
    prior_freeze_threshold=0.30,           # Freezes minority prior updates under noise
    tau_tie=0.10,                          # Hoeffding tie parameter
    gamma_smoothing=0.50,                  # Moving average factor for threshold smoothing
    max_noise_dwell=20,                    # Timeout escaping absorbing noise states
    max_history_len=1000,                  # Bounded ring-buffer history capacity
    generate_explanations=False,           # Zero-overhead streaming mode
    cooldown_steps=10,                     # Steps in COOLDOWN state post-adaptation
)
```

---

## 3. Configuration Use Case Examples

### 3.1. Minimal Default Configuration (One-Liner)
```python
import adaptive_ml as aml

# Instantiates with optimal defaults
clf = aml.AdaptiveClassifier(n_features=4, n_classes=2)
controller = aml.UnifiedLearningControllerV4_1(classifier=clf)
```

### 3.2. Custom Highly Constrained Edge Device Configuration
```python
import adaptive_ml as aml

# Configure for low-memory micro-batch environment
config = aml.ULCv41Config(
    spatial_k=3,
    spatial_discordance_threshold=0.20,
    max_history_len=200,         # Minimal memory footprint
    generate_explanations=False, # High-throughput streaming
)

budget = aml.DynamicResourceBudgetManager(
    max_step_time_ms=50.0,
    max_memory_mb=256.0,         # 256 MB RAM ceiling
)

controller = aml.UnifiedLearningControllerV4_1(
    config=config,
    budget_manager=budget,
)
```

### 3.3. Invalid Configuration Handling (Early Actionable Rejection)
```python
import adaptive_ml as aml

try:
    # Attempt invalid hyperparameter bounds
    aml.ULCv41Config(spatial_discordance_threshold=1.5)
except ValueError as exc:
    print("Caught expected validation error:", exc)
    # Output: spatial_discordance_threshold must be in [0, 1], got 1.5
```

---

## 4. Configuration Serialization & Export

Configurations support native dictionary conversion:
```python
from dataclasses import asdict
import json

cfg_dict = asdict(config)
json_str = json.dumps(cfg_dict, indent=2)

# Reconstruction from JSON
restored_cfg = aml.ULCv41Config(**json.loads(json_str))
assert restored_cfg == config
```

---

## 5. Design Verification Summary

- [x] Strongly typed dataclasses for all core configurations.
- [x] Input validation guards reject invalid parameters during `__init__` / `__post_init__`.
- [x] Zero mandatory cloud dependencies.
- [x] Lossless JSON serialization tested and verified.
