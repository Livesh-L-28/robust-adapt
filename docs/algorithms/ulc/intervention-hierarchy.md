# The Five-Tier Intervention Hierarchy

ULC-v5 categorizes all candidate interventions into five discrete tiers of escalating operational impact:

---

## Tier Summary Table

| Tier | Enum Identifier | Operational Cost | Operational Action Executed | When Triggered |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | `TIER_0_NOOP` | $0.00$ | Incremental `partial_fit` update; zero structural changes | Normal stationary stream or active cooldown |
| **Tier 1** | `TIER_1_PARAM_DAMPING` | $0.05$ | Scales sample weights to $0.80\times$; damps transient noise | Mild elevation in error rate without concept match |
| **Tier 2** | `TIER_2_CONCEPT_RESTORE` | $0.15$ | Restores stored model snapshot; updates concept metadata | Fingerprint matches historical concept ($\text{Sim} \ge \tau_{\text{sim}}$) |
| **Tier 3** | `TIER_3_SOFT_REPLAY_RESET`| $0.25$ | Reinitializes active tree; warm-starts from reservoir | Novel concept drift ($U_{\text{soft}} > U_{\text{damp}}$ and $\Delta > 0.40$) |
| **Tier 4** | `TIER_4_HARD_RESET` | $0.70$ | Complete emergency purge of tree, buffer, and state | Extreme catastrophic drift ($\ge 0.95$) with repeated resets |

---

## 1. Expected Utility Arbitration

Every candidate tier is scored by `UtilityScorer.score_action`:

$$U(\text{Tier}) = (\text{Confidence} \times \text{Benefit}) - \text{Cost}$$

- **`TIER_0_NOOP`**: Fixed baseline utility of $0.10$.
- **`TIER_1_PARAM_DAMPING`**: $\text{Benefit} = 0.35 \times \Delta_{\text{drift}}$.
- **`TIER_2_CONCEPT_RESTORE`**: $\text{Benefit} = 0.85$ (if recurrent) or $0.10$ (if novel).
- **`TIER_3_SOFT_REPLAY_RESET`**: $\text{Benefit} = 0.75 \times \Delta_{\text{drift}}$ (if novel) or $0.15$ (if recurrent).
- **`TIER_4_HARD_RESET`**: $\text{Benefit} = 0.90 \times \Delta_{\text{drift}}$.

The controller selects the tier that maximizes expected utility, ensuring structural resets are only executed when mathematically justified by the severity of the distribution shift.
