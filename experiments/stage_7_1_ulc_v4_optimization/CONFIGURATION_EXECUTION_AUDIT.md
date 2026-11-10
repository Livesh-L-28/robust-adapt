# Workstream A: Configuration Execution Audit
## Forensic Analysis of Identical Model Metrics & Component Activation

**Document Identifier:** `STAGE-7-1-A-002`  
**Distribution Package Identifier:** `aml-core`  
**Audit Target:** Benchmark implementations in [`run_stage7_experiment.py`](file:///c:/projects/AdaptiveML/experiments/stage_7_ulc_v4/run_stage7_experiment.py)  
**Status:** `AUDITED & ROOT CAUSES PROVEN`

---

## 1. Executive Summary

During the initial baseline verification, three pairs of model configurations yielded identical metrics across all 5 seeds:
1. `Standalone RLA (SCE + Margin)` vs `ALA + RLA` (71.75% Acc, 0.4734 F1, 18.36% MinRec).
2. `ULC-v2 Baseline` vs `ULC-v3 Audited` (73.73% Acc, 0.5582 F1, 50.29% MinRec).
3. `Standalone ADWIN (ALA 1.0)` vs `ALA + RAO` (90.00% Acc, 0.4737 F1, 0.00% MinRec, 10.0 FDR).

An independent forensic audit was conducted using deep step-level tracing on Seed 42 ([`SEED_42_DETAILED_TRACE.json`](file:///c:/projects/AdaptiveML/experiments/stage_7_1_ulc_v4_optimization/SEED_42_DETAILED_TRACE.json)). The audit confirmed that these identical metrics are **not** caused by cached data, shared mutable state, or copy-paste evaluation bugs, but rather by **specific architectural bypasses** in the benchmark logic.

---

## 2. Investigation of Identical Pair 1: Standalone RLA vs ALA + RLA

### Code Comparison
- **Standalone RLA (lines 238–254):**
  ```python
  probs = clf.predict_proba(X_b)
  logits_b = np.log(np.clip(probs, 1e-12, 1.0))
  w = scorer.score_samples(X_b, logits_b, y_obs)
  clf.partial_fit(X_b, y_obs, sample_weight=w)
  ```
- **ALA + RLA (lines 286–310):**
  ```python
  probs = clf.predict_proba(X_b)
  logits_b = np.log(np.clip(probs, 1e-12, 1.0))
  w = scorer.score_samples(X_b, logits_b, y_obs)
  mean_w = float(np.mean(w))
  if delta >= 1.0 and mean_w >= 0.70:
      clf.reset()
      clf.fit(X_b, y_obs, sample_weight=w)
  else:
      clf.partial_fit(X_b, y_obs, sample_weight=w)
  ```

### Forensic Finding
In `ALA + RLA`, drift reset is gated by `delta >= 1.0 and mean_w >= 0.70`:
1. *Regime 2 (Noise Burst):* `delta = 1.25 >= 1.0`, but because 40% of labels are corrupt, `mean_w` drops to \(\sim 0.525 < 0.70\). The condition is FALSE, correctly suppressing false reset.
2. *Regime 4 (Abrupt Inverted Drift):* `delta = 1.40 >= 1.0`. However, because the incoming batch has inverted class centroids, the unadapted classifier predicts with high error. Consequently, the logit margins \(M_i = z_{y_i} - \max_{j \ne y_i} z_j\) are strongly negative (\(M_i < -5.0\)), driving `mean_w` to **0.050**.
3. Because \(0.050 < 0.70\), the reset guard `mean_w >= 0.70` is **NEVER SATISFIED** during true drift!
4. Therefore, `clf.reset()` is never executed. Both `Standalone RLA` and `ALA + RLA` execute `clf.partial_fit(X_b, y_obs, sample_weight=w)` on every single batch.
5. **Conclusion:** Identical results are an inevitable mathematical consequence of conditioning drift adaptation on unadapted model margin reliability.

---

## 3. Investigation of Identical Pair 2: ULC-v2 vs ULC-v3

### Code Comparison
- **ULC-v2 Baseline (lines 375–401):**
  ```python
  directive, _ = controller.step(...)
  if directive.state == ControllerState.CONFIRMED_DRIFT:
      clf.purge_replay(policy="partial")
      opt.reset_momenta()
  elif directive.state == ControllerState.NOISE_BURST:
      pass
  else:
      clf.partial_fit(X_b, y_obs)
  ```
- **ULC-v3 Audited (lines 402–426):**
  ```python
  directive, _ = controller.step(...)
  if directive.state == ControllerState.CONFIRMED_DRIFT:
      clf.purge_replay(policy="selective", keep_minority=True)
      opt.reset_momenta()
  elif directive.state != ControllerState.NOISE_BURST:
      clf.partial_fit(X_b, y_obs)
  ```

### Forensic Finding
The step-level trace reveals the operational states emitted by `controller.step(...)` throughout the entire 60 batches:
$$\text{Observed States} = \{\text{STABLE}, \text{NOISE\_BURST}\}$$
1. `directive.state == ControllerState.CONFIRMED_DRIFT` was **never emitted** by `AdaptiveLearningController`.
2. Why? Because during true drift (Batches 36, 37), `delta >= 1.0`, but `rel < 0.65`. In the legacy automaton:
   ```python
   if delta >= 1.0:
       if rel >= tau_r:
           next_state = CONFIRMED_DRIFT
       else:
           next_state = NOISE_BURST
   ```
3. Since `rel = 0.05 < 0.65`, the legacy automaton transitioned to `NOISE_BURST` instead of `CONFIRMED_DRIFT`.
4. Because `CONFIRMED_DRIFT` was never emitted, the difference between ULC-v2 (`policy="partial"`) and ULC-v3 (`policy="selective", keep_minority=True`) was **never exercised**.
5. Both controllers entered `NOISE_BURST` on Batches 16–25 and Batches 36–45, and executed `clf.partial_fit(X_b, y_obs)` on all other batches.
6. **Conclusion:** ULC-v2 and ULC-v3 produced identical outputs because the legacy automaton never transitioned into the state where their implementations diverge.

---

## 4. Investigation of Identical Pair 3: Standalone ADWIN vs ALA + RAO

### Code Comparison
- In both models, `if delta >= 1.0: clf.reset(); clf.fit(X_b, y_obs)`.
- In `ALA + RAO`, `opt.reset_momenta()` is also called on the `LinearSurrogate`.
- However, predictions in both models were evaluated via `clf.predict(X_b)`:
  ```python
  preds = clf.predict(X_b)
  all_y_clean.extend(y_clean)
  all_y_pred.extend(preds)
  ```
- Because predictions were generated exclusively by `clf` and not the surrogate model, the surrogate optimizer updates in `ALA + RAO` had zero influence on the measured predictions.
- **Conclusion:** Identical metrics occurred because the benchmark measured the Hoeffding tree classifier in both configurations.

