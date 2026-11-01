# AdaptiveML — Phase 5: Research Questions & Formal Hypotheses

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-007`  
> **Last Updated**: 2026-11-01  
> **Scope**: Detailed Scientific Specifications for all P0 and P1 Priority Gaps

---

## 1. Research Protocol for P0 Gap: GAP-01 (RLA Small-Loss Imbalance)

- **Research Question (RQ-1)**: Can a density-aware margin reliability scorer protect legitimate minority-class instances from noise-pruning while achieving equal or superior clean-label accuracy compared to Confident Learning?
- **Alternative Hypothesis ($H_1$)**: Normalizing prediction margin by local feature density $\rho_k(x)$ will increase minority-class recall by $\ge 15\%$ on imbalanced noisy datasets without degrading majority-class accuracy by $>2\%$ relative to standard Confident Learning.
- **Null Hypothesis ($H_0$)**: Incorporating local feature density yields no statistically significant difference in minority-class recall ($p \ge 0.01$, Wilcoxon signed-rank test).
- **Baselines for Comparison**: Standard ERM (Cross-Entropy), Confident Learning (`cleanlab`), Generalized Cross Entropy (Zhang & Sabuncu, 2018), Symmetric Cross Entropy (Wang et al., 2019).
- **Independent Variables**: Noise rate $\eta \in [0.1, 0.5]$ (symmetric and asymmetric), class imbalance ratio $\text{IR} \in [10:1, 100:1]$, density estimator bandwidth $k \in [5, 20]$.
- **Dependent Variables**: Minority Class Recall, Macro F1-Score, Clean-Sample Retention Rate, Accuracy.
- **Target Datasets**: Imbalanced CIFAR-10N (with injected synthetic tail imbalance), Forest CoverType (classes 4 and 5 as rare tails).
- **Failure Conditions**: If density estimation computational overhead exceeds $20\%$ of training epoch time, or if density errors in high dimensions degrade majority accuracy by $>5\%$.

---

## 2. Research Protocol for P0 Gap: GAP-02 (ULC Drift-Noise Collision)

- **Research Question (RQ-2)**: Can in-loop sample reliability weighting within a finite state arbitration automaton reduce false-positive concept drift triggers caused by transient label noise bursts without increasing true drift detection delay?
- **Alternative Hypothesis ($H_1$)**: Weighting ADWIN sub-window error statistics by sample reliability scores will suppress false-alarm drift alerts by $\ge 60\%$ during transient label noise bursts while maintaining true drift detection delay within $100$ samples of clean ADWIN.
- **Null Hypothesis ($H_0$)**: Reliability-weighted ADWIN yields no statistically significant reduction in false alarms ($p \ge 0.01$).
- **Baselines for Comparison**: Uncoordinated ADWIN + River Hoeffding Tree, Standard DDM, Naive Retraining Pipeline.
- **Independent Variables**: Noise burst magnitude $\eta_{\text{burst}} \in [0.2, 0.6]$, noise burst duration $L \in [50, 500\text{ samples}]$, drift type (abrupt vs gradual SEA concepts).
- **Dependent Variables**: False Alarm Rate (alarms per $10^4$ stationary samples), Drift Detection Delay (samples), Prequential Accuracy over non-stationary dirty streams.
- **Target Datasets**: Synthetic SEA with injected noise bursts, Electricity (ELEC2) with synthetic noise injection.
- **Failure Conditions**: If the arbitration automaton delays genuine abrupt drift detection by $>250\text{ samples}$ compared to uncoordinated ADWIN.

---

## 3. Research Protocol for P0 Gap: GAP-03 (RAO CPU Low-Memory AdamW)

- **Research Question (RQ-3)**: Can a pure Python/NumPy block-quantized optimizer achieve a $\ge 30\%$ to $50\%$ reduction in optimizer state heap memory relative to 32-bit AdamW on standard CPUs while matching final convergence within $1\%$ validation accuracy?
- **Alternative Hypothesis ($H_1$)**: Block-wise symmetric integer scaling ($B=256$) executed in vector NumPy/PyTorch CPU operations will reduce optimizer state memory by $\ge 40\%$ and match final test accuracy of 32-bit AdamW within $\pm 0.5\%$ across standard benchmark architectures.
- **Null Hypothesis ($H_0$)**: Block-quantized integer scaling diverges or degrades final task accuracy by $>2\%$ relative to 32-bit AdamW.
- **Baselines for Comparison**: Standard PyTorch `AdamW` (fp32), Standard `SGD + Momentum` (fp32), `Adafactor` (momentum-free), `bitsandbytes.optim.AdamW8bit` (CPU backend).
- **Independent Variables**: Block size $B \in [64, 256, 2048]$, model architecture (ResNet-18, Tabular MLP, Mini-Transformer), learning rate $\gamma \in [10^{-4}, 10^{-2}]$.
- **Dependent Variables**: Peak Heap Memory during step (`tracemalloc`), Step Wall-Clock Latency (ms), Final Validation Loss & Accuracy.
- **Target Datasets**: California Housing (Tabular MLP), CIFAR-10 (ResNet-18).
- **Failure Conditions**: If per-step CPU quantization latency overhead exceeds $25\%$ of standard AdamW step time, or if numerical underflow causes gradient divergence.
