# AdaptiveML — Phase 5: Preliminary Experimental Designs

> **Document Status**: Complete Baseline Deliverable (Phase 5)  
> **Document Identifier**: `DOC-RES-P5-008`  
> **Last Updated**: 2026-11-01  
> **Target Execution Phase**: Phase 12 (Research Experiments & Benchmarking)

---

## 1. Universal Statistical Testing & Hardware Protocol

To ensure absolute reproducibility across all Phase 12 benchmark runs:
1. **Multi-Seed Protocol**: Every experiment must execute across **5 independent randomized seeds**: `[42, 1337, 2026, 9999, 88888]`.
2. **Statistical Significance Testing**: Superiority claims must be substantiated by the two-tailed **Wilcoxon signed-rank test** with significance threshold $\alpha = 0.01$.
3. **Hardware Environment Specification**:
   - Single-node commodity CPU runner (minimum 4-core, 8 GB to 16 GB RAM).
   - Zero GPU requirement for primary verification.
   - Recording exact NumPy BLAS configuration (`numpy.show_config()`) and CPU model.

---

## 2. Experiment Design 1: RLA Minority-Preserving Noise Resilience (EXP-RLA-01)

### 2.1 Benchmark Architecture & Datasets
- **Objective**: Measure minority-class preservation under combined label noise and severe class imbalance.
- **Datasets**:
  1. **Imbalanced CIFAR-10**: Exponential class decay with imbalance ratio $\text{IR} = 50:1$; classes 8 and 9 represent minority tails.
  2. **Forest CoverType**: Real-world ecological dataset where Class 4 represents $<0.5\%$ of instances.
- **Noise Injection Regimes**:
  - Symmetric Noise: $\eta \in \{0.0, 0.2, 0.4, 0.6\}$.
  - Asymmetric Noise: Semantically paired transitions with $\eta = 0.3$.
- **Models**: Standard 3-layer Tabular MLP (CoverType); ResNet-18 (CIFAR-10).
- **Baselines**:
  1. Standard Cross-Entropy (Baseline ERM)
  2. Cleanlab Confident Learning (Pruning baseline)
  3. Generalized Cross Entropy (GCE, $q=0.7$)
  4. Symmetric Cross Entropy (SCE, $\alpha=0.1, \beta=1.0$)
  5. **AdaptiveML RLA (Density-Aware Margin Scorer)**
- **Reported Metrics**: Minority Class Recall, Macro F1, Overall Accuracy, False Positive Pruning Rate (clean samples discarded).

---

## 3. Experiment Design 2: ULC In-Loop Drift-Noise Arbitration (EXP-ULC-01)

### 3.1 Benchmark Architecture & Datasets
- **Objective**: Measure drift alarm false-positive suppression and recovery speed under non-stationary dirty streams.
- **Datasets**:
  1. **Synthetic SEA Stream**: $100,000$ instances with 3 abrupt concept drifts at steps $25k, 50k, 75k$; transient label noise bursts ($\eta = 0.4$, duration $500$ samples) injected at stationary steps $12.5k, 37.5k, 62.5k$.
  2. **Electricity (ELEC2)**: Real 45,312 stream with injected noise spikes.
- **Baselines**:
  1. Uncoordinated Stream: Standard ADWIN + River Hoeffding Tree
  2. Static Batch Model (retrained every $10,000$ samples)
  3. **AdaptiveML ULC: Dual-Evidence Arbitration Automaton**
- **Reported Metrics**:
  - Number of False Drift Alarms triggered during stationary noise bursts.
  - Mean Detection Delay (samples) on true abrupt drift at $25k, 50k, 75k$.
  - Rolling Prequential Accuracy ($\alpha = 0.999$) throughout the complete stream.

---

## 4. Experiment Design 3: RAO CPU Low-Memory Optimizer Profiling (EXP-RAO-01)

### 4.1 Benchmark Architecture & Datasets
- **Objective**: Verify heap memory reduction and step execution latency on commodity CPU hardware.
- **Datasets & Architectures**:
  1. **Tabular Deep MLP** ($5\text{ hidden layers}, 1024\text{ units}$, $5\text{M parameters}$) on Forest CoverType.
  2. **ResNet-18** ($11.7\text{M parameters}$) on CIFAR-10 executed purely on CPU.
- **Baselines**:
  1. Standard PyTorch `AdamW` (fp32)
  2. Standard `SGD + Momentum` (fp32)
  3. `Adafactor` (momentum-free)
  4. `bitsandbytes.optim.AdamW8bit` (CPU backend)
  5. **AdaptiveML `LowMemoryAdamW` (Pure NumPy / PyTorch block-quantized)**
- **Reported Metrics**:
  - Optimizer State Memory Footprint (MB allocated via `tracemalloc`).
  - Step Execution Latency (ms per optimizer step).
  - Number of Steps / Epochs to reach target training loss threshold.
  - Final Validation Accuracy.
