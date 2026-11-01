# AdaptiveML — Phase 5: ULC Research Gap Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-005`  
> **Focus Pillar**: Pillar 4 — ULC (Unified Learning Controller)

---

## 1. Candidate Research Gaps in ULC

```
+-------------------------------------------------------------------------------------------------------+
|                                    ULC RESEARCH GAP INVENTORY                                         |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| Gap ID  | Candidate Gap Title               | Failure Mode       | Priority Rank    | Classification  |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| **ULC-G1**| Drift-Noise Retraining Collision  | Corrupted retrain  | **P0 (Critical)**| Algorithmic/Sys |
| **ULC-G2**| Emerging Concept Preservation     | Prunes new classes | **P1 (High)**    | Algorithmic     |
| **ULC-G3**| Resource-Gated Plasticity Buffer  | RAM exhaustion     | **P2 (Medium)**  | Systems         |
| **ULC-G4**| Explainable Controller Telemetry  | Black-box decisions| **P2 (Medium)**  | Systems / DX    |
+---------+-----------------------------------+--------------------+------------------+-----------------+
```

---

## 2. In-Depth Analysis: GAP ULC-G1 (The Drift-Noise Collision)

### 2.1 The Inherent Conflict
In production data streams:
- Concept drift requires **increasing model plasticity** (updating weights, flushing old memory buffers).
- Label noise requires **decreasing model plasticity** (downweighting corrupted samples, relying on historical calibrated memory).

When concept drift and label noise co-occur:
1. An uncoordinated drift detector (ADWIN) interprets the error rate spike from the noise burst as a concept drift event.
2. It triggers a model reset.
3. The model trains aggressively on the corrupted data batch.
4. **Catastrophe**: The model memorizes corrupted labels and destroys its historical decision boundary.

### 2.2 Target Algorithmic Gap: The Dual-Evidence Arbitration Automaton
Formulating an in-loop state machine that mathematically conditions drift adaptation on local sample reliability:
$$\text{Action} = \mathcal{F}\left( \text{Drift Alert}_{\text{ALA}}, \; \mathbb{E}[\text{Reliability}]_{\text{RLA}}, \; \mathcal{M}_{\text{RAM}} \right)$$
- If **Drift Alert = True** AND **Mean Reliability < $\tau_{\text{noise}}$**:
  $\implies$ **Assert False Alarm / Noise Burst**. Suppress drift reset, attenuate gradient learning rate, preserve historical memory buffer.
- If **Drift Alert = True** AND **Mean Reliability $\ge \tau_{\text{noise}}$**:
  $\implies$ **Confirm Real Concept Drift**. Modulate learning rate, allocate replay buffer, update model weights.
