# AdaptiveML Production Operations — Resource Management Guide

## 1. Principles of Resource-Aware Optimization (RAO)

In high-throughput edge, on-premise, or cloud streaming ML deployments, memory consumption and latency variance must remain strictly bounded. Unchecked memory growth leads to OS out-of-memory (OOM) killer terminations, while latency spikes breach production service level agreements (SLAs).

AdaptiveML enforces resource predictability through four core mechanisms:
1. **Dynamic Resource Budgeting:** Real-time latency and memory utilization monitoring.
2. **Quantized Optimizer States:** $75\%$ reduction in AdamW optimizer memory via 64-block quantization.
3. **Adaptive Gradient Accumulation:** Dynamic scaling of micro-batch execution under tight memory ceilings.
4. **Stratified Reservoir Memory:** Class-balanced rehearsal buffers with hard capacity ceilings.

---

## 2. Dynamic Resource Budget Manager

The [`DynamicResourceBudgetManager`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/budget.py) monitors wall-clock execution time and RSS footprint:

```python
from robust_adapt.rao.budget import DynamicResourceBudgetManager

budget_mgr = DynamicResourceBudgetManager(
    max_step_time_ms=50.0,    # SLA step latency ceiling
    max_memory_mb=2048.0,     # Physical memory allocation ceiling
    throttle_factor=0.5,      # Back-off multiplier on breach
)
```

### Utilization Evaluation
During each step, the budget manager evaluates resource state:
- If `step_time_ms > max_step_time_ms`: Emits `THROTTLE_COMPUTATION` directive, scaling down batch size or disabling optional tree split evaluations.
- If `current_memory_mb > max_memory_mb`: Emits `PURGE_REPLAY` or `SHRINK_BUFFERS` directive to reclaim heap space.

---

## 3. Low-Memory Optimizer Deployment

Standard AdamW stores first ($m$) and second ($v$) moment vectors in 32-bit floating point, tripling model parameter memory overhead. In contrast, [`LowMemoryAdamW`](file:///c:/projects/AdaptiveML/adaptive_ml/rao/adamw.py) segments tensors into 64-element blocks and applies dynamic 8-bit quantization:

```python
from robust_adapt.integrations import create_torch_low_memory_adamw

# Drop-in replacement for torch.optim.AdamW
optimizer = create_torch_low_memory_adamw(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-4,
    block_size=64,
)
```

### Memory Footprint Comparison

| Parameter Count | Standard AdamW State | LowMemoryAdamW State | Memory Reduction |
| :--- | :--- | :--- | :--- |
| **$10\text{ Million}$** | $80.0\text{ MB}$ | $20.3\text{ MB}$ | **$-74.6\%$** |
| **$100\text{ Million}$** | $800.0\text{ MB}$ | $203.1\text{ MB}$ | **$-74.6\%$** |
| **$1\text{ Billion}$** | $8.0\text{ GB}$ | $2.03\text{ GB}$ | **$-74.6\%$** |

---

## 4. Rehearsal Buffer Capacity Limits

To prevent infinite memory growth during continual learning, the [`ClassBalancedReservoirReplay`](file:///c:/projects/AdaptiveML/adaptive_ml/ala/replay.py) enforces a strict sample ceiling:

```python
from robust_adapt.ala.replay import ClassBalancedReservoirReplay

# Bounded capacity of 2,000 samples across 5 classes
replay = ClassBalancedReservoirReplay(capacity=2000, n_classes=5)
```

- When the buffer reaches 2,000 samples, incoming instances replace existing instances using Vitter's Algorithm $R$.
- Majority-class samples are preferentially replaced to safeguard minority class representation.
- Absolute heap memory remains constant at $O(\text{capacity} \times \text{features})$.
