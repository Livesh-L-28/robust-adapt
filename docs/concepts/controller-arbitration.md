# Unified Controller Arbitration (ULC)

In multi-pillar streaming systems, individual components operating in isolation often trigger catastrophic operational conflicts:

```
[ ALA: Rapid Adaptation ] <---- CONFLICT ----> [ RLA: Noise Insulation ]
"Tree detects drift, attempts reset"            "Downweights samples as corrupt noise"
```

If RLA filters out genuine drift instances as "noise", ALA never adapts. Conversely, if ALA treats random noise bursts as "drift", the model resets repeatedly, destroying historical memory.

---

## 1. Expected Utility Optimization

The **Unified Learning Controller V5 (ULC-v5)** formalizes all adaptation interventions as a constrained expected utility optimization problem:

$$U(\text{Action}) = \left(\text{Confidence} \times \text{Expected Benefit}\right) - \text{Operational Cost}$$

- **Operational Cost**: Resetting a model incurs high cost (temporary accuracy drop while learning from scratch). Incremental updates incur zero cost.
- **Expected Benefit**: Measured as a function of statistical drift magnitude $\Delta_{\text{drift}}$ and recurring concept similarity $\text{sim}$.
- **Evidence Confidence**: Derived from multi-pillar consensus (ADWIN variance ratio, neighborhood agreement, margin distribution).

---

## 2. Five-Tier Intervention Hierarchy

Instead of binary adaptation (do nothing vs. wipe model), ULC-v5 chooses the lowest-impact intervention justified by the utility score:

```
+-------------------------------------------------------------------------+
| Tier 0: NOOP (Incremental Update)                                       |
| Cost: 0.00 | Action: Continue standard prequential streaming learning.   |
+-------------------------------------------------------------------------+
                                    |
                                    v (Mild elevation in error variance)
+-------------------------------------------------------------------------+
| Tier 1: PARAM_DAMPING                                                   |
| Cost: 0.05 | Action: Attenuate learning rates / sample weights (0.80x).  |
+-------------------------------------------------------------------------+
                                    |
                                    v (Statistical match with historical concept)
+-------------------------------------------------------------------------+
| Tier 2: CONCEPT_RESTORE                                                 |
| Cost: 0.15 | Action: Restore stored snapshot from memory; 0 retraining. |
+-------------------------------------------------------------------------+
                                    |
                                    v (Moderate novel concept drift)
+-------------------------------------------------------------------------+
| Tier 3: SOFT_REPLAY_RESET                                               |
| Cost: 0.25 | Action: Reset active tree; warm-start from reservoir.     |
+-------------------------------------------------------------------------+
                                    |
                                    v (Extreme unrecoverable divergence)
+-------------------------------------------------------------------------+
| Tier 4: HARD_RESET                                                      |
| Cost: 0.70 | Action: Emergency complete purge of tree, buffer, and state|
+-------------------------------------------------------------------------+
```

---

## 3. Anti-Thrashing via Exponential Cooldown Backoff

Under adversarial noise, controllers can enter an infinite reset loop ("thrashing"), causing catastrophic performance collapse.

ULC-v5 prevents this by enforcing dynamic lockout:
$$\text{Cooldown Lockout} = \text{base\_cooldown} \times \min(4, \text{consecutive\_interventions})$$
- When an intervention occurs, subsequent structural resets are locked out for the cooldown period.
- Repeated triggers increase the lockout window up to $4\times$.
- When the stream returns to steady state (Tier 0), consecutive intervention counters decay cleanly to zero.
