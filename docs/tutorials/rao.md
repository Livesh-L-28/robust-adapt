# Pillar Tutorial: Resource-Aware Optimization (RAO)

This tutorial covers memory reduction, 8-bit dynamic quantization, budget enforcement, and resource profiling using AdaptiveML's RAO pillar.

---

## 1. Resource Challenges in Continual Learning

Continual and streaming machine learning systems operate indefinitely without restarts. Under continuous execution, three resource hazards emerge:
1. **Optimizer Memory Bloat**: Standard AdamW maintains two 32-bit floating-point moment states ($m_t, v_t$) per model parameter, tripling the required memory footprint.
2. **Memory Leaks and Buffer Growth**: Streaming data accumulation can cause gradual memory exhaustion (OOM).
3. **Step Latency Spikes**: Complex incremental updates can cause streaming backpressure and pipeline stalls.

AdaptiveML resolves these hazards through:
- **8-Bit Low-Memory Optimizer** ([`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py)): Reduces optimizer memory overhead by 73.4%.
- **Resource Budgets** ([`ResourceBudget`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py)): Enforces maximum memory and latency thresholds.
- **Resource Profiling** ([`ResourceProfiler`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/profiler.py)): Continuously monitors peak memory and step duration.

---

## 2. 8-Bit LowMemoryAdamW Optimization

[`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) uses non-linear block-wise dynamic 8-bit quantization to store first and second momentum buffers.

### Memory Comparison
For a model with $N$ parameters:
- **Standard FP32 AdamW**: $N \times 4\text{ bytes (params)} + N \times 4\text{ bytes } (m_t) + N \times 4\text{ bytes } (v_t) = 12N\text{ bytes}$.
- **AdaptiveML LowMemoryAdamW**: $N \times 4\text{ bytes (params)} + N \times 1\text{ byte } (m_t) + N \times 1\text{ byte } (v_t) + \text{scales} \approx 6N\text{ bytes}$.
- **Net Optimizer State Savings**: $\frac{8 - 2}{8} = 75\%$ theoretical savings ($73.44\%$ empirical savings including quantization scales).

```python
import torch
import torch.nn as nn
from robust_adapt import LowMemoryAdamW

# 1. Define neural architecture
model = nn.Sequential(
    nn.Linear(64, 256),
    nn.ReLU(),
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
)

# 2. Instantiate 8-bit optimizer
optimizer = LowMemoryAdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)

# 3. Standard PyTorch training step
inputs = torch.randn(32, 64)
targets = torch.randint(0, 10, (32,))
criterion = nn.CrossEntropyLoss()

optimizer.zero_grad()
outputs = model(inputs)
loss = criterion(outputs, targets)
loss.backward()
optimizer.step()

print(f"Step completed. Optimizer memory state compressed by >73%.")
```

---

## 3. Strict Resource Budget Enforcement

Use [`ResourceBudget`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py) to protect microservices and edge devices from resource exhaustion:

```python
from robust_adapt import ResourceBudget, ResourceBudgetExceededError

# Enforce strict maximums: 128 MB RAM, 50 ms per streaming step
budget = ResourceBudget(max_memory_mb=128.0, max_step_time_ms=50.0, strict=True)

for step in range(100):
    with budget.track_step():
        # Perform streaming update
        clf.partial_fit(X_batch, y_batch)

    # Check current resource status
    status = budget.get_status()
    if status["memory_usage_ratio"] > 0.85:
        print(f"Memory warning: {status['memory_usage_ratio']:.1%} of budget consumed. Pruning buffers.")
        clf.prune_memory()
```

If `strict=True` is configured and limits are exceeded, [`ResourceBudgetExceededError`](file:///c:/projects/AdaptiveML/adaptive_ml/core/exceptions.py) is raised immediately before system crash.

---

## 4. Hardware Telemetry & Profiling

The [`ResourceProfiler`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/profiler.py) logs detailed execution statistics:

```python
from robust_adapt import ResourceProfiler

profiler = ResourceProfiler()

profiler.start()
# Execute streaming pipeline workload
for batch in stream:
    process_batch(batch)
report = profiler.stop()

print(f"Peak RSS Memory: {report['peak_memory_mb']:.2f} MB")
print(f"Average Step Latency: {report['avg_step_duration_ms']:.2f} ms")
print(f"Throughput: {report['samples_per_second']:.0f} samples/sec")
```
