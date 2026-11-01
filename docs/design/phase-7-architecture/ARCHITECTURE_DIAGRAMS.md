# AdaptiveML — Comprehensive Architecture Diagrams Catalog

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-012`  
> **Last Updated**: 2026-11-01  
> **Scope**: Collection of 12 official Mermaid architectural diagrams matching written specifications  
> **Compliance**: Fully compliant with GitHub Flavored Markdown and Antigravity Mermaid rendering standards

---

## 1. System Context Diagram

```mermaid
flowchart TD
    UserApp["User Application (Notebooks / Streaming Services / Microservices)"]
    
    subgraph AdaptiveMLRuntime ["AdaptiveML Runtime (Local Process Memory)"]
        PublicAPI["Public Facades (aml.ala, aml.rla, aml.rao, aml.ulc)"]
        Engines["Core Algorithmic Engines (ALA, RLA, RAO, ULC)"]
        CoreLib["Shared Core, Data Structures & Execution Backends"]
        PublicAPI --> Engines
        Engines --> CoreLib
    end
    
    subgraph OptionalDeps ["Optional Framework Integrations"]
        PyTorch["PyTorch (torch.optim, Tensor autograd)"]
        Sklearn["scikit-learn (BaseEstimator, Pipeline)"]
        Dataframe["Pandas / Polars DataFrames"]
    end
    
    subgraph HostPlatform ["Host Platform / Operating System"]
        CPU["Standard Multi-Core CPU (x86_64 / ARM64)"]
        NumPySIMD["NumPy Vector SIMD Engine"]
        Storage["Local Disk / RAM Checkpoints"]
    end

    UserApp -->|"Calls API"| PublicAPI
    CoreLib -.->|"Lazy Import"| OptionalDeps
    CoreLib -->|"Executes BLAS/SIMD"| NumPySIMD
    NumPySIMD --> CPU
    CoreLib -->|"Safe Safetensors IO"| Storage
```

---

## 2. Six-Layer Architectural Model

```mermaid
flowchart TD
    L1["Layer 1: Public Surface & Estimator Facade (AdaptiveClassifier, LowMemoryAdamW)"]
    L2["Layer 2: Core Algorithmic Engines (Hoeffding Tree, RW-ADWIN, Margin Scorer, SCE Loss)"]
    L3["Layer 3: Shared Core & Data Structures (SlidingWindow, Quantile Bins, Reservoir Pools)"]
    L4["Layer 4: Execution Backends (NumPy SIMD Engine, PyTorch Bridge Engine)"]
    L5["Layer 5: Ecosystem Framework Adapters (Scikit-Learn Adapter, PyTorch Optimizer Bridge)"]
    L6["Layer 6: State, Validation & Diagnostics (Safetensors Serde, Boundary Validators)"]

    L1 --> L2
    L2 --> L3
    L3 --> L4
    L1 -.-> L5
    L2 -.-> L6
    L4 --> L6
```

---

## 3. Package Dependency & Module Boundary DAG

```mermaid
flowchart TD
    Core["adaptive_ml.core (Types, Exceptions, Validation, Telemetry)"]
    Backends["adaptive_ml.backends (NumPy SIMD, PyTorch Bridge)"]
    State["adaptive_ml.state (Safetensors Serializer, Checkpoints)"]
    
    ALA["adaptive_ml.ala (Adaptive Learning)"]
    RLA["adaptive_ml.rla (Robust Learning)"]
    RAO["adaptive_ml.rao (Resource-Aware Opt)"]
    
    ULC["adaptive_ml.ulc (Unified Controller)"]
    Integrations["adaptive_ml.integrations (sklearn, torch_optim)"]

    Backends --> Core
    State --> Core
    
    ALA --> Core
    ALA --> Backends
    
    RLA --> Core
    RLA --> Backends
    
    RAO --> Core
    RAO --> Backends
    RAO --> State

    ULC --> Core
    ULC --> ALA
    ULC --> RLA
    ULC --> RAO

    Integrations --> Core
    Integrations --> ALA
    Integrations --> RAO
```

---

## 4. ALA Streaming Pipeline Architecture

```mermaid
flowchart LR
    BatchIn["Streaming Batch (X, y)"] --> RouteLeaves["Route Batch to Active Leaves"]
    RouteLeaves --> Digitize["Digitize Continuous Features (np.digitize)"]
    Digitize --> AccHist["Vectorized In-Place Histogram Accumulation"]
    AccHist --> CheckGrace["Check Leaf Grace Period (n_u >= n_min)"]
    CheckGrace -->|"Yes"| HoeffdingCheck["Hoeffding Split Test (Delta G > eps_H)"]
    CheckGrace -->|"No"| ReplayStep["Class-Balanced Reservoir Step"]
    HoeffdingCheck -->|"Split Condition Met"| SplitNode["Convert Leaf to Internal Node"]
    HoeffdingCheck -->|"Not Met"| ReplayStep
    SplitNode --> ReplayStep
    ReplayStep --> BatchOut["Updated Classifier State"]
```

---

## 5. RLA Denoising & Weighting Flow

```mermaid
flowchart LR
    Batch["Batch (X, y) & Model Logits z"] --> LogitMargin["Signed Logit Margin: M = z_y - max z_j"]
    Batch --> KNNDensity["Pairwise L2 Matrix & k-NN Density: rho_k"]
    LogitMargin --> CoupledScorer["Coupled Density-Margin Scorer: r_i = Phi(M - gamma*ln(rho))"]
    KNNDensity --> CoupledScorer
    CoupledScorer --> BranchMethod{"Dispatch Mode"}
    BranchMethod -->|"Soft Weighting"| SoftWeights["Sample Weights: w_i = r_i"]
    BranchMethod -->|"Hard Filtering"| HardFilter["Drop Corrupted: r_i < theta_filter"]
    SoftWeights --> RobustLoss["Symmetric Cross Entropy Loss (SCE)"]
    HardFilter --> RobustLoss
    RobustLoss --> BoundedGrad["Strictly Bounded Gradients for Backprop"]
```

---

## 6. RAO Block-Quantization Memory Flow

```mermaid
flowchart TD
    Params["Parameters theta & Gradients g in R^p"] --> Slicer["Block Slicer (Non-Overlapping Blocks of 256 Elements)"]
    
    subgraph BlockProcessing ["In-Place Block Execution (L1 Cache Resident)"]
        Dequant["Dequantize int8 m & uint8 v via Float32 Block Scales"]
        ComputeEMA["Compute Moving Averages (beta1 * m, beta2 * v)"]
        DescentStep["Apply Parameter Descent Step: theta - lr * update"]
        Requantize["Compute New Block Scales & Re-Quantize into int8 / uint8"]
        Dequant --> ComputeEMA --> DescentStep --> Requantize
    end

    Slicer --> BlockProcessing
    Requantize --> StoreRAM["Store Compact State in RAM (2.031 bytes/param)"]
```

---

## 7. ULC Dual-Evidence Finite State Machine

```mermaid
stateDiagram-v2
    [*] --> S0_STABLE

    S0_STABLE --> S1_WARNING : Delta_drift >= 0.50
    S0_STABLE --> S2_CONFIRMED_DRIFT : Delta_drift >= 1.0 AND R_bar >= tau_R
    S0_STABLE --> S3_NOISE_BURST : Delta_drift >= 1.0 AND R_bar < tau_R

    S1_WARNING --> S0_STABLE : Delta_drift < 0.35 (Hysteresis Exit)
    S1_WARNING --> S2_CONFIRMED_DRIFT : Delta_drift >= 1.0 AND R_bar >= tau_R
    S1_WARNING --> S3_NOISE_BURST : Delta_drift >= 1.0 AND R_bar < tau_R

    S2_CONFIRMED_DRIFT --> S4_RECOVERY : Issue Adapt Directives & Set Dwell Counter

    S3_NOISE_BURST --> S0_STABLE : R_bar >= tau_R AND Delta_drift < 0.50

    S4_RECOVERY --> S0_STABLE : Dwell Counter == 0 AND Delta_drift < 0.50
    S4_RECOVERY --> S4_RECOVERY : Decrement Dwell Counter
```

---

## 8. Cross-Pillar Coordination Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Pipeline as User Data Stream
    participant ULC as AdaptiveLearningController
    participant RLA as DensityAwareMarginScorer
    participant ALA as VectorizedHoeffdingTree
    participant ADWIN as ReliabilityWeightedADWIN
    participant RAO as LowMemoryAdamW

    Pipeline->>ULC: step(X, y)
    ULC->>RLA: score_samples(X, logits, y)
    RLA-->>ULC: return reliability vector r
    ULC->>ADWIN: update(window_loss, mean(r))
    ADWIN-->>ULC: return drift_detected, delta_drift
    ULC->>ULC: arbitrate_state(delta_drift, mean(r))
    alt Confirmed Drift State
        ULC->>ALA: accelerate_split() & purge_replay()
        ULC->>RAO: boost_lr(2.5x) & reset_momentum()
    else Noise Burst State
        ULC->>ALA: suppress_adwin_cut() & freeze_buffer()
        ULC->>RAO: clamp_gradients()
    end
    ULC->>ALA: partial_fit(X, y, sample_weight=r)
    ULC-->>Pipeline: return StepMetrics(state, delta_drift, mean_r)
```

---

## 9. Streaming Decision Tree Node Splitting Sequence

```mermaid
sequenceDiagram
    autonumber
    participant Engine as TreeEngine
    participant Leaf as LeafNode_u
    participant Stats as SufficientStatistics_Su
    participant Evaluator as SplitEvaluator

    Engine->>Leaf: update_batch(X_u, y_u)
    Leaf->>Stats: np.add.at(S_u, (j, bins, c), counts)
    Leaf->>Leaf: n_samples += B_u
    alt n_samples - last_check >= grace_period
        Leaf->>Evaluator: evaluate_candidate_splits(S_u)
        Evaluator-->>Leaf: return best_gain_1, best_gain_2, delta_G
        Leaf->>Leaf: compute Hoeffding epsilon_H
        alt delta_G > epsilon_H OR epsilon_H < tau_tie
            Leaf->>Engine: trigger_split(feat, threshold)
            Engine->>Engine: allocate ChildLeaf_L, ChildLeaf_R
            Engine->>Engine: replace LeafNode_u with SplitNode
        end
    end
```

---

## 10. Memory Layout & Cache Alignment Diagram

```mermaid
flowchart LR
    subgraph HostRAM ["Host System RAM"]
        ParamTensor["Parameter Vector theta (p elements x 4 bytes = 4p)"]
        QStateM["Quantized Momentum q_m (p elements x 1 byte = 1p)"]
        QStateV["Quantized Variance q_v (p elements x 1 byte = 1p)"]
        Scales["Block Scales (p / 256 blocks x 8 bytes = 0.031p)"]
    end

    subgraph CPUCache ["CPU L1 Data Cache (32 KB - 48 KB)"]
        BlockSlice["Active Block Slice (256 elements = 1024 bytes)"]
        ScratchM["Dequantized float32 m_block (1024 bytes)"]
        ScratchV["Dequantized float32 v_block (1024 bytes)"]
        ScratchG["Gradient float32 g_block (1024 bytes)"]
    end

    QStateM -->|"Load 256 bytes"| BlockSlice
    BlockSlice --> ScratchM
    ScratchM -->|"SIMD Arithmetic"| ScratchV
    ScratchV -->|"Vector Quantize"| BlockSlice
    BlockSlice -->|"Write back 256 bytes"| QStateM
```

---

## 11. Checkpoint & Serialization Protocol

```mermaid
flowchart TD
    Trigger["Save Checkpoint Request: model.save(path)"] --> ValidateDir["Ensure Output Directory Exists"]
    ValidateDir --> BuildMeta["Construct JSON Metadata (Topology, State, Config)"]
    BuildMeta --> WriteMeta["Atomically Write metadata.json.tmp -> metadata.json"]
    ValidateDir --> ExtractTensors["Extract Contiguous C-Order ndarrays"]
    ExtractTensors --> SafetensorsHeader["Generate 8-Byte Offset Header Table"]
    SafetensorsHeader --> WriteBinary["Write Raw Contiguous Tensor Buffers (tensors.safetensors)"]
    WriteBinary --> Finalize["Atomic Rename & Checksum Verification"]
    Finalize --> Success["Safe Checkpoint Complete (Zero Pickle Used)"]
```

---

## 12. Test Pyramid & Validation Flow

```mermaid
flowchart TD
    CodeCommit["Code / Algorithm Modification"] --> L1Tests["Layer 1: Unit & Numerical Gradient Tests (Tolerance <= 1e-5)"]
    L1Tests --> L2Tests["Layer 2: Property-Based Invariant Tests (Hypothesis 1000 iterations)"]
    L2Tests --> L3Tests["Layer 3: Scikit-Learn & PyTorch Integration Tests"]
    L3Tests --> L4Tests["Layer 4: 5-Seed Scientific Reproducibility Suite (Seeds: 42, 1337, 2024, 7, 999)"]
    L4Tests --> AuditPass["Automated Release Gate Passed (Zero Regressions)"]
```
