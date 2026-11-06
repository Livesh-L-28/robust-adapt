# Getting Started — Configuration Guide

AdaptiveML emphasizes explicit, typed, and decoupled configuration. Every component can be configured via Python dataclasses, explicit constructor keyword arguments, or loaded from serializable dictionaries.

---

## 1. Core Configuration Dataclasses

### 1.1 Hoeffding Tree Configuration (`TreeConfig`)
Controls incremental decision tree growth, split confidence, and memory caps:

```python
from robust_adapt import TreeConfig, AdaptiveClassifier

config = TreeConfig(
    max_depth=8,              # Maximum depth of any tree branch (default: 10)
    grace_period=50,          # Minimum samples observed at a leaf before split test (default: 200)
    split_confidence=1e-4,    # Desired 1 - delta confidence for Hoeffding bound (default: 1e-4)
    tie_threshold=0.05,       # Threshold for breaking near-identical attribute ties (default: 0.05)
    memory_limit_mb=64.0      # Maximum memory allowed for tree nodes in MB (default: 64.0)
)

clf = AdaptiveClassifier(config=config)
```

### 1.2 ADWIN Drift Detector Configuration (`ADWINConfig`)
Tunes the statistical sensitivity of the adaptive sliding window:

```python
from robust_adapt import ADWINConfig, ADWIN

adwin_config = ADWINConfig(
    delta=0.002,              # Statistical significance threshold (default: 0.002)
    max_buckets=10,           # Max buckets per tier in exponential histogram (default: 5)
    min_window_length=10      # Minimum sub-window length before cut test (default: 10)
)

detector = ADWIN(config=adwin_config)
```

### 1.3 8-Bit Low-Memory Optimizer Configuration (`AdamWConfig`)
Controls learning rates, momentum parameters, and quantization modes:

```python
from robust_adapt import AdamWConfig

optimizer_config = AdamWConfig(
    lr=1e-3,                  # Base learning rate (default: 1e-3)
    betas=(0.9, 0.999),       # First and second moment coefficients (default: (0.9, 0.999))
    eps=1e-8,                 # Numerical stability denominator epsilon (default: 1e-8)
    weight_decay=1e-2,        # Decoupled L2 regularization weight (default: 1e-2)
    quantize_state=True       # Enable 8-bit dynamic moment quantization (default: True)
)
```

### 1.4 Unified Learning Controller Configuration (`ULCv41Config`)
Controls multi-pillar arbitration, spatial discordance sensitivity, and hysteresis:

```python
from robust_adapt import ULCv41Config, UnifiedLearningControllerV4_1

ulc_config = ULCv41Config(
    drift_threshold=0.35,     # Metric delta threshold to signal concept drift (default: 0.35)
    noise_threshold=0.60,     # Entropy threshold to signal label noise (default: 0.60)
    discordance_weight=0.40,  # Weight assigned to spatial discordance (default: 0.40)
    confidence_decay=0.95,    # Decay rate for temporal confidence tracking (default: 0.95)
    hysteresis_steps=3        # Required stable steps before de-escalation (default: 3)
)

controller = UnifiedLearningControllerV4_1(config=ulc_config)
```

---

## 2. Minimal vs. Custom Configurations

AdaptiveML adheres to sensible default configurations. You can initialize any component with zero arguments, pass keyword overrides, or provide a full configuration object:

```python
# 1. Zero-argument default initialization:
clf_default = AdaptiveClassifier()

# 2. Direct keyword override:
clf_custom = AdaptiveClassifier(max_depth=5, grace_period=100)

# 3. Full configuration dataclass:
clf_dataclass = AdaptiveClassifier(config=TreeConfig(max_depth=5, grace_period=100))
```

---

## 3. Configuration Validation & Error Handling

All configuration classes perform eager type and range validation at instantiation. Supplying invalid hyperparameters immediately raises [`ConfigurationError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py):

```python
from robust_adapt import TreeConfig, ConfigurationError

try:
    # Invalid: grace_period must be positive integer
    config = TreeConfig(grace_period=-10)
except ConfigurationError as err:
    print(f"Validation caught error: {err}")
```

---

## 4. Configuration Serialization

Configurations support conversion to and from JSON-compatible dictionaries for configuration management, infrastructure-as-code, and MLflow logging:

```python
from dataclasses import asdict
import json

# Export configuration
config_dict = asdict(ulc_config)
config_json = json.dumps(config_dict, indent=2)

# Reconstruct configuration
loaded_dict = json.loads(config_json)
restored_config = ULCv41Config(**loaded_dict)
```
