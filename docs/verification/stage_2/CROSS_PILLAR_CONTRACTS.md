# Stage 2: Cross-Pillar Contracts Specification
## Canonical Interfaces Governing ALA, RLA, RAO, and ULC Interoperability

**Document Identifier:** `VERIF-STAGE-2-004`<br>
**Distribution Package Identifier:** `aml-core`<br>
**Package Version:** `0.1.0.dev0`<br>
**Status:** `RATIFIED ARCHITECTURAL SPECIFICATION`

---

## 1. Architectural Philosophy

AdaptiveML adheres to a strict **Decoupled Pillar Architecture**:
1. Every pillar (ALA, RLA, RAO, ULC) must remain fully operational as a standalone module without requiring imports from or coupling to other pillars.
2. Cross-pillar coordination is executed via **structural typing, capability detection, and protocol contracts**.
3. No pillar may assume direct access to private internal attributes of another pillar (e.g. `_replay_buffer`).

---

## 2. Formal Protocol Contracts

### 2.1 Replay Buffer Protocol (`ReplayBufferProtocol`)

Any streaming model providing replay capabilities must satisfy the following contract:

```python
class ReplayBufferProtocol(Protocol):
    @property
    def total_stored(self) -> int:
        """Total number of instances currently retained."""
        ...

    @property
    def class_counts(self) -> Dict[int, int]:
        """Dictionary of counts stored per class."""
        ...

    def add(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> None:
        """Ingest batch into replay memory."""
        ...

    def sample(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Extract balanced replay batch."""
        ...

    def purge(
        self,
        policy: str = "selective",
        min_reliability: float = 0.0,
        keep_minority: bool = True,
        minority_classes: Optional[Sequence[int]] = None,
    ) -> int:
        """Purge obsolete or low-reliability samples while protecting minority data."""
        ...

    def clear(self) -> None:
        """Unconditionally flush all buffers."""
        ...
```

### 2.2 Streaming Classifier Protocol (`AdaptiveClassifierProtocol`)

```python
class AdaptiveClassifierProtocol(Protocol):
    @property
    def replay_buffer(self) -> Optional[ReplayBufferProtocol]:
        """Public access to the underlying replay buffer, if enabled."""
        ...

    def purge_replay(
        self,
        policy: str = "selective",
        min_reliability: float = 0.0,
        keep_minority: bool = True,
    ) -> int:
        """Purge obsolete instances according to specified policy."""
        ...

    def partial_fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[Sequence[int]] = None,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "AdaptiveClassifierProtocol":
        """Incrementally update model state."""
        ...
```

### 2.3 Adaptive Optimizer Protocol (`AdaptiveOptimizerProtocol`)

Any optimizer managed by RAO or coordinated by ULC must support runtime momentum flushes and dynamic learning rate adjustments:

```python
class AdaptiveOptimizerProtocol(Protocol):
    param_groups: List[Dict[str, Any]]

    def step(self, closure: Optional[Callable[[], float]] = None) -> Optional[float]:
        """Perform optimization step."""
        ...

    def reset_momenta(self, param_indices: Optional[Sequence[int]] = None) -> None:
        """Reset first-order momentum buffers and step counts to zero."""
        ...

    def scale_learning_rate(self, factor: float) -> None:
        """Scale current learning rate across parameter groups."""
        ...
```

### 2.4 ULC Action Directive Contract (`ControllerDirective`)

The ULC finite automaton communicates with executing pipelines strictly through immutable `ControllerDirective` records:

```python
@dataclass(frozen=True)
class ControllerDirective:
    state: ControllerState
    learning_rate_scale: float = 1.0
    reset_momentum: bool = False
    suppress_adwin: bool = False
    freeze_buffer: bool = False
    purge_replay: bool = False
    split_immediate: bool = False
    sample_filter_threshold: float = 0.0
    gradient_clip_factor: float = 1.0
    dwell_remaining: int = 0
    message: str = ""
```

---

## 3. Pillar Isolation Verification Matrix

| Pillar Combination | Dependency Direction | Coupling Mechanism | Isolation Status |
| :--- | :--- | :--- | :--- |
| **ALA standalone** | None | Pure NumPy / scikit-learn | **Strictly Isolated** |
| **RLA standalone** | None | Pure NumPy / PyTorch optional | **Strictly Isolated** |
| **RAO standalone** | None | Pure NumPy / PyTorch optional | **Strictly Isolated** |
| **ULC with ALA** | ULC $\rightarrow$ ALA | `AdaptiveClassifierProtocol` | **Decoupled via Protocol** |
| **ULC with RAO** | ULC $\rightarrow$ RAO | `AdaptiveOptimizerProtocol` | **Decoupled via Protocol** |
| **ULC with RLA** | ULC $\rightarrow$ RLA | `RobustPipelineProtocol` | **Decoupled via Protocol** |
