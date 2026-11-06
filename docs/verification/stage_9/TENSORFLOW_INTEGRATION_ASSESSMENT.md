# AdaptiveML Stage 9 — TensorFlow / Keras Integration Assessment

**Document Identifier**: `STAGE-9-TF-ASSESS-001`<br>
**Distribution Name**: `aml-core`<br>
**Namespace**: `adaptive_ml`<br>
**Version**: `0.1.0.dev0`<br>
**Status**: FORMALLY DEFERRED (TECHNICAL FEASIBILITY AUDIT)<br>
**Date**: November 6, 2026<br>
**Governance**: DEF-004 Remains Open (Phase 17 & Phase 18 locked)

---

## 1. Executive Summary

This report delivers a thorough technical feasibility assessment regarding the integration of **TensorFlow and Keras** into the AdaptiveML (`aml-core`) framework.

In accordance with the Stage 9 engineering mandate ("*Do not implement a superficial adapter merely to claim framework coverage*"), this assessment investigates:
1. Upstream Python 3.14 runtime support and operating system compatibility.
2. The Keras model lifecycle, custom loss functions, and optimizer extension interfaces.
3. Impedance mismatches between AdaptiveML's dynamic 8-bit block quantization and TensorFlow's XLA graph compilation.
4. Dependency footprint, installation friction, and long-term maintenance costs.

**Architectural Determination**: Native TensorFlow integration is **formally deferred**. AdaptiveML will maintain clean, modular integration boundaries without implementing superficial or untested mocks.

---

## 2. Technical Evaluation Dimensions

### 2.1 Upstream Python 3.14 & OS Compatibility Barrier
- **Current Runtime Environment**: Python 3.14.3 AMD64 on Windows 11 Enterprise.
- **Upstream TensorFlow Status**: As of November 2026, official pre-compiled binary wheels for TensorFlow support Python 3.9 through Python 3.12, with experimental builds for Python 3.13. **Zero official wheels exist for Python 3.14 on Windows AMD64.**
- Any attempt to declare `tensorflow>=2.12.0` as an optional extra or import it during automated test runs fails with `ModuleNotFoundError` or unresolvable compilation requirements on standard Windows development environments.

### 2.2 Algorithmic & Compiler Impedance Mismatch
AdaptiveML's RAO pillar relies on dynamic CPU block quantization:
- In **PyTorch**, dynamic memory operations and block-wise tensor slicing are executed imperatively on Python-managed memory buffers with immediate eager execution.
- In **TensorFlow**, optimal performance requires `tf.function` compilation into static computation graphs or XLA (Accelerated Linear Algebra) clusters.
- Implementing dynamic block quantization (`BlockQuantizer` with power-of-2 slicing and non-uniform dynamic scaling) inside a TensorFlow graph without custom C++ kernel extensions incurs severe graph tracing overhead and loop performance penalties, negating the memory and latency benefits of RAO.

### 2.3 Dependency Footprint vs. Core Library Tenet
- AdaptiveML is engineered as a **local-first, CPU-first, lightweight library** whose core dependency is strictly `numpy>=1.24.0`.
- Standard TensorFlow wheels introduce over **550 MB** of binary dependencies, including Protobuf, Flatbuffers, MLIR, TensorBoard, and heavy platform libraries.
- For streaming ML practitioners, importing or bundling this massive dependency footprint to support streaming tabular classification or continual learning represents disproportionate bloat.

### 2.4 Keras 3 Multi-Backend Evolution
- Keras has evolved into **Keras 3** (`keras-core`), a multi-backend abstraction supporting PyTorch, JAX, and TensorFlow interchangeably.
- Rather than maintaining a brittle, legacy `tensorflow.keras` adapter, future integration efforts will achieve far broader impact by targeting Keras 3's backend-agnostic ops API once Python 3.14 upstream wheels stabilize.

---

## 3. Comparison of Framework Integration Feasibility

| Assessment Dimension | scikit-learn (Workstream B) | PyTorch (Workstream C) | TensorFlow / Keras (Workstream D) |
| :--- | :---: | :---: | :---: |
| **Python 3.14 Compatibility** | Verified (`1.8.0`) | Verified (`2.12.1`) | **Incompatible (No upstream wheels)** |
| **Execution Paradigm** | Streaming / Eager Tabular | Eager Dynamic Tensors | Static Graph / XLA Compilation |
| **RAO Optimizer Affinity** | N/A (Solvers embedded) | Native (`torch.optim.Optimizer`) | Requires custom C++ XLA Op |
| **Binary Footprint** | Low (~30 MB) | Moderate (~80 MB CPU) | **Very High (>550 MB)** |
| **Engineering Value** | High (Pipelines & Streaming) | High (Deep Neural Continual ML) | Low (Severe compilation friction) |
| **Final Recommendation** | **Tier 1 Supported** | **Tier 1 Supported** | **Formally Deferred** |

---

## 4. Future Integration Boundary Specification

When official TensorFlow wheels for Python 3.14+ are released and user demand warrants implementation, the integration should follow this decoupled blueprint:

1. **Location**: `adaptive_ml/integrations/tensorflow/`
2. **Keras Loss**:
   ```python
   # Future implementation blueprint:
   import keras
   from keras import ops

   class KerasSymmetricCrossEntropyLoss(keras.losses.Loss):
       def __init__(self, alpha=1.0, beta=0.5, name="symmetric_cross_entropy"):
           super().__init__(name=name)
           self.alpha = alpha
           self.beta = beta

       def call(self, y_true, y_pred):
           ce = ops.categorical_crossentropy(y_true, y_pred)
           rce = -ops.sum(y_pred * ops.log(y_true + 1e-7), axis=-1)
           return self.alpha * ce + self.beta * rce
   ```
3. **Keras Training Callback**:
   A `keras.callbacks.Callback` invoking [`DynamicResourceBudgetManager`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py) at `on_train_batch_end`.

---

## 5. Conclusion

Deferring native TensorFlow support is the technically disciplined, evidence-based decision. It protects AdaptiveML from fragile mock implementations, avoids breaking Python 3.14 environments, and concentrates engineering resources on deeply validated scikit-learn and PyTorch integrations.
