# TensorFlow / Keras Integration Assessment & Roadmap

AdaptiveML has conducted an exhaustive architectural and runtime assessment regarding deep integration with TensorFlow 2.x and Keras 3.

---

## 1. Executive Summary & Status

| Category | Assessment | Status |
|:---|:---|:---|
| **Primary Decision** | Formal Deferral of Native TensorFlow Adapters | **Deferred** |
| **Interim Path** | Zero-Copy NumPy Array Ingestion (`to_numpy`, `to_tensor`) | **Available & Supported** |
| **Root Drivers** | Python 3.14 ABI Incompatibility, Graph Compilation Mismatch, Heavy Footprint | Verified |

---

## 2. Technical Evaluation & Rationale

1. **Python 3.14 Wheel Availability:**
   As of Q4 2026, the official TensorFlow distribution does not distribute pre-compiled AMD64 binary wheels for Python 3.14 on Windows or Linux. Attempting to mandate TensorFlow support would break environment installation on modern Python runtimes.

2. **Static Graph Compilation vs Dynamic Quantization:**
   AdaptiveML's RAO algorithms (e.g., 8-bit block-quantized AdamW) rely on dynamic per-block scale normalization. Under `tf.function` XLA graph compilation, variable dynamic block allocation triggers trace recompilations, neutralizing quantization throughput gains.

3. **Dependency Footprint Inflation:**
   `aml-core` adheres to a lightweight footprint philosophy ($\approx 35\text{ MB}$). Introducing TensorFlow pulls in $> 550\text{ MB}$ of binaries (including CUDA dependencies, Abseil, FlatBuffers, and Protobuf), violating local-first design tenets.

---

## 3. Supported Interoperability Workflow

TensorFlow/Keras practitioners can interoperate with AdaptiveML seamlessly using the native NumPy tensor conversion bridge:

```python
import numpy as np
import tensorflow as tf
from robust_adapt.ala.classifier import AdaptiveClassifier
from robust_adapt.integrations.data import to_numpy

# 1. Extract feature representations from Keras backbone
feature_extractor = tf.keras.applications.MobileNetV2(include_top=False, pooling="avg")
tf_tensor = feature_extractor(images)

# 2. Convert to NumPy without serialization
np_features = to_numpy(tf_tensor.numpy())

# 3. Stream through AdaptiveML streaming tree
clf = AdaptiveClassifier(n_features=np_features.shape[1], n_classes=10)
clf.partial_fit(np_features, labels)
```

---

## 4. Future Roadmap

Native Keras 3 multi-backend adapters will be evaluated once TensorFlow publishes official Python 3.14+ binary wheels and stable XLA custom call bindings for dynamic block quantization.
