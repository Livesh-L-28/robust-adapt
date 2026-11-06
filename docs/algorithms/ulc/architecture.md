# ULC-v5: Architecture & Execution State

`UnifiedLearningControllerV5` encapsulates five core sub-components:

```
+-----------------------------------------------------------------------------------+
|                        UnifiedLearningControllerV5                                 |
+-----------------------------------------------------------------------------------+
|  1. classifier:    AdaptiveClassifier (Streaming Hoeffding Tree)                 |
|  2. adwin:         ReliabilityWeightedADWIN (Statistical Drift Detector)          |
|  3. replay:        ClassBalancedReservoirReplay (Bounded Experience Buffer)       |
|  4. fingerprinter: ConceptFingerprinter (Statistical Batch Feature Profiler)      |
|  5. memory:        RecurringConceptMemory (Historical Snapshot Repository)        |
+-----------------------------------------------------------------------------------+
```

---

## 1. Prequential Step Lifecycle

When `controller.step(X_b, y_b)` is invoked:

```
[ Incoming Micro-batch (X_b, y_b) ]
                 |
                 v
1. Prequential Evaluation (Predict -> Compute Error Vector)
                 |
                 v
2. Statistical Drift Check (ADWIN Update)
                 |
                 +---- No Drift / In Cooldown ----> [ TIER 0: NOOP (Incremental Update) ]
                 |
                 +---- Drift Statistically Detected
                                 |
                                 v
3. Concept Fingerprinting & Historical Memory Query
   - Compute candidate centroid & variance: FP_candidate
   - Query RecurringConceptMemory -> (match_snapshot, similarity)
                                 |
                                 v
4. Expected Utility Scoring (UtilityScorer)
   - u_restore: Utility of restoring historical concept
   - u_soft_reset: Utility of resetting tree & seeding from replay
   - u_damping: Utility of attenuating sample weights
   - u_hard_reset: Utility of catastrophic reset
                                 |
                                 v
5. Execute Highest-Utility Intervention
   - Apply directive to classifier, replay buffer, and cooldown timer
                                 |
                                 v
6. Model Weight Update & Telemetry Emission
   - Partial fit on batch using directive's sample weight scale
   - Return (ULCv5Directive, telemetry_dict)
```

---

## 2. Complete State Dict Roundtrip

`UnifiedLearningControllerV5` supports full serialization and restoration via standard `state_dict()` and `load_state_dict()` methods, allowing continuous streaming pipelines to be paused, checkpointed, and resumed seamlessly.
