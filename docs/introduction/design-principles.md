# Core Design Principles

AdaptiveML adheres to seven strict engineering and architectural principles:

---

## 1. Local-First & Cloud-Agnostic
- **No Mandatory Network Connection**: The library runs completely offline. It never dials out to external license servers, telemetry endpoints, or cloud backends.
- **Embedded & Edge Ready**: Designed to run inside resource-constrained Docker containers, Kubernetes sidecars, edge gateways, or local developer workstations.

## 2. CPU-First Execution Efficiency
- **Microsecond Latency**: Streaming inference ($5.06\ \mu\text{s}$) and prequential updates ($<320\ \mu\text{s}$) execute natively on standard x86_64 and ARM64 CPUs.
- **Zero Mandatory GPU/CUDA Dependencies**: GPU acceleration is optional via PyTorch; all core functionality runs on commodity CPU cores.

## 3. Minimal Mandatory Dependencies
- **Strictly Minimal Core**: `import robust_adapt` requires exclusively `numpy>=1.24.0`.
- **Decoupled Extras**: PyTorch, Scikit-Learn, SciPy, Pandas, Polars, and Safetensors are optional extras installed only when required (`pip install 'robust-adapt[torch]'`).

## 4. Strict $O(1)$ Memory Invariance
- **No Unbounded Buffers**: All historical buffers, sliding windows, queues, and concept stores enforce deterministic upper bounds via reservoir replacement, FIFO eviction, or LRU pruning.
- **Infinite Streaming Stability**: Tested across $100,000+$ consecutive samples; resident memory remains strictly sub-$50\text{ MB}$.

## 5. Security by Default & Zero-Pickle Architecture
- **Immune to Deserialization Exploits**: Python `pickle` is strictly forbidden across the codebase.
- **SafeTensors Persistence**: All model weights are serialized via binary SafeTensors.
- **HMAC-SHA256 Authenticity**: Optional keyed HMAC-SHA256 signatures with constant-time verification protect state files against tampering.

## 6. Stable, Scikit-Learn Compatible APIs
- **Protocol Compliance**: Core classifiers implement `fit`, `partial_fit`, `predict`, `predict_proba`, `get_params`, `set_params`.
- **PEP 561 Typing**: All public functions and classes are fully typed and ship with `py.typed`.

## 7. Zero Telemetry & Privacy Preservation
- **NullHandler Logging**: Root logger attaches `logging.NullHandler()` by default, emitting zero noise unless explicitly configured by the host application.
- **Zero PII**: Diagnostic events record purely numeric telemetry (loss, error rate, RSS memory). Customer feature payloads and labels are never logged.
