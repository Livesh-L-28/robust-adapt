# Frequently Asked Questions (FAQ)

### 1. Does AdaptiveML replace PyTorch or scikit-learn?
No. AdaptiveML is an algorithmic complement, not a framework replacement. It integrates directly with PyTorch models and scikit-learn pipelines.

### 2. Can AdaptiveML run on GPUs?
AdaptiveML is engineered CPU-first and local-first. PyTorch integrations can optimize GPU-resident tensors, but all core operations run with maximal efficiency on standard consumer and workstation CPUs without CUDA.

### 3. Why is the package registered as `aml-core` instead of `adaptiveml`?
To protect users and maintainers from trademark and namespace dilution regarding commercial entities bearing similar names (*Adaptive ML, Inc.*), the provisional distribution identifier is set to `aml-core`.

### 4. Is unpickling supported for checkpoints?
No. Standard Python `pickle` is unsafe on untrusted network streams. AdaptiveML exclusively uses safe serialization: JSON for metadata and `Safetensors` for array/tensor weights.
