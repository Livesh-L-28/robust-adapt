# AdaptiveML Production Operations — Performance Tuning Guide

## 1. Streaming Latency and Throughput Architecture

AdaptiveML is engineered for low-latency, CPU-first streaming environments. Empirical benchmarks demonstrate:
- **Single-Sample Inference:** $4.70\,\mu\text{s}$ P50 latency ($209,000\text{ samples/s}$).
- **Batch Inference ($B=64$):** $154.40\,\mu\text{s}$ P50 latency ($409,000\text{ samples/s}$).
- **Integrated ULC-v4.1 Pipeline ($B=16$):** $1.56\text{ ms}$ P50 latency ($10,500\text{ samples/s}$).

---

## 2. Ingestion Batch Sizing Guidelines

In streaming deployments, selecting an appropriate ingestion micro-batch size ($B$) balances throughput against end-to-end pipeline latency:

| Ingestion Batch Size ($B$) | Pipeline Latency (P50) | Throughput (samples/s) | Best Suited For |
| :--- | :--- | :--- | :--- |
| **$B=1$ (Pure Online)** | $252\,\mu\text{s}$ | $3,660\text{ samples/s}$ | Hard real-time fraud detection, sub-millisecond trading triggers. |
| **$B=16$ (Recommended)** | $1,558\,\mu\text{s}$ | $10,560\text{ samples/s}$ | High-throughput sensor streams, edge gateway aggregators. |
| **$B=64$ (High-Throughput)**| $5,099\,\mu\text{s}$ | $12,460\text{ samples/s}$ | Near real-time log ingestion, network packet classification. |
| **$B \ge 256$** | $> 20,000\,\mu\text{s}$ | $\approx 12,500\text{ samples/s}$ | CPU cache thrashing observed; diminishing throughput returns. |

> [!TIP]
> For most production streaming deployments, a micro-batch size between **$16$ and $64$ samples** delivers the optimal balance of high throughput ($>10,000\text{ samples/s}$) and sub-$5\text{ ms}$ latency.

---

## 3. Algorithm Parameter Tuning

### 3.1 AdaptiveClassifier Grace Period
The `grace_period` controls how many streaming samples a leaf must observe before computing Hoeffding bounds for splitting:
```python
clf = AdaptiveClassifier(grace_period=50, delta=1e-4)
```
- **Low `grace_period` (e.g. 10–20):** Rapid tree growth, adapts quickly to changing distributions, but higher CPU overhead during continuous split re-evaluation.
- **High `grace_period` (e.g. 50–200):** Maximizes training throughput ($>20,000\text{ samples/s}$), ideal for stable or slowly drifting regimes.

### 3.2 Reliability Engine Spatial Buffer & Neighborhood
In [`MultiSignalReliabilityEngine`](file:///c:/projects/AdaptiveML/adaptive_ml/rla/reliability.py):
```python
engine = MultiSignalReliabilityEngine(k_neighbors=5, buffer_size=300)
```
- `buffer_size=300`: Keeps pairwise distance matrix computation small ($N \times 300$). Increasing beyond $1,000$ increases step latency without meaningful accuracy improvements.
- `k_neighbors=5`: Provides optimal noise filtering without susceptibility to local cluster sparsity.

### 3.3 Reliability-Weighted ADWIN Delta
In [`ReliabilityWeightedADWIN`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/adwin.py):
```python
adwin = ReliabilityWeightedADWIN(delta=0.002)
```
- Lower $\delta$ (e.g. $10^{-4}$): Decreases false positive drift detections in noisy streams.
- Higher $\delta$ (e.g. $10^{-2}$): Faster reaction to subtle or gradual concept drift.

---

## 4. Zero-Copy and Memory Alignment Tuning

1. **Ensure C-Contiguity:** Ensure feature matrices are contiguous in memory (`np.ascontiguousarray(X, dtype=np.float32)`).
2. **Avoid Type Casting in Streaming Loops:** Pass `float32` features and `int64` labels to eliminate runtime type promotion overhead.
3. **PyTorch Tensor Sharing:** On CPU, `torch.from_numpy()` creates a zero-copy tensor sharing underlying memory with NumPy. Avoid `.clone()` unless independent mutation is required.
