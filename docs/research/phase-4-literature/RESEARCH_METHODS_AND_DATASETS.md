# AdaptiveML — Research Methods and Benchmark Datasets

> **Document Status**: Complete Baseline Deliverable (Phase 4)  
> **Document Identifier**: `DOC-LIT-006`  
> **Last Updated**: 2026-11-01  
> **Scope**: Standardized evaluation protocols, statistical metrics, and public benchmark datasets

---

## 1. Experimental Methodologies by Research Pillar

### 1.1 ALA (Adaptive Learning Algorithms) Evaluation Protocols
1. **Prequential (Interleaved Test-Then-Train) Evaluation**:
   - Each streaming instance or batch is first evaluated for out-of-sample prediction accuracy, then used to update model parameters.
   - Prequential accuracy is computed using fading factors ($\alpha = 0.99$ or $0.999$):
     $$S_t = \alpha S_{t-1} + (1 - \alpha) \cdot \mathbb{I}(\hat{y}_t = y_t)$$
2. **Drift Detection Performance Metrics**:
   - **Detection Delay (Mean Steps to Detect)**: Number of samples between true change-point $\tau^*$ and alarm trigger $\hat{\tau}$: $\text{Delay} = \hat{\tau} - \tau^*$.
   - **False Positive Rate (FPR / False Alarms)**: Frequency of alarms raised during stationary distribution periods.
   - **Missed Drift Rate**: Failures to detect real concept drift within a pre-defined evaluation window.

---

### 1.2 RLA (Robust Learning Algorithms) Evaluation Protocols
1. **Synthetic Noise Injection Protocol**:
   - Clean datasets (CIFAR-10, CoverType) are perturbed with known noise rates $\eta \in [0.1, 0.6]$:
     - **Symmetric Noise**: Randomly flipping labels to any class with uniform probability.
     - **Asymmetric Noise**: Flipping semantically similar classes (e.g. *Truck* $\to$ *Automobile* with probability $\eta$).
2. **Human / Real-World Noise Benchmark Protocol**:
   - Benchmarking on **CIFAR-10N** (real crowdsourced human annotations from Amazon Mechanical Turk) and **Clothing1M** (web-scraped noisy e-commerce images).
3. **Imbalance & Tail Metrics**:
   - Rather than aggregate accuracy (which hides minority collapse), evaluate **Minority Class Recall**, **Macro F1-Score**, and **Rare Sample Retention Rate**.

---

### 1.3 RAO (Resource-Aware Optimization) Evaluation Protocols
1. **Memory Profiling**:
   - Dedicated heap memory tracking via Python `tracemalloc` capturing exact allocations during the `optimizer.step()` invocation.
   - Direct measurement of optimizer state memory footprint vs. theoretical parameter count ($8\Phi$ baseline for AdamW).
2. **Step Latency & Throughput**:
   - Measuring CPU step execution wall-clock time (milliseconds per step) averaged across 100 warm iterations.
3. **Convergence Quality**:
   - Verifying that compressed optimizers reach equivalent final test accuracy / validation perplexity within identical epoch budgets as 32-bit AdamW.

---

## 2. Master Benchmark Dataset Directory

| Dataset Name | Domain / Modality | Sample Count | Feature Dim | Target Classes | Target Pillar | Authoritative Download Source |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Electricity (ELEC2)** | Tabular Time-Series | 45,312 | 8 | 2 (Up / Down) | ALA | [OpenML Data 151](https://www.openml.org/d/151) |
| **Forest CoverType** | Tabular Multi-Class | 581,012 | 54 | 7 | ALA / RLA | [UCI ML Repository](https://archive.ics.uci.edu/dataset/31/covertype) |
| **Synthetic SEA** | Synthetic Stream | $10^5 - 10^6$ | 3 | 2 | ALA | Native generator (`aml.datasets.synthetic_sea`) |
| **Split-MNIST** | Vision (Digits) | 70,000 | $28 \times 28$ | 5 tasks of 2 classes | ALA Continual | Torchvision (`torchvision.datasets.MNIST`) |
| **CIFAR-10N** | Vision (Natural) | 60,000 | $32 \times 32 \times 3$ | 10 (Real Noise) | RLA | [CIFAR-N Dataset](https://github.com/UCSC-REAL/cifar-10-100n) |
| **Clothing1M** | Vision (E-Commerce) | 1,000,000 | $224 \times 224 \times 3$ | 14 (Real Noise) | RLA | Academic request only (Tsinghua University) |
| **California Housing** | Tabular Regression | 20,640 | 8 | Continuous | RAO Regression | Scikit-learn (`sklearn.datasets.fetch_california_housing`)|
