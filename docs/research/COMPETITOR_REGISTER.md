# AdaptiveML: Competitor Register & Capability Analysis

> **Document Status**: Authoritative Baseline (Phase 1 Deliverable)  
> **Working Codename**: AdaptiveML (*Provisional — Subject to formal legal and trademark clearance*)  
> **Document Identifier**: `DOC-RES-002`  
> **Last Updated**: 2026-11-01  
> **Classification Scheme**: Direct Competitor | Indirect Competitor | Complementary Tool | Research Framework | Infrastructure Platform | Potential Integration Partner

---

## 1. Competitor Classification Taxonomy

To ensure accurate strategic positioning, external software projects are classified into precise relationship categories:

```
+-------------------------------------------------------------------------------------------------------+
|                                    COMPETITOR CLASSIFICATION MAP                                      |
+--------------------------+---------------------------+------------------------------------------------+
| Pillar                   | Direct Competitors        | Indirect / Complementary / Research Frameworks |
+--------------------------+---------------------------+------------------------------------------------+
| **ALA (Adaptive)**       | River (partial overlap)   | Menelaus (Drift monitor)                       |
|                          |                           | Avalanche (Deep Continual Learning framework)  |
|                          |                           | scikit-multiflow (Legacy / archived)           |
+--------------------------+---------------------------+------------------------------------------------+
| **RLA (Robust)**         | Cleanlab (Data curation)  | imbalanced-learn (Resampling toolkit)          |
|                          |                           | Snorkel (Weak supervision / data programming)  |
|                          |                           | PyTorch Robust Loss repos (Academic codebases) |
+--------------------------+---------------------------+------------------------------------------------+
| **RAO (Resource-Aware)** | bitsandbytes (Quantized)  | PyTorch Optimizers (Foundational standard)     |
|                          | Adafactor (Factorized)    | DeepSpeed (Distributed scaling engine)         |
|                          | GaLore (Low-rank SVD)     | torchao (PyTorch Native Architecture Opt)      |
+--------------------------+---------------------------+------------------------------------------------+
| **ULC (Unified)**        | None (Clear White Space)  | Ray Train / ZenML / Prefect (Workflow DAGs)   |
+--------------------------+---------------------------+------------------------------------------------+
```

---

## 2. In-Depth Competitor Profiles

---

### 2.1 Profile: River
- **Category**: Direct Competitor (ALA Tabular Streaming).
- **Repository**: [https://github.com/online-ml/river](https://github.com/online-ml/river)
- **Documentation**: [https://riverml.xyz/](https://riverml.xyz/)
- **Distribution**: PyPI (`pip install river`), Conda-forge.
- **License**: BSD 3-Clause.
- **Main Purpose**: Online/streaming machine learning for Python, created by merging Creme and scikit-multiflow.
- **Algorithms**: Hoeffding Trees, Adaptive Random Forests, ADWIN, DDM, Page-Hinkley, online linear models, streaming metrics.
- **Primary API**: `model.learn_one(x, y)` / `model.predict_one(x)` using Python `dict`. Optional `learn_many` via `pandas.DataFrame`.
- **Dependencies**: Mandatory: `numpy`, `scipy`. Optional: `pandas`, `torch` (via `deep-river`).
- **Framework Support**: Standalone; integration with PyTorch via separate `deep-river` library.
- **Hardware**: Pure CPU (single-core Python loops).
- **Maintenance**: Active (regular releases, institutional backing from Inria / academic contributors).
- **Strengths**: Comprehensive streaming algorithms; excellent progressive evaluation metrics; pure Python usability.
- **Limitations**:
  - Enforces single-instance dictionary iteration (`learn_one`), causing extreme Python interpreter loop overhead on large-scale numerical datasets.
  - Does not natively support 2D NumPy array matrix batching (`partial_fit(X, y)`).
  - No built-in robust learning objectives for high-noise regimes or memory-efficient optimizer states.
- **Overlap with AdaptiveML**: Overlaps with ALA concept drift detection and incremental tabular classification.
- **AdaptiveML Design Lesson**: Adopt scikit-learn's standard `partial_fit(X, y)` on 2D NumPy arrays to achieve vector-level throughput without dict iteration penalties.

---

### 2.2 Profile: Cleanlab
- **Category**: Indirect Competitor / Potential Integration Partner (RLA).
- **Repository**: [https://github.com/cleanlab/cleanlab](https://github.com/cleanlab/cleanlab)
- **Documentation**: [https://cleanlab.ai/](https://cleanlab.ai/)
- **Distribution**: PyPI (`pip install cleanlab`), Cleanlab Studio (commercial SaaS).
- **License**: AGPL-3.0 (Open-Source Core) / Commercial.
- **Main Purpose**: Data-centric AI framework to detect label errors and characterize label noise in datasets.
- **Algorithms**: Confident Learning (joint distribution estimation between noisy and true labels), rank pruning.
- **Primary API**: `find_label_issues(labels, pred_probs)`.
- **Dependencies**: `numpy`, `scipy`, `scikit-learn`, `pandas`.
- **Framework Support**: Framework-agnostic (takes pre-computed predicted probabilities from any model).
- **Hardware**: CPU / GPU (depending on model used to generate probabilities).
- **Maintenance**: Highly active (commercial company with dedicated engineering team).
- **Strengths**: Industry gold standard for identifying annotation errors; rigorous theoretical backing (Northcutt et al.).
- **Limitations**:
  - Requires **offline, multi-pass out-of-fold cross-validation** to generate predicted probabilities; completely unusable in online streaming or single-pass training.
  - Treats "hard" minority examples with high loss as potential label errors, often pruning rare classes in imbalanced datasets.
  - Does not provide in-training robust loss functions or streaming estimators.
  - Core license is AGPL-3.0, restricting certain proprietary embedding workflows without a commercial license.
- **Overlap with AdaptiveML**: Overlaps with RLA sample reliability identification.
- **AdaptiveML Design Lesson**: Focus on **in-training, single-pass robust losses and streaming reliability weighting** that operate directly during optimization, preserving rare classes.

---

### 2.3 Profile: Avalanche (ContinualAI)
- **Category**: Research Framework / Complementary Tool (ALA Continual Learning).
- **Repository**: [https://github.com/ContinualAI/avalanche](https://github.com/ContinualAI/avalanche)
- **Documentation**: [https://avalanche.continualai.org/](https://avalanche.continualai.org/)
- **Distribution**: PyPI (`pip install avalanche-lib`).
- **License**: MIT.
- **Main Purpose**: End-to-end library for continual, lifelong learning research based on PyTorch.
- **Algorithms**: EWC, LwF, GEM, A-GEM, Synaptic Intelligence, Replay buffers, iCaRL, PackNet.
- **Primary API**: `strategy.train(experience)` / `strategy.eval(stream)` using PyTorch tensors and datasets.
- **Dependencies**: `torch`, `torchvision`, `pytorchcv`, `quadprog`, `gdown`.
- **Framework Support**: Strictly PyTorch.
- **Hardware**: CPU and GPU (CUDA).
- **Maintenance**: Active academic consortium (ContinualAI).
- **Strengths**: Unmatched breadth of continual learning research baselines; standardized benchmark scenarios (Split-MNIST, Permuted-MNIST).
- **Limitations**:
  - Heavy PyTorch dependency; massive installation footprint; steep learning curve (`Strategy`, `Plugin`, `Benchmark` abstractions).
  - Designed for academic benchmark scenarios with distinct "tasks/experiences"; poor fit for real-world continuous streaming tabular data.
  - Zero support for scikit-learn pipelines or pure NumPy execution.
- **Overlap with AdaptiveML**: Overlaps with ALA knowledge retention and catastrophic forgetting mitigation.
- **AdaptiveML Design Lesson**: Provide lightweight parameter-elasticity and bounded replay buffers callable in pure NumPy and scikit-learn without requiring PyTorch.

---

### 2.4 Profile: bitsandbytes
- **Category**: Direct Competitor (RAO Optimizer Compression).
- **Repository**: [https://github.com/bitsandbytes-foundation/bitsandbytes](https://github.com/bitsandbytes-foundation/bitsandbytes)
- **Documentation**: [https://huggingface.co/docs/bitsandbytes](https://huggingface.co/docs/bitsandbytes)
- **Distribution**: PyPI (`pip install bitsandbytes`).
- **License**: MIT.
- **Main Purpose**: Accessible 8-bit and 4-bit optimizers and quantization for deep neural networks.
- **Algorithms**: 8-bit Adam, 8-bit AdamW, 8-bit Lion, 8-bit LARS, LLM.int8(), NF4/FP4 quantization.
- **Primary API**: `bitsandbytes.optim.AdamW8bit(model.parameters(), lr=1e-3)`.
- **Dependencies**: `torch`.
- **Framework Support**: Strictly PyTorch.
- **Hardware**: Primarily NVIDIA CUDA; recent experimental CPU support requiring AVX2 / AVX-512 instruction sets.
- **Maintenance**: Active (maintained by Tim Dettmers and Hugging Face team).
- **Strengths**: Dominant solution for 8-bit LLM fine-tuning on consumer GPUs; massive ecosystem adoption.
- **Limitations**:
  - CPU execution incurs substantial dequantization latency overhead.
  - Complex binary wheel compilation; historical installation failures on Windows and older CPUs lacking AVX-512.
  - Purely targeted at neural network weights; no streaming estimators or tabular models.
- **Overlap with AdaptiveML**: Overlaps with RAO low-memory optimizer states.
- **AdaptiveML Design Lesson**: Develop CPU-native memory reduction techniques that do not rely on specialized hardware vector extensions or custom C++ shared libraries, ensuring frictionless cross-platform execution.

---

### 2.5 Profile: imbalanced-learn
- **Category**: Complementary Ecosystem Tool (RLA Imbalance).
- **Repository**: [https://github.com/scikit-learn-contrib/imbalanced-learn](https://github.com/scikit-learn-contrib/imbalanced-learn)
- **Documentation**: [https://imbalanced-learn.org/](https://imbalanced-learn.org/)
- **Distribution**: PyPI (`pip install imbalanced-learn`), Conda-forge.
- **License**: MIT.
- **Main Purpose**: Toolkit for addressing class imbalance through resampling strategies.
- **Algorithms**: SMOTE, ADASYN, RandomUnderSampler, TomekLinks, NearMiss, BalancedRandomForest.
- **Primary API**: `sampler.fit_resample(X, y)` conforming to scikit-learn pipeline syntax.
- **Dependencies**: `numpy`, `scipy`, `scikit-learn`, `joblib`.
- **Framework Support**: scikit-learn native.
- **Hardware**: CPU.
- **Maintenance**: Stable, mature maintenance under scikit-learn-contrib.
- **Strengths**: Ubiquitous standard for static tabular data resampling; familiar scikit-learn syntax.
- **Limitations**:
  - Relies entirely on static pairwise distance calculations across the full dataset; structurally incapable of streaming execution.
  - Completely blind to label noise: blindly interpolates synthetic samples around corrupted labels, magnifying annotation errors.
  - No PyTorch autograd loss integrations.
- **Overlap with AdaptiveML**: Overlaps with RLA minority-class preservation.
- **AdaptiveML Design Lesson**: Implement class-balanced robust loss formulations and streaming weight adjustments rather than synthetic data generation, maintaining robustness even when minority classes contain label errors.

---

### 2.6 Profile: Menelaus
- **Category**: Complementary Tool / Research Reference (ALA Drift Detection).
- **Repository**: [https://github.com/mitre/menelaus](https://github.com/mitre/menelaus)
- **Documentation**: [https://mitre.github.io/menelaus/](https://mitre.github.io/menelaus/)
- **Distribution**: PyPI (`pip install menelaus`).
- **License**: Apache-2.0.
- **Main Purpose**: Standalone concept drift and data drift detection library created by MITRE.
- **Algorithms**: ADWIN, DDM, EDDM, STEPD, Page-Hinkley, KdqTree, PCA-CD, Nearest Neighbors drift.
- **Primary API**: `detector.update(y_true, y_pred)` / `detector.drift_state`.
- **Dependencies**: `numpy`, `scipy`, `pandas`.
- **Framework Support**: Framework-agnostic detector objects.
- **Hardware**: CPU.
- **Maintenance**: Low/Moderate activity (specialized enterprise/government focus).
- **Strengths**: Clean modular detector classes; transparent statistical implementations; Apache-2.0 licensed.
- **Limitations**:
  - Only provides drift *detection* alerts; does not provide adaptive estimators, model retraining, or forgetting mechanisms.
  - Slower execution on multi-variate high-dimensional streams.
- **Overlap with AdaptiveML**: Overlaps with ALA drift detection primitives.
- **AdaptiveML Design Lesson**: Provide drift detection coupled directly to adaptive estimator update schedules, closing the loop between detection and mitigation.

---

## 3. Competitor Capability Comparison Matrix

| Capability / Dimension | River | Cleanlab | Avalanche | bitsandbytes | imbalanced-learn | Menelaus | **AdaptiveML (Target)** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Streaming Input (Mini-Batch 2D NumPy)** | Partial (`learn_many` via Pandas) | Not supported | Partial (via PyTorch Loaders) | Not supported | Not supported | Partial (Instance stream) | **Native Support (`partial_fit`)** |
| **Single-Event Stream (`dict`)** | Native Support (`learn_one`) | Not supported | Not supported | Not supported | Not supported | Native Support | **Partial Support (via adapter)** |
| **Concept Drift Detection** | Native Support | Not supported | Partial Support | Not supported | Not supported | Native Support | **Native Support** |
| **Knowledge Retention / Elasticity** | Partial Support | Not supported | Native Support | Not supported | Not supported | Not supported | **Native Support** |
| **In-Training Robust Loss Objectives** | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | **Native Support** |
| **Offline Label Error Detection** | Not supported | Native Support | Not supported | Not supported | Not supported | Not supported | **External Integration (Cleanlab)** |
| **Streaming Sample Reliability Scoring** | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | **Native Support** |
| **Class Imbalance in Streams** | Partial Support | Not supported | Not supported | Not supported | Not supported | Not supported | **Native Support** |
| **Minority-Preserving Noise Filtering** | Not supported | Partial (Risks pruning tails) | Not supported | Not supported | Not supported | Not supported | **Native Support** |
| **Optimizer State Memory Reduction** | Not supported | Not supported | Not supported | Native Support (8-bit) | Not supported | Not supported | **Native Support (CPU-first)** |
| **CPU Execution Optimization** | Native Support | Native Support | Partial Support | Partial (Latency penalty) | Native Support | Native Support | **Native Support (Zero GPU req)** |
| **Zero Mandatory Framework Dependencies** | Native Support | Partial (requires sklearn) | Not supported (requires torch) | Not supported (requires torch) | Partial (requires sklearn) | Native Support | **Native Support (NumPy only)** |
| **Unified Cross-Pillar Controller** | Not supported | Not supported | Not supported | Not supported | Not supported | Not supported | **Native Support (ULC Layer)** |

---

## 4. Competitor Strengths Analysis: What AdaptiveML Must Respect

1. **River's API Elegance in Streaming**: River established the benchmark for progressive validation (`metrics.Accuracy().update(y_true, y_pred)`). AdaptiveML should adopt progressive metric tracking conventions while supporting 2D NumPy vectorization.
2. **Cleanlab's Mathematical Grounding**: Cleanlab succeeded because it backed every feature with peer-reviewed mathematical proofs (Confident Learning in JAIR). AdaptiveML must match this standard of formal mathematical rigor in Phase 6.
3. **Avalanche's Benchmark Reproducibility**: Avalanche earned academic adoption by providing one-line access to standard reproducible benchmarks. AdaptiveML must provide standardized, reproducible benchmarks in Phase 12.
4. **PyTorch's Optimizer Contract**: `torch.optim.Optimizer` is the undisputed standard interface for deep learning optimization. RAO must conform exactly to `step()`, `zero_grad()`, `state_dict()` to achieve frictionless drop-in adoption.
