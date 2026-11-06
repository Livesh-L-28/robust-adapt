# Unified Learning Controller (ULC) — Evolution Register v2.0

**Document Identifier:** `DOC-STRAT-EVO-ULC-001`<br>
**Working Codename:** AdaptiveML (*Provisional — Subject to formal legal clearance*)<br>
**Distribution Identifier:** `aml-core`<br>
**Target Module:** [`adaptive_ml.ulc`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc)<br>
**Parent Roadmap:** [Evolution Roadmap v2.0](file:///c:/projects/AdaptiveML/docs/strategy/ADAPTIVEML_EVOLUTION_ROADMAP_V2.md)<br>
**Status:** Approved Strategic Architecture<br>

---

## 1. Pillar Mission & Architectural Scope

The **Unified Learning Controller (ULC)** is an **optional dynamic coordination layer** that arbitrates between the independent capabilities of ALA, RLA, and RAO during complex, non-stationary data stream processing.

In strict compliance with **Product Specification Section 3.4 and Functional Requirement FR-ULC-001**, the ULC is an **optional orchestrator**. ALA, RLA, and RAO must remain 100% decoupled and independently usable in standalone workflows without importing or configuring the ULC. The ULC resolves the fundamental dilemma between **concept drift adaptation** (which requires accelerating plasticity) and **noise burst suppression** (which requires dampening updates to prevent corruption).

---

## 2. Baseline Capabilities Grounded in Verified Source Evidence

The verified implementation of ULC in `aml-core==0.1.0.dev0` comprises four core modules in [`adaptive_ml/ulc`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc):

```
adaptive_ml/ulc/
├── __init__.py           # Exports ControllerState, ControllerDirective, EvidenceVector,
│                         # EvidenceSynthesizer, ArbitrationAutomaton, AdaptiveLearningController
├── directives.py         # ControllerDirective, ControllerState (Enumerations and immutable directives)
├── evidence.py           # EvidenceSynthesizer, EvidenceVector (Dual-evidence metric accumulation)
├── automaton.py          # ArbitrationAutomaton (Hysteresis-governed finite state machine)
└── controller.py         # AdaptiveLearningController (Main orchestrator dispatching directives)
```

### 2.1 Verified Capabilities Inventory

| Component | Source File & Class | Mathematical Formulation / Implementation | Verified Invariants |
| :--- | :--- | :--- | :--- |
| **Evidence Synthesis** | [`EvidenceSynthesizer`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/evidence.py#L22) in [`evidence.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/evidence.py) | Synthesizes stream signals into immutable [`EvidenceVector`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/evidence.py#L14): $E_t = \langle \Delta_{\text{drift}}, \bar{r}_{\text{noise}}, M_{\text{util}}, \nabla_{\text{norm}} \rangle$ | Zero-division guarded; values strictly normalized to $[0, 1]$; thread-safe metric logging |
| **Arbitration Automaton** | [`ArbitrationAutomaton`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/automaton.py#L24) in [`automaton.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/automaton.py) | Discrete finite state machine operating across states: `NORMAL`, `DRIFT_DETECTED`, `HIGH_NOISE`, `RESOURCE_PRESSURE`, `RECOVERY` | Hysteresis band $\delta_{\text{hyst}}$ prevents state chatter; recovery step counter guarantees stability |
| **Controller Directives** | [`ControllerDirective`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/directives.py#L25) in [`directives.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/directives.py) | Generates actionable parameter directives: learning rate multiplier $\gamma_{\text{lr}}$, replay ratio $\gamma_{\text{replay}}$, noise threshold $\tau_{\text{noise}}$, and memory budget mode | Directives are pure data objects; decoupled from underlying estimator internals |
| **Coordinated Controller** | [`AdaptiveLearningController`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py#L30) in [`controller.py`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py) | Dispatches directives to registered components implementing [`EstimatorProtocol`](file:///c:/projects/AdaptiveML/adaptive_ml/core/types.py) and [`StatefulProtocol`](file:///c:/projects/AdaptiveML/adaptive_ml/core/types.py) | Transparent execution pass-through; component failure does not crash pipeline |

---

## 3. Current Limitations

Based on Phase 11 integration testing and Phase 12 benchmarks:

1. **Discrete State Transitions:** The current [`ArbitrationAutomaton`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/automaton.py) operates on sharp discrete state transitions. In real-world environments where gradual concept drift and fluctuating label noise co-occur simultaneously, a binary state choice (`DRIFT_DETECTED` vs `HIGH_NOISE`) forces sub-optimal compromise.
2. **Static Hysteresis Thresholds:** Parameters such as [`DEFAULT_TAU_R`](file:///c:/projects/AdaptiveML/adaptive_ml/core/constants.py) ($0.65$) and [`DEFAULT_DELTA_HYST`](file:///c:/projects/AdaptiveML/adaptive_ml/core/constants.py) ($0.10$) are statically configured, requiring empirical calibration for disparate domain distributions.
3. **Single-Pipeline Topology:** The controller is designed to arbitrate a single estimator pipeline operating on a single data stream. It cannot dynamically allocate shared memory or adjust learning rates across multiple concurrent streaming tasks.
4. **Heuristic Directive Scaling:** Learning rate and replay ratio adjustments are currently derived from pre-programmed step functions rather than continuous gradient-based or probabilistic policy optimization.

---

## 4. ULC Evolution Itemized Register

| Identifier | Priority | Classification | Original Phase Mapping | Complexity | Risk | Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EVO-ULC-001** | **P1** | Proposed Enhancement | Phase 11 (ULC Development) | Medium | Low | [`adaptive_ml.ulc.directives`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/directives.py) |
| **EVO-ULC-002** | **P1** | New Research | Phase 11 & Phase 12 | High | Medium | Phase 12 Benchmarks |
| **EVO-ULC-003** | **P2** | Proposed Enhancement | Phase 11 (ULC Development) | Medium | Low | [`adaptive_ml.ulc.evidence`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/evidence.py) |
| **EVO-ULC-004** | **P2** | New Engineering | Phase 11 & Phase 14 | Medium | Low | Telemetry Architecture |
| **EVO-ULC-005** | **P3** | New Research | Phase 11 & Phase 21 | High | High | Mathematical Design |
| **EVO-ULC-006** | **P4** | Deferred Opportunity | Phase 21 (Continuous R&D) | Very High | High | Distributed Scheduling |

---

### Detailed Specification of Evolution Items

#### EVO-ULC-001: Continuous Probabilistic Belief State Arbitration
- **Classification:** Proposed Enhancement
- **Priority:** P1
- **Phase Mapping:** Phase 11 (ULC Development)
- **Problem Statement:** Discrete state switching creates discontinuous step updates when noise and drift signals fluctuate near threshold boundaries.
- **Mathematical Design Requirements:** Replace discrete automaton states with a continuous Bayesian belief state vector $\vec{b}_t \in \Delta^3$:
  $$\vec{b}_t = [P(\text{Drift}_t), P(\text{Noise}_t), P(\text{Stationary}_t)]^T, \quad \sum b_{t, k} = 1$$
  and interpolate directives continuously:
  $$\gamma_{\text{lr}}(t) = b_{t, \text{drift}} \cdot \gamma_{\max} + b_{t, \text{noise}} \cdot \gamma_{\min} + b_{t, \text{stat}} \cdot 1.0$$
- **Implementation Dependencies:** [`adaptive_ml.ulc.evidence`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/evidence.py), [`adaptive_ml.ulc.directives`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/directives.py).
- **Validation Requirements:** Compare test error variance on synthetic continuous drift + noise benchmarks against discrete automaton.
- **Acceptance Criteria:** Reduces step prediction variance by $\ge 40\%$; eliminates abrupt directive oscillations without increasing computational latency by $>0.1\text{ ms/step}$.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ULC-002: Dual-Evidence Drift vs Noise Disentanglement Hypothesis
- **Classification:** New Research
- **Priority:** P1
- **Phase Mapping:** Phase 11 (ULC Development) & Phase 12 (Benchmarking)
- **Problem Statement:** When error rate surges in a stream, naive detectors cannot distinguish whether the cause is genuine concept drift (requiring model plasticity) or a transient noise burst (requiring sample rejection).
- **Research Hypothesis:** By computing the spatial consistency of prediction errors—specifically, comparing the variance of prediction residuals in local feature neighborhoods against global error variance:
  $$\Lambda(t) = \frac{\text{Var}_{\text{local}}(e_t)}{\text{Var}_{\text{global}}(e_t)}$$
  the controller can statistically disentangle concept drift ($\Lambda \ll 1$, errors cluster spatially) from uniform label noise ($\Lambda \approx 1$, errors distribute uniformly).
- **Relevant Prior Art:**
  - Ditzler et al. (2015): *Learning under Concept Drift: An Overview* (IEEE CIM).
  - Lipton et al. (2018): *Detecting and Correcting for Label Shift with Black Box Predictors* (ICML).
  - Bifet & Gavaldà (2007): *Learning from Time-Changing Data with Adaptive Windowing*.
- **Validation Requirements:** Synthetic benchmarks with interleaved sudden drift events and high-noise bursts ($40\%$).
- **Acceptance Criteria:** Correct attribution accuracy $\ge 90\%$ within $150$ samples of event onset; prevents model parameter corruption during noise bursts.
- **Estimated Complexity:** High.
- **Risk:** Medium (spatial variance estimation complexity in high-dimensional feature spaces).

---

#### EVO-ULC-003: Explainable Intervention Auditing and Attribution Reporting
- **Classification:** Proposed Enhancement
- **Priority:** P2
- **Phase Mapping:** Phase 11 (ULC Development)
- **Problem Statement:** In regulated industries (e.g., finance, healthcare), automated changes to learning rates, sample weights, or memory allocations must be interpretable and auditable by compliance officers.
- **Mathematical Design Requirements:** Implement an immutable audit log recording:
  $$\mathcal{R}_t = \left\{ t, \vec{b}_t, \text{triggering\_signal}, \text{applied\_directive}, \Delta\text{loss}_{\text{expected}} \right\}$$
  with programmatic export to JSON / Markdown summary tables.
- **Implementation Dependencies:** [`adaptive_ml.ulc.controller`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py).
- **Validation Requirements:** Verify zero overhead when logging is disabled; audit log schema validation in CI.
- **Acceptance Criteria:** Human-readable intervention explanation generated via `controller.explain_last_decision()`; zero memory leak over $10^6$ steps with ring-buffer storage.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ULC-004: Multi-Tenant Resource Arbitration across Concurrent Pipelines
- **Classification:** New Engineering
- **Priority:** P2
- **Phase Mapping:** Phase 11 & Phase 14 (Production Engineering)
- **Problem Statement:** When multiple streaming models run on a single host (e.g., 20 models for different sensor types), uncoordinated memory allocations can collectively breach physical RAM, triggering OS OOM killers.
- **Mathematical Design Requirements:** Implement a global coordinator that collects memory pressure signals across all registered ULC instances and solves a budget allocation linear program:
  $$\max \sum_{m=1}^M w_m \cdot \text{capacity}_m \quad \text{subject to} \quad \sum_{m=1}^M \text{RSS}_m \le \text{Budget}_{\max}$$
- **Implementation Dependencies:** [`adaptive_ml.rao.memory`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/memory.py), [`adaptive_ml.ulc.controller`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/controller.py).
- **Validation Requirements:** Stress test with 10 concurrent streaming pipelines on an 8 GB RAM container.
- **Acceptance Criteria:** Zero OOM events under 95% memory saturation; dynamic eviction of low-priority buffers to maintain system headroom.
- **Estimated Complexity:** Medium.
- **Risk:** Low.

---

#### EVO-ULC-005: Contextual Bandit for Self-Tuning Directive Policy
- **Classification:** New Research
- **Priority:** P3
- **Phase Mapping:** Phase 11 & Phase 21 (Continuous R&D)
- **Problem Statement:** Pre-configured heuristic scaling constants ($\gamma_{\text{lr}} \in [0.1, 2.0]$) fail to achieve optimal convergence rates across widely varying data dynamics.
- **Research Hypothesis:** Formulating directive selection as an online contextual bandit (using LinUCB with context vector $\vec{c}_t = \vec{b}_t$) optimizes downstream predictive loss reward:
  $$r_t = - \mathcal{L}_{t+1}(x_{t+1}, y_{t+1})$$
  achieving sublinear regret without manual hyperparameter search.
- **Relevant Prior Art:**
  - Li et al. (2010): *A Contextual-Bandit Approach to Personalized News Article Recommendation* (WWW).
  - Auer et al. (2002): *Finite-time Analysis of the Multiarmed Bandit Problem* (Machine Learning).
- **Validation Requirements:** Benchmarking across 5 diverse streaming datasets against fixed-heuristic ULC.
- **Acceptance Criteria:** Cumulative streaming test log-loss reduced by $\ge 8\%$ compared to static heuristic controller.
- **Estimated Complexity:** High.
- **Risk:** High (bandit exploration steps inducing instability during critical drift regimes).

---

#### EVO-ULC-006: Distributed Consensus Controller for Edge Mesh Networks
- **Classification:** Deferred Opportunity
- **Priority:** P4
- **Phase Mapping:** Phase 21 (Continuous R&D)
- **Problem Statement:** In edge IoT meshes, sensor nodes must reach decentralized consensus on drift onset without central coordinator servers.
- **Proposed Exploration:** Investigate gossip-based drift consensus protocols across local ULC instances using lightweight UDP message exchange.
- **Acceptance Criteria:** Decentralized drift consensus reached across 16 nodes within $2\text{ seconds}$ with $\le 1\text{ KB/s}$ bandwidth.
- **Estimated Complexity:** Very High.
- **Risk:** High (network partition tolerance and distributed consensus overhead).
