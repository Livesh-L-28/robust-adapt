# Controller Decision Engine Report

**Document ID:** `ULC-ENG-001`  
**Phase:** Phase 11 — Unified Learning Controller (ULC)  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.ulc.automaton`

---

## 1. Mathematical Formalization of Decision Boundaries

The transition kernel $\Gamma: \mathcal{S} \times [0, 1]^4 \to \mathcal{S}$ partitions the evidence space into distinct behavioral regions:

```
                  Evidence Space Partitioning (Delta_drift vs R_bar_W)
       R_bar_W
         ▲
     1.0 ┼───────────────────────┬───────────────────────────────┐
         │                       │                               │
         │     S0: STABLE        │      S2: CONFIRMED_DRIFT      │
         │  (Standard Updates)   │   (Adapt Model, Purge Buffer) │
         │                       │                               │
   tau_R ┼───────────────────────┼───────────────────────────────┤
         │                       │                               │
         │     S0: STABLE        │       S3: NOISE_BURST         │
         │  (Standard Updates)   │   (Suppress ADWIN, Filter)    │
         │                       │                               │
     0.0 ┴───────────────────────┴───────────────────────────────►
        0.0                     1.0                         2.0
                                                     Delta_drift
```

### 1.1 Arbitration Boundary
- When $\Delta_{\text{drift}} \ge 1.0$:
  - If $\bar{R}_{\mathcal{W}} \ge \tau_R \implies \text{CONFIRMED\_DRIFT}$. Incoming samples exhibit coherent feature clusters and legitimate labels; the model must adapt immediately.
  - If $\bar{R}_{\mathcal{W}} < \tau_R \implies \text{NOISE\_BURST}$. Incoming samples have severe label-feature inconsistencies; drift cut is suppressed to preserve model knowledge.

---

## 2. Hysteresis Dead-Band Dynamics

To eliminate rapid oscillation (limit cycle chattering) between $S_0$ (`STABLE`) and $S_1$ (`WARNING`) when $\Delta_{\text{drift}} \approx 0.5$:
- **Ascending Trigger**: Transition $S_0 \to S_1$ requires $\Delta_{\text{drift}} \ge 0.50$.
- **Descending Reset**: Transition $S_1 \to S_0$ requires $\Delta_{\text{drift}} < (0.50 - \Delta_{\text{hyst}}) = 0.35$.
- In the deadband $\Delta_{\text{drift}} \in [0.35, 0.50)$, the controller maintains its current state, preventing cyclic flipping.

---

## 3. Recovery Phase Annealing

Upon entering `CONFIRMED_DRIFT`, the controller initializes the dwell counter $c_{\text{dwell}} = K_{\text{recovery}}$ and transitions to `RECOVERY`:
- Learning rate scale factor is dynamically annealed:
  $$\eta_{\text{scale}}(t) = 1.0 + 1.5 \cdot \left(\frac{c_{\text{dwell}}}{K_{\text{recovery}}}\right)$$
- When $c_{\text{dwell}} = K_{\text{recovery}}$, $\eta_{\text{scale}} = 2.5$.
- As $c_{\text{dwell}} \to 0$, $\eta_{\text{scale}} \to 1.0$.
- Protects the model from overshooting newly adapted local optima.
