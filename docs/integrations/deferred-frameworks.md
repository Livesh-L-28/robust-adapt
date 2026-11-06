# Deferred Framework Integrations & Roadmap

AdaptiveML has conducted exhaustive architectural and runtime evaluations regarding deep integrations with TensorFlow 2.x, Keras 3, and other third-party frameworks.

---

## 1. Executive Summary & Status Matrix

| Framework | Status | Primary Decision Drivers | Recommended Interoperability Path |
|:---|:---:|:---|:---|
| **TensorFlow 2.x** | **Deferred** | Python 3.14 binary wheel unavailability, static graph compilation vs dynamic quantization mismatch, dependency bloat (>550 MB). | Zero-copy NumPy buffer ingestion via `to_numpy()`. |
| **Keras 3** | **Deferred** | Dynamic block-quantization custom call instability across multiple backends. | PyTorch backend native integration or NumPy bridge. |
| **JAX / Flax** | **Roadmap** | Strong functional fit; under active architectural evaluation for Q2 2027. | Functional array transformations via NumPy/DLPack. |

---

## 2. Technical Evaluation & Rationale for Deferral

### 2.1 Python 3.14 Binary Wheel Availability
As of Q4 2026, the official TensorFlow distribution does not distribute pre-compiled binary wheels for Python 3.14 on Windows or Linux. Attempting to mandate TensorFlow support would immediately break installation environments on modern Python releases.

### 2.2 Static Graph Compilation vs. Dynamic Block Quantization
AdaptiveML's RAO algorithms (such as 8-bit block-quantized AdamW) rely on dynamic per-block scale normalization:
$$q_i = \text{clip}\left(\left\lfloor \frac{w_i}{\text{scale}_b} \times 127 \right\rceil, -127, 127\right)$$
Under `tf.function` XLA graph compilation, variable dynamic block allocation triggers trace recompilations, neutralizing quantization throughput gains.

### 2.3 Dependency Footprint Inflation
`aml-core` adheres to a lightweight footprint philosophy ($\approx 35\text{ MB}$ uncompressed). Introducing TensorFlow pulls in $> 550\text{ MB}$ of binaries (including CUDA dependencies, Abseil, FlatBuffers, and Protobuf), violating local-first and CPU-efficient design tenets.

---

## 3. Supported Interoperability Workflow

TensorFlow/Keras practitioners can interoperate with AdaptiveML seamlessly using the native NumPy tensor conversion bridge:

```python
import numpy as np
from robust_adapt.ala import ALA30AdaptiveLearner
from robust_adapt.integrations import to_numpy

# 1. Feature extraction from Keras model in streaming pipeline
# (Assuming features extracted as numpy array or tensor)
features_np = np.random.randn(100, 32).astype(np.float32)
labels_np = np.random.randint(0, 2, size=100)

# 2. Convert to validated C-contiguous numpy array
X_clean = to_numpy(features_np, ensure_2d=True, dtype=np.float64)
y_clean = to_numpy(labels_np, ensure_1d=True, dtype=np.int64)

# 3. Stream through AdaptiveML streaming learner
learner = ALA30AdaptiveLearner(n_features=32, n_classes=2)
metrics = learner.fit_batch(X_clean, y_clean)
print(f"Incremental streaming accuracy: {metrics['accuracy'] * 100:.2f}%")
```

---

## 4. Re-evaluation Criteria

Native adapters for deferred frameworks will be formally re-evaluated when:
1. Official binary wheels for current Python versions (Python 3.14+) are published upstream.
2. Stable C++ / XLA custom call APIs allow dynamic block quantization without graph recompilation overhead.
3. Decoupled distribution wheels allow optional installation without inflating the core package footprint.
