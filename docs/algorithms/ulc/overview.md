# ULC-v5: Unified Learning Controller Overview

**ULC-v5 (Unified Learning Controller V5)** is the master orchestration and arbitration engine of AdaptiveML.

---

## 1. Why Unified Coordination Exists

Without unified coordination, independent streaming modules frequently clash:
- A drift detector requests a model reset because error rates elevated.
- A noise filter treats the elevated errors as corrupted labels and drops the samples.
- An imbalanced prior tracker attempts to adjust decision thresholds simultaneously.

ULC-v5 unifies these components into a single coherent prequential learning loop, evaluating evidence from all pillars before executing any structural intervention.

---

## 2. Core Capabilities

- **Expected Utility Scoring**: Arbitrates actions by balancing expected generalization benefit against operational intervention cost.
- **Five-Tier Intervention Hierarchy**: Scales intervention severity from passive monitoring (NOOP) up to catastrophic emergency recovery (Hard Reset).
- **Anti-Thrashing Exponential Cooldown**: Dynamic lockout suppresses cyclic reset loops under adversarial noise.
- **Explainability & Telemetry**: Every decision outputs a structured `ULCv5Directive` detailing the tier, semantic action name, confidence score, and operational rationale.
