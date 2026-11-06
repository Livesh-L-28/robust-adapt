# Getting Started — Troubleshooting & Common Issues

This guide addresses common questions, debugging techniques, and resolution strategies when working with AdaptiveML.

---

## 1. Import and Packaging Issues

### Problem: `ModuleNotFoundError: No module named 'adaptive_ml'`
- **Cause**: The package was installed under an unexpected Python environment or the virtual environment is not activated.
- **Resolution**:
  Verify your Python runtime and pip environment:
  ```powershell
  py -3.14 -m pip list | findstr aml-core
  ```
  If not installed, run:
  ```powershell
  py -3.14 -m pip install -e .
  ```

### Problem: `ImportError: cannot import name 'torch' from 'adaptive_ml.backends'`
- **Cause**: PyTorch optional dependencies were not installed.
- **Resolution**:
  Install `aml-core` with the `[torch]` extra:
  ```bash
  pip install "robust-adapt[torch]"
  ```

---

## 2. Streaming Data & Validation Errors

### Problem: `ValidationError: Input feature dimension mismatch`
- **Cause**: The incoming batch has a feature dimension $D_{batch}$ that does not match the model's expected `n_features`.
- **Resolution**:
  Ensure all streaming batches have identical feature dimensionality:
  ```python
  assert X.shape[1] == classifier.n_features, f"Expected {classifier.n_features}, got {X.shape[1]}"
  ```

### Problem: `ValidationError: Target vector length does not match features`
- **Cause**: `len(X) != len(y)`.
- **Resolution**:
  Verify the batch slicing logic. Both `X` and `y` must contain the exact same number of samples.

---

## 3. Drift Detection Diagnostics

### Problem: Tree does not adapt when concept drift occurs
- **Cause**: The `grace_period` is set too high, or the statistical significance threshold $\delta$ in ADWIN is too strict (e.g. $10^{-6}$).
- **Resolution**:
  - Decrease `grace_period` (e.g. from 200 to 25 or 50) for fast-moving streams.
  - Increase `delta` in ADWIN (e.g. from 0.001 to 0.01) to increase sensitivity.

### Problem: False drift alerts triggered during noise bursts
- **Cause**: Standard drift detectors (ADWIN) cannot differentiate between a genuine distribution change and random label noise.
- **Resolution**:
  Use the **ULC-v4.1 Unified Controller** ([`UnifiedLearningControllerV4_1`](file:///c:/projects/AdaptiveML/adaptive_ml/ulc/v4_1_controller.py)), which integrates spatial discordance and reliability scoring to filter noise bursts without resetting models.

---

## 4. Resource & Memory Diagnostics

### Problem: Out of memory (OOM) on resource-constrained devices
- **Cause**: Unbounded tree growth or standard 32-bit floating point optimizer moments accumulating in memory.
- **Resolution**:
  - Enforce tree memory caps in `TreeConfig(memory_limit_mb=32.0)`.
  - Use [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) which reduces optimizer moment footprint by 73.4%.
  - Wrap streaming execution in a [`ResourceBudget`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py) to automatically trigger pruning.

---

## 5. Getting Further Help

- Review the [API Standardization Report](file:///c:/projects/AdaptiveML/docs/verification/stage_8/API_STANDARDIZATION_REPORT.md).
- Inspect the [Lifecycle and Error Handling Guide](file:///c:/projects/AdaptiveML/docs/verification/stage_8/ERROR_HANDLING_AND_LIFECYCLE.md).
- Run the executable examples located in the [`examples/`](file:///c:/projects/AdaptiveML/examples/) directory.
