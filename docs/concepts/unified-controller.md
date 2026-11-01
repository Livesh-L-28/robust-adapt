# Concept: Unified Learning Controller (ULC)

The **Unified Learning Controller (ULC)** is an optional coordination layer that resolves conflicts between drift adaptation, noise filtering, and resource constraints.

---

## The Fundamental Conflict: Drift vs. Noise

When prediction error spikes in a streaming environment, two opposing hypotheses exist:
1. **Hypothesis 1 (Concept Drift)**: The distribution changed. The model must adapt rapidly or discard old weights.
2. **Hypothesis 2 (Noise Burst)**: A transient burst of corrupted labels occurred. The model must freeze updates or filter samples.

Executing drift adaptation during a noise burst causes catastrophic forgetting: the model learns incorrect labels and wipes valid historical knowledge. Conversely, executing noise filtering during genuine drift causes adaptation failure: the model stubbornly ignores new concepts.

---

## The ULC Dual-Evidence Arbitration Automaton

The `ArbitrationAutomaton` evaluates a 4-dimensional normalized evidence vector $E_t = [e_{\text{entropy}}, e_{\text{trend}}, e_{\text{density}}, e_{\text{mem}}]$:
- **Predictive Entropy ($e_{\text{entropy}}$)**: High entropy across inputs suggests genuine structural uncertainty (concept drift).
- **Loss Trend ($e_{\text{trend}}$)**: A sustained elevation indicates drift; an isolated spike indicates label noise.

### 5-State Operational Model
```
            +-------------------+
            |    STATIONARY     |
            +---------+---------+
                      |
           Prediction Error Spike
                      v
            +-------------------+
            |     WARNING       | <---+  (Hysteresis deadband)
            +---------+---------+     |
                      |               |
          Evidence Arbitration        |
         /                     \      |
        v                       v     |
+---------------+       +---------------+
|     DRIFT     |       |  NOISE BURST  |
+---------------+       +---------------+
```

1. **STATIONARY**: Standard incremental learning and gradient updates.
2. **WARNING**: Elevated error rate; initiates evaluation window with hysteresis deadband $\Delta_{\text{hyst}} = 0.15$.
3. **DRIFT**: Genuine concept drift confirmed. Triggers adaptation directives (`TRIGGER_DRIFT_ADAPTATION`, adjust tree split parameters).
4. **NOISE_BURST**: Corrupted burst detected. Directs RLA pipeline to filter samples (`DISCARD_CORRUPTED_SAMPLE`) and suppress ADWIN drift triggers.
5. **RECOVERY**: Controlled cooldown period preventing oscillatory re-triggers.
