# Stage 6: Technical Limitations & Operational Boundaries
## RAO 2.0 (Advanced Resource-Aware Optimization)

**Document Identifier:** `VERIF-STAGE-6-007`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Author:** Antigravity Engineering & Research Team

---

## 1. Subsystem Scope & Operational Boundaries

### 1.1 Process-Level Memory Tracking
- `DynamicResourceBudgetManager` measures memory consumption using process resident set size (RSS) via `get_process_memory_bytes()`. In environments hosting multiple background processes in the same Python runtime, memory spikes caused by external modules will be attributed to the overall process and may trigger conservative budget throttling.

### 1.2 Disk I/O Overhead in Checkpoint Recovery
- `ResilientCheckpointManager` computes SHA-256 digests over JSON-serialized state dictionaries and calls `os.fsync` to enforce atomic write flushing. While negligible for streaming models ($< 5\text{ ms}$ for typical model checkpoints), calling `save_checkpoint` on every single streaming step will bottleneck pipeline throughput. Checkpointing should be scheduled on a stride basis (e.g. every $100$ or $1{,}000$ steps) or triggered conditionally upon ULC state transitions.

### 1.3 Micro-Batch Scaling Granularity
- Batch size adjustments in `DynamicResourceBudgetManager` scale geometrically between `min_batch_size` and `max_batch_size`. For workloads requiring strict constant batch sizes due to external streaming buffers, batch scaling can be pinned by setting `min_batch_size == max_batch_size`.
