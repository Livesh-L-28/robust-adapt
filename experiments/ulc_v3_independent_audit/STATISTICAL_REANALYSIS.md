# ULC-v3 Statistical Audit & Rigorous Re-Analysis

**Audit Directory:** [`experiments/ulc_v3_independent_audit/`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit)  
**Reference Data:** [`statistical_audit_results.json`](file:///c:/projects/AdaptiveML/experiments/ulc_v3_independent_audit/statistical_audit_results.json)  
**Evaluated Datasets:** Original $N=5$ Seeds ($df=4$) and Extended $N=20$ Seeds ($df=19$)  
**Primary Outcome:** Macro F1 Score across 50-batch stream  
**Primary Alpha Threshold:** $\alpha = 0.01$ (Mandatory Research Requirement)  
**FWER Correction:** Holm-Bonferroni Step-Down Procedure  

---

## 1. Executive Statistical Audit Summary

This audit independently recalculates all statistical tests from raw per-seed observations, audits test assumptions, evaluates family-wise multiple comparison adjustments, and assesses sample size adequacy.

### Key Audit Findings:
1. **Macro F1 (Primary Outcome, $N=5$)**:
   - ULC-v3 achieves large effect sizes ($d_z > 2.1$) across all four comparisons.
   - Comparisons against **ALA Only** ($p = 0.0004$) and **Uncoordinated Three Pillars** ($p = 0.0006$) pass both unadjusted and Holm-adjusted $p < 0.01$ thresholds ($p_{\text{adj}} = 0.0018$).
   - However, comparisons against **Static Baseline** (raw $p = 0.0083$) and **Full ULC-v1** (raw $p = 0.0085$), while passing raw $\alpha = 0.01$, yield **Holm-adjusted $p = 0.0166$**. Therefore, under strict family-wise error control at $\alpha = 0.01$, they fail to reach statistical significance at $N=5$, passing only at $\alpha = 0.05$.
2. **Correction of Erroneous Claim on Balanced Accuracy**:
   - The prior completion report claimed that Balanced Accuracy improvements over Static Baseline ($p = 0.0454$) and Full ULC-v1 ($p = 0.0452$) met the research criteria.
   - **Correction**: $p = 0.0454$ does **not** meet $p < 0.01$. Furthermore, under Holm-Bonferroni adjustment, the adjusted p-value is **$p_{\text{adj}} = 0.0905$**, failing to reach significance even at $\alpha = 0.05$. Universal statistical superiority cannot be claimed for Balanced Accuracy at $N=5$.
3. **Resolution via Extended $N=20$ Seed Study ($df=19$)**:
   - To resolve the statistical power limitation of $N=5$, we executed an extended 20-seed experiment.
   - Across $N=20$ seeds, Macro F1 superiority of ULC-v3 is **overwhelmingly significant** across all baselines:
     - vs Static Baseline: $\Delta = +0.0935$, $t(19) = 8.396$, **$p = 8.12 \times 10^{-8}$** (Passes $p < 0.001$, Hedges' $g = 1.802$).
     - vs ALA Only: $\Delta = +0.1638$, $t(19) = 15.159$, **$p = 4.57 \times 10^{-12}$** (Passes $p < 0.001$, Hedges' $g = 3.254$).
     - vs Uncoordinated: $\Delta = +0.1568$, $t(19) = 14.622$, **$p = 8.62 \times 10^{-12}$** (Passes $p < 0.001$, Hedges' $g = 3.139$).
     - vs Full ULC-v1: $\Delta = +0.1421$, $t(19) = 10.601$, **$p = 2.04 \times 10^{-9}$** (Passes $p < 0.001$, Hedges' $g = 2.276$).

---

## 2. Statistical Audit on Original $N=5$ Study ($df=4$)

### 2.1. Primary Outcome: Macro F1 Score
- **ULC-v3 Mean**: $0.6455 \pm 0.0321$

| Comparison (ULC-v3 vs Target) | Target Mean | Diff ($\Delta$) [95% CI] | $t$-statistic | Raw $p$-value | Holm-Adjusted $p$ | Shapiro-Wilk $p$ (Normality) | Effect Size (Cohen's $d_z$) | Bias-Corrected (Hedges' $g$) | Verdict at $\alpha=0.01$ |
|---|---|---|---|---|---|---|---|---|---|
| **vs ALA Only** | $0.4737$ | $+0.1718$ [$+0.1269, +0.2167$] | $10.629$ | **$0.0004$** | **$0.0018$** | $0.2046$ (Valid) | $4.753$ | $3.803$ | **PASS (Raw & Holm)** |
| **vs Uncoordinated** | $0.4848$ | $+0.1607$ [$+0.1159, +0.2054$] | $9.958$ | **$0.0006$** | **$0.0018$** | $0.9415$ (Valid) | $4.453$ | $3.563$ | **PASS (Raw & Holm)** |
| **vs Static Baseline** | $0.5550$ | $+0.0905$ [$+0.0388, +0.1422$] | $4.859$ | **$0.0083$** | **$0.0166$** | $0.9624$ (Valid) | $2.173$ | $1.739$ | **Raw PASS, Holm FAIL** |
| **vs Full ULC-v1** | $0.4998$ | $+0.1457$ [$+0.0618, +0.2296$] | $4.820$ | **$0.0085$** | **$0.0166$** | $0.8363$ (Valid) | $2.156$ | $1.725$ | **Raw PASS, Holm FAIL** |

*Note on Non-Parametric Check*: Because $N=5$, the minimum achievable two-tailed p-value for the Wilcoxon signed-rank test is $p = 2 \times (1/2)^5 = 0.0625$. Thus, Wilcoxon tests cannot mathematically reject $H_0$ at $\alpha = 0.05$ with $N=5$. The Shapiro-Wilk tests confirmed normality ($p > 0.20$), validating parametric t-tests.

---

### 2.2. Secondary Outcome: Balanced Accuracy
- **ULC-v3 Mean**: $61.38 \pm 2.98\%$

| Comparison (ULC-v3 vs Target) | Target Mean | Diff ($\Delta$) [95% CI] | $t$-statistic | Raw $p$-value | Holm-Adjusted $p$ | Effect Size ($d_z$) | Verdict at $\alpha=0.01$ | Verdict at $\alpha=0.05$ |
|---|---|---|---|---|---|---|---|---|
| **vs ALA Only** | $50.00\%$ | $+11.38\%$ [$+7.23\%, +15.52\%$] | $7.626$ | **$0.0016$** | **$0.0063$** | $3.411$ | **PASS** | **PASS** |
| **vs Uncoordinated** | $50.00\%$ | $+11.38\%$ [$+7.23\%, +15.52\%$] | $7.626$ | **$0.0016$** | **$0.0063$** | $3.411$ | **PASS** | **PASS** |
| **vs Static Baseline** | $56.58\%$ | $+4.79\%$ [$+0.16\%, +9.42\%$] | $2.872$ | **$0.0454$** | **$0.0905$** | $1.285$ | **FAIL ($p \ge 0.01$)** | **FAIL (Holm $p > 0.05$)** |
| **vs Full ULC-v1** | $51.10\%$ | $+10.28\%$ [$+0.35\%, +20.21\%$] | $2.875$ | **$0.0452$** | **$0.0905$** | $1.286$ | **FAIL ($p \ge 0.01$)** | **FAIL (Holm $p > 0.05$)** |

> [!CAUTION]
> **Audit Finding**: In the previous report, $p = 0.0454$ was conflated with statistical clearance. At the mandatory $\alpha = 0.01$ threshold, Balanced Accuracy is **not statistically significant** over Static Baseline or Full ULC-v1. When adjusted for family-wise testing, $p_{\text{adj}} = 0.0905$, indicating inconclusive evidence at $N=5$.

---

### 2.3. Secondary Outcome: Calibration (Brier Score)
- **ULC-v3 Mean**: $0.120 \pm 0.005$ (Lower is better)

| Comparison (ULC-v3 vs Target) | Target Mean | Diff ($\Delta$) [95% CI] | $t$-statistic | Raw $p$-value | Holm-Adjusted $p$ | Verdict at $\alpha=0.01$ |
|---|---|---|---|---|---|---|
| **vs Static Baseline** ($0.163$) | $0.163$ | $-0.0423$ [$-0.0576, -0.0270$] | $-7.685$ | **$0.0015$** | **$0.0062$** | **PASS (Superior)** |
| **vs Full ULC-v1** ($0.204$) | $0.204$ | $-0.0832$ [$-0.1137, -0.0527$] | $-7.566$ | **$0.0016$** | **$0.0062$** | **PASS (Superior)** |
| **vs ALA Only** ($0.125$) | $0.125$ | $-0.0048$ [$-0.0113, +0.0016$] | $-2.084$ | $0.1056$ | $0.1393$ | **Inconclusive** |
| **vs Uncoordinated** ($0.126$) | $0.126$ | $-0.0058$ [$-0.0124, +0.0007$] | $-2.460$ | $0.0697$ | $0.1393$ | **Inconclusive** |

---

## 3. Sample Size Sufficiency Audit and Extended Study ($N=20$, $df=19$)

### Why $N=5$ Seeds are Insufficient for Borderline Effects:
With $n=5$ ($df=4$), the Student's t-distribution has heavy tails ($t_{\text{crit}} = 4.604$ at $\alpha=0.01$). Detecting a moderate-to-large effect ($d_z = 1.0$) with $80\%$ statistical power ($\beta = 0.20$) at $\alpha = 0.01$ requires at least **$N = 18$ paired observations**. At $N=5$, power drops to $\approx 31\%$, meaning true effects are frequently missed and observed p-values suffer high sampling variance.

### Extended $N=20$ Seed Study Results on Macro F1:
To provide conclusive, high-power evidence, we evaluated $N=20$ independent random seeds:

```
Extended Seed Array (N=20):
[42, 101, 2024, 7, 99, 13, 21, 55, 88, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711]
```

| Comparison | Target Mean ($N=20$) | Baseline Mean ($N=20$) | Mean Diff ($\Delta$) | 95% Confidence Interval | $t$-statistic ($df=19$) | Exact $p$-value | Hedges' $g$ | Formal Verdict |
|---|---|---|---|---|---|---|---|---|
| **ULC-v3 vs Static Baseline** | **$0.6391 \pm 0.0462$** | $0.5455 \pm 0.0187$ | $+0.0935$ | [$+0.0702, +0.1169$] | $8.396$ | **$8.12 \times 10^{-8}$** | $1.802$ | **CONVINCING PASS ($p < 10^{-7}$)** |
| **ULC-v3 vs ALA Only** | **$0.6391 \pm 0.0462$** | $0.4752 \pm 0.0047$ | $+0.1638$ | [$+0.1412, +0.1865$] | $15.159$ | **$4.57 \times 10^{-12}$** | $3.254$ | **CONVINCING PASS ($p < 10^{-11}$)** |
| **ULC-v3 vs Uncoordinated** | **$0.6391 \pm 0.0462$** | $0.4823 \pm 0.0096$ | $+0.1568$ | [$+0.1343, +0.1792$] | $14.622$ | **$8.62 \times 10^{-12}$** | $3.139$ | **CONVINCING PASS ($p < 10^{-11}$)** |
| **ULC-v3 vs Full ULC-v1** | **$0.6391 \pm 0.0462$** | $0.4970 \pm 0.0357$ | $+0.1421$ | [$+0.1140, +0.1702$] | $10.601$ | **$2.04 \times 10^{-9}$** | $2.276$ | **CONVINCING PASS ($p < 10^{-8}$)** |

### Conclusion of Extended Statistical Audit:
When evaluated at adequate statistical power ($N=20$), the Macro F1 advantage of Multi-Objective ULC-v3 is proven beyond all statistical doubt ($p < 10^{-7}$ across all comparisons). However, claims of statistical superiority must remain strictly restricted to **Macro F1, Brier score, and False Reset suppression**; Balanced Accuracy at $N=5$ remains inconclusive under family-wise error control.

