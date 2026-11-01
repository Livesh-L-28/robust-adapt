# AdaptiveML — ULC Algorithm Specification: Unified Learning Controller

> **Document Status**: Complete Baseline Deliverable (Phase 6)  
> **Document Identifier**: `DOC-DES-P6-006`  
> **Last Updated**: 2026-11-01  
> **Pillar**: ULC (Unified Learning Controller — Optional Holistic Coordinator)  
> **Target Downstream Deliverable**: `DOC-DES-P7-004` (Public API Specification), `DOC-DES-P6-009` (Pseudocode Catalog)

---

## 1. Executive Pillar Architecture

The **Unified Learning Controller (ULC)** is an **optional cross-pillar coordinator**. It addresses the classical cross-pillar dilemma in machine learning:
> *When model error increases, is it caused by concept drift (which mandates model adaptation and resetting obsolete statistics), or by a burst of noisy labels (which mandates discarding corrupted samples and preserving the existing model)?*

Operating in isolation:
- An adaptive drift detector resets the model upon encountering noisy bursts, inducing catastrophic forgetting.
- A robust sample filter purges genuine new-concept instances as outliers, blinding the model to real distributional change.

The ULC resolves this dilemma via a mathematically formal **Dual-Evidence In-Loop Arbitration Automaton**.

```
                         ULC ARBITRATION ARCHITECTURE
                                      │
                   Incoming Mini-Batch (X_tau, y_tau)
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
    ┌───────────────────────────┐             ┌───────────────────────────┐
    │     ALA Evidence Input    │             │     RLA Evidence Input    │
    │  Delta_drift = |mu0-mu1|  │             │   Mean Sample Reliability │
    │     ADWIN Window Cut      │             │        R_bar_W in [0,1]   │
    └────────────┬──────────────┘             └─────────────┬─────────────┘
                 └────────────────────┬────────────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │    Dual-Evidence Synthesizer  │
                      │  Evidence Vector e_tau in R^4 │
                      └───────────────┬───────────────┘
                                      ▼
                      ┌───────────────────────────────┐
                      │   Finite State Automaton (S)  │
                      │   Transition Kernel Gamma     │
                      └───────────────┬───────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   [State S0: STABLE]        [State S2: DRIFT]           [State S3: NOISE]
   Standard Streaming        - Boost Learning Rate       - Suppress Reset
   Steady-State Update       - Invalidate Buffer         - Down-Weight Samples
                             - Trigger Tree Split        - Freeze Buffer
```

---

## 2. Mathematical Formalization of the Evidence Vector

At mini-batch step $\tau$, the controller constructs an evidence vector $\mathbf{e}_\tau \in [0, 1]^4$:
$$\mathbf{e}_\tau = \begin{bmatrix} \Delta_{\text{drift}}(\tau) \\ \bar{R}_{\mathcal{W}}(\tau) \\ \mathcal{H}_{\text{pred}}(\tau) \\ \mathcal{T}_{\text{loss}}(\tau) \end{bmatrix}$$

### 2.1 Component 1: Normalized Drift Divergence ($\Delta_{\text{drift}}$)
From the ALA pillar's RW-ADWIN sub-window partition $W = W_0 \cdot W_1$:
$$\Delta_{\text{drift}}(\tau) = \min\left( \frac{\left| \hat{\mu}_{W_0}^{(r)} - \hat{\mu}_{W_1}^{(r)} \right|}{\epsilon_{\text{cut}}^{(r)} + \epsilon_{\text{div}}}, \; 2.0 \right) \cdot \frac{1}{2.0} \in [0, 1]$$
- $\Delta_{\text{drift}} < 0.5$: Normal fluctuation.
- $0.5 \le \Delta_{\text{drift}} < 1.0$: Warning range (suspected shift).
- $\Delta_{\text{drift}} \ge 1.0$: Statistical drift boundary violated.

### 2.2 Component 2: Mean Window Sample Reliability ($\bar{R}_{\mathcal{W}}$)
From the RLA pillar's `DensityAwareMarginScorer`:
$$\bar{R}_{\mathcal{W}}(\tau) = \frac{1}{|W_1|} \sum_{i \in W_1} r_i \in [0, 1]$$
- High $\bar{R}_{\mathcal{W}} \approx 1.0$: Incoming samples are clean and lie coherently within local density clusters.
- Low $\bar{R}_{\mathcal{W}} \approx 0.0$: Incoming samples exhibit conflicting labels and negative margins in high-density regions (systematic corruption).

### 2.3 Component 3: Normalized Predictive Entropy ($\mathcal{H}_{\text{pred}}$)
For model predictions $\hat{\mathbf{p}}_i \in \Delta^{C-1}$:
$$\mathcal{H}_{\text{pred}}(\tau) = \frac{1}{B \cdot \ln(C)} \sum_{i=1}^B \left( -\sum_{c=0}^{C-1} \hat{p}_{ic} \ln(\hat{p}_{ic} + \epsilon_{\text{div}}) \right) \in [0, 1]$$
- Under real drift, predictive entropy surges as new features cross old boundaries.
- Under label noise alone, feature clusters remain concentrated while only labels flip.

### 2.4 Component 4: Directional Loss Trend ($\mathcal{T}_{\text{loss}}$)
Computed via exponential moving average slope over a short window $K_{\text{trend}}$:
$$\mathcal{T}_{\text{loss}}(\tau) = \sigma\left( \kappa_{\text{slope}} \cdot \frac{d \mathcal{L}}{d\tau} \right) \in [0, 1]$$

---

## 3. Finite State Automaton Formalization

### 3.1 State Space $\mathcal{S}$

The controller state space consists of five discrete operational modes:
$$\mathcal{S} = \{ S_0: \text{STABLE}, \; S_1: \text{WARNING}, \; S_2: \text{CONFIRMED\_DRIFT}, \; S_3: \text{NOISE\_BURST}, \; S_4: \text{RECOVERY} \}$$

### 3.2 State Transition Kernel $\Gamma: \mathcal{S} \times [0, 1]^4 \to \mathcal{S}$

Let $c_{\text{dwell}}$ be an integer dwell counter enforcing hysteresis. The deterministic transition rules are:

#### 3.2.1 From $S_0$ (STABLE):
$$\Gamma(S_0, \mathbf{e}_\tau) = \begin{cases} 
S_2 (\text{CONFIRMED\_DRIFT}), & \text{if } \Delta_{\text{drift}} \ge 1.0 \land \bar{R}_{\mathcal{W}} \ge \tau_R \\
S_3 (\text{NOISE\_BURST}), & \text{if } \Delta_{\text{drift}} \ge 1.0 \land \bar{R}_{\mathcal{W}} < \tau_R \\
S_1 (\text{WARNING}), & \text{if } \Delta_{\text{drift}} \ge 0.5 \land \Delta_{\text{drift}} < 1.0 \\
S_0 (\text{STABLE}), & \text{otherwise}
\end{cases}$$
where $\tau_R \in [0.6, 0.75]$ is the reliability arbitration threshold (default $\tau_R = 0.65$).

#### 3.2.2 From $S_1$ (WARNING):
$$\Gamma(S_1, \mathbf{e}_\tau) = \begin{cases}
S_2 (\text{CONFIRMED\_DRIFT}), & \text{if } \Delta_{\text{drift}} \ge 1.0 \land \bar{R}_{\mathcal{W}} \ge \tau_R \\
S_3 (\text{NOISE\_BURST}), & \text{if } \Delta_{\text{drift}} \ge 1.0 \land \bar{R}_{\mathcal{W}} < \tau_R \\
S_0 (\text{STABLE}), & \text{if } \Delta_{\text{drift}} < 0.35 \quad \text{(resolved false alarm)} \\
S_1 (\text{WARNING}), & \text{otherwise}
\end{cases}$$

#### 3.2.3 From $S_2$ (CONFIRMED\_DRIFT):
Upon entering $S_2$, a drift adaptation directive is broadcast across all pillars:
- Controller sets dwell counter $c_{\text{dwell}} \leftarrow K_{\text{recovery}}$.
- Transition: $\Gamma(S_2, \cdot) = S_4 (\text{RECOVERY})$.

#### 3.2.4 From $S_3$ (NOISE\_BURST):
$$\Gamma(S_3, \mathbf{e}_\tau) = \begin{cases}
S_0 (\text{STABLE}), & \text{if } \bar{R}_{\mathcal{W}} \ge \tau_R \land \Delta_{\text{drift}} < 0.5 \\
S_3 (\text{NOISE\_BURST}), & \text{otherwise}
\end{cases}$$

#### 3.2.5 From $S_4$ (RECOVERY):
$$\Gamma(S_4, \mathbf{e}_\tau) = \begin{cases}
S_0 (\text{STABLE}), & \text{if } c_{\text{dwell}} \le 0 \land \Delta_{\text{drift}} < 0.5 \\
S_4 (\text{RECOVERY}), & \text{otherwise (decrement } c_{\text{dwell}} \leftarrow c_{\text{dwell}} - 1 \text{)}
\end{cases}$$

---

## 4. Cross-Pillar Coordination Directives

When transitioning states, the ULC issues typed control directives to each independent pillar:

| Controller State | ALA Directive | RLA Directive | RAO Directive |
| :--- | :--- | :--- | :--- |
| **$S_0$ (STABLE)** | Standard incremental updates; normal replay sampling | Standard reliability scoring; default loss formulation | Standard base learning rate $\eta_0$ |
| **$S_1$ (WARNING)** | Prepare background shadow model; preserve window | Increase $k$-NN density checking resolution | Keep optimizer state unchanged |
| **$S_2$ (CONFIRMED\_DRIFT)**| Replace active tree with shadow tree; prune obsolete replay buffer buckets | Reset running feature density statistics to current window | Temporarily scale learning rate: $\eta_t \leftarrow 2.5 \eta_0$; reset momentum $\mathbf{m}_t \leftarrow \mathbf{0}$ |
| **$S_3$ (NOISE\_BURST)** | **Suppress ADWIN cut**; freeze tree splitting; freeze replay buffer | Enforce hard filtering: drop samples with $r_i < \theta_{\text{filter}}$; use pure SCE loss | Clamp maximum gradient norm $\|\mathbf{g}\| \le G_{\text{clip}} / 2$ |
| **$S_4$ (RECOVERY)** | Accelerate leaf split checks ($n_{\min} \leftarrow n_{\min} / 2$) | Increase minority class density protection parameter $\gamma$ | Linearly anneal learning rate from $2.5 \eta_0$ down to $\eta_0$ over $K_{\text{recovery}}$ steps |

---

## 5. Mathematical Stability and Chattering Prevention

### 5.1 Hysteresis Dead-Band
To prevent rapid oscillations between $S_0$ and $S_1$ (chattering):
- Entry condition to $S_1$: $\Delta_{\text{drift}} \ge 0.50$.
- Exit condition back to $S_0$: $\Delta_{\text{drift}} \le 0.35$.
The dead-band width $\Delta_{\text{hyst}} = 0.15$ guarantees that small stochastic fluctuations in window error cannot trigger cyclic switching.

### 5.2 Minimum Dwell Time Bound
> **Theorem 4 (Finite Transition Non-Oscillation Guarantee)**:  
> By enforcing $c_{\text{dwell}} \ge K_{\text{recovery}} > 0$ upon entering $S_2$ or $S_4$, the maximum transition frequency between stable and adaptation states is strictly bounded by:
> $$f_{\text{transition}} \le \frac{1}{K_{\text{recovery}}} \quad \text{transitions per step}$$
> Under adversarial sequences of alternating corrupt labels and abrupt drifts, the controller maintains Lyapunov stability: cumulative regret over horizon $T$ is bounded by $\mathcal{O}(\sqrt{T} + N_{\text{drift}} \cdot K_{\text{recovery}})$.

---

## 6. Summary of Mathematical Guarantees

| Metric | Property | Derivation / Proof |
| :--- | :--- | :--- |
| **Computational Overhead** | $\mathcal{O}(1)$ scalar operations | Evaluates 4 scalars against static thresholds per mini-batch |
| **State Memory Footprint** | $< 128$ bytes | Stores integer state, dwell counter, and 4 scalar history buffers |
| **Drift-Noise Separability**| High | Separates real shift from label noise via dual evidence $(\Delta_{\text{drift}}, \bar{R}_{\mathcal{W}})$ |
| **Pillar Independence** | Strictly decoupled | Communicates solely through numerical directive structs |
