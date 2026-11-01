# AdaptiveML — Phase 5: RLA Research Gap Analysis

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-003`  
> **Focus Pillar**: Pillar 2 — RLA (Robust Learning Algorithms)

---

## 1. Candidate Research Gaps in RLA

```
+-------------------------------------------------------------------------------------------------------+
|                                    RLA RESEARCH GAP INVENTORY                                         |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| Gap ID  | Candidate Gap Title               | Failure Mode       | Priority Rank    | Classification  |
+---------+-----------------------------------+--------------------+------------------+-----------------+
| **RLA-G1**| Small-Loss Imbalance Breakdown    | Minority pruning   | **P0 (Critical)**| Algorithmic     |
| **RLA-G2**| Single-Pass In-Training Scoring   | Offline latency    | **P0 (Critical)**| Systems / Alg   |
| **RLA-G3**| Robust Loss Parameter Brittleness | Divergence on noise| **P1 (High)**    | Mathematical    |
| **RLA-G4**| Instance-Dependent Noise Modeling | Real-world failure | **P2 (Medium)**  | Theoretical     |
+---------+-----------------------------------+--------------------+------------------+-----------------+
```

---

## 2. In-Depth Analysis: GAP RLA-G1 (The Small-Loss Imbalance Breakdown)

### 2.1 The Underlying Structural Breakdown
Existing state-of-the-art sample selection algorithms (Cleanlab / Confident Learning, Co-teaching, MentorNet) rely on the foundational **Small-Loss Principle**:
$$\ell(x_i, y_i) < \tau \implies \text{Clean}; \quad \ell(x_i, y_i) \ge \tau \implies \text{Noisy}$$

In imbalanced or long-tailed distributions (where head classes have $10,000$ samples and tail classes have $50$ samples):
1. The model's representation for minority-class patterns is undertrained during early epochs.
2. Consequently, legitimate clean minority instances naturally produce **High Loss**.
3. Small-loss criteria treat these high-loss instances as "corrupt annotations" and prune them.
4. **Catastrophic Result**: Tail classes are starved of training data, causing minority recall to collapse.

### 2.2 Proposed Research Direction: Density-Aware Margin Scoring
To resolve this gap, sample reliability must be formulated as a function of **Prediction Margin $\mathcal{M}(x, y)$** and **Local Feature Density $\rho_k(x)$**:
$$\text{Reliability}(x_i, y_i) = \Phi\left( f_{y_i}(x_i) - \max_{j \ne y_i} f_j(x_i), \; \rho_k(x_i) \right)$$
- If a sample has high loss in a **high-density region**, it is an isolated outlier / noisy label $\implies$ **Downweight / Filter**.
- If a sample has high loss in a **low-density region**, it is a legitimate tail pattern $\implies$ **Preserve / Protect**.

---

## 3. In-Depth Analysis: GAP RLA-G2 (Single-Pass In-Training Scoring)

### 3.1 The Offline Cross-Validation Bottleneck
- Cleanlab requires running $K$-fold cross-validation to generate out-of-sample predicted probabilities prior to identifying label issues.
- In online learning or large-scale streaming, running multiple complete training passes is computationally impossible.
- **Target Gap**: Developing an **online running reliability accumulator** that estimates sample confidence dynamically within a single training pass using exponential moving averages of per-sample prediction margins.
