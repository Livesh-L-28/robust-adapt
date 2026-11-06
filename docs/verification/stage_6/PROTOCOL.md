# Stage 6: Verification Protocol & Acceptance Criteria
## RAO 2.0 (Advanced Resource-Aware Optimization)

**Document Identifier:** `VERIF-STAGE-6-002`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Acceptance Gates

| Gate ID | RAO 2.0 Module | Test Method | Pass Criterion |
| :--- | :--- | :--- | :--- |
| **GATE-6.1** | Dynamic Budget Throttling | `test_normal_and_throttling_transitions` | Correctly transitions to `CRITICAL` and shrinks batch size when step time exceeds target ceiling. |
| **GATE-6.2** | Operation Shedding Predicate | `test_normal_and_throttling_transitions` | `should_skip_expensive_ops()` returns True under `CRITICAL` or `PRESSURE_WARNING`. |
| **GATE-6.3** | Replay Ratio Scaling | `test_replay_ratio_scaling_under_pressure` | Scales down replay retention ratio to 0.05 under critical resource pressure. |
| **GATE-6.4** | Step Execution Profiling | `test_profiler_measure_step` | Measures latency and memory delta; updates EMA tracking. |
| **GATE-6.5** | Predictive Breach Alert | `test_predictive_breach_detection` | Detects projected breach when EMA approaches target ceiling within safety margin. |
| **GATE-6.6** | Hardware Capability Detection | `test_detect_hardware_profile` | Detects host platform, CPU core count, and recommended backend without crashing. |
| **GATE-6.7** | Atomic Checkpointing | `test_checkpoint_save_and_restore` | Saves and restores state dict with exact matching values. |
| **GATE-6.8** | Corruption Rollback | `test_corruption_rollback_to_prior_checkpoint` | Safely catches corrupted/truncated JSON and rolls back to prior intact checkpoint. |
