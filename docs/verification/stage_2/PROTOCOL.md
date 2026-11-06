# Stage 2: Verification Protocol & Acceptance Criteria
## Production Defect Remediation & Architecture Hardening

**Document Identifier:** `VERIF-STAGE-2-002`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Scope & Objectives

The Stage 2 verification protocol defines the formal requirements, test procedures, and acceptance gates for resolving DEF-006 and DEF-007, and hardening cross-pillar communication contracts across ALA, RAO, and ULC.

---

## 2. Test Suites & Pass Criteria

### 2.1 Test Battery Matrix

| Gate ID | Target Pillar / Defect | Test Method | Pass Criterion |
| :--- | :--- | :--- | :--- |
| **GATE-2.1** | DEF-006: Replay Buffer Contract | `test_classifier_replay_buffer_property` | `AdaptiveClassifier.replay_buffer` returns instance of `ClassBalancedReservoirReplay` or `None`. |
| **GATE-2.2** | DEF-006: Replay Selective Purge | `test_replay_buffer_purge_selective_preserves_minority` | Majority buffer pruned; minority buffer retention ratio = $1.0$ ($100\%$). |
| **GATE-2.3** | DEF-006: Replay Partial Purge | `test_replay_buffer_purge_partial` | 50% majority pruning; minority protected. |
| **GATE-2.4** | DEF-007: Optimizer Momentum Reset | `test_low_memory_adamw_reset_momenta_numpy` | `q_m` tensor norm $= 0.0$, `scale_m` tensor norm $= 0.0$, `step = 0`. |
| **GATE-2.5** | DEF-007: Optimizer LR Scaling | `test_low_memory_adamw_scale_learning_rate` | Group `lr` matches exact multiplier; non-positive scales raise `ValidationError`. |
| **GATE-2.6** | Integrated Cross-Pillar Coordination | `test_ulc_confirmed_drift_triggers_safe_purge_and_momentum_reset` | ULC confirmed drift successfully calls `purge_replay` and `reset_momenta` without unhandled exceptions. |
| **GATE-2.7** | Zero Baseline Regression | Full pytest battery | All 54 baseline tests continue to pass. |

---

## 3. Execution Protocol

1. **Pre-flight Check**:
   - Inspect Python 3.14 environment, PyTorch CPU availability, and NumPy baseline.
   - Run baseline test suite (`54 passed`).
2. **Implementation Execution**:
   - Apply DEF-006 fixes in [`adaptive_ml/ala/replay.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) and [`adaptive_ml/ala/classifier.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/classifier.py).
   - Apply DEF-007 fixes in [`adaptive_ml/rao/adamw.py`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py).
   - Harden controller invocation logic in [`adaptive_ml/ulc/controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py).
   - Expand state enumerations in [`adaptive_ml/ulc/directives.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/directives.py) and [`adaptive_ml/ulc/automaton.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/automaton.py).
3. **Automated Verification**:
   - Execute [`tests/unit/test_stage2_remediation.py`](file:///c:/projects/AdaptiveML/tests/unit/test_stage2_remediation.py).
   - Execute complete test battery across `tests/`.
4. **Empirical Benchmarking**:
   - Execute [`experiments/stage_2_production_remediation/run_stage2_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_2_production_remediation/run_stage2_experiment.py).
   - Output structured telemetry to JSON and CSV.
