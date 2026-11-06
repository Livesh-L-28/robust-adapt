# Security Architecture & Threat Model

**Document ID:** `docs/architecture/security-architecture.md`<br>
**Distribution Package:** `aml-core` v0.1.0.dev0<br>
**Security Posture:** Production Hardened, Zero-Pickle, Air-Gapped Compliant<br>

---

## 1. Security Threat Model & Boundaries

AdaptiveML is designed to execute in untrusted or multi-tenant production environments, including cloud microservices, edge edge devices, and regulated on-premise infrastructure.

```mermaid
graph TD
    subgraph Untrusted Inputs
        RAW[Streaming Data Inputs]
        CKPT[Serialized Checkpoint Files]
        KEYS[Environment Configurations]
    end

    subgraph Security Boundaries
        VAL[Input Validation: NaN/Inf & Shape Check]
        HMAC[Cryptographic HMAC-SHA256 & Ceiling Check]
        CONF[Configuration Range & Type Verification]
    end

    subgraph Hardened Core
        CORE[Safe Execution Engine (Zero-Pickle, O(1) Memory)]
        PRIV[Zero-PII Aggregated Diagnostics Sink]
    end

    RAW --> VAL --> CORE
    CKPT --> HMAC --> CORE
    KEYS --> CONF --> CORE
    CORE --> PRIV
```

---

## 2. Zero-Pickle Policy (CWE-502 Mitigation)

### Threat
Python's standard `pickle` and `torch.save(..., pickle_module=pickle)` deserialize arbitrary Python bytecodes. An adversary with write access to model storage can construct a malicious payload that executes arbitrary operating system commands upon model loading (`os.system`, `subprocess.Popen`).

### Mitigation
- **Mandatory SafeTensors Serialization:** AdaptiveML completely rejects `pickle` for model weights, using the HuggingFace SafeTensors binary tensor format.
- **Header Parsing Security:** SafeTensors headers are constrained JSON metadata strings with explicit size offsets. Raw buffers are directly memory-mapped with zero bytecode execution pathways.
- **Repository-Wide Ban:** Internal AST linters verify that `pickle.load` and `pickle.loads` are never invoked anywhere in `adaptive_ml`.

---

## 3. Cryptographic Tamper-Proofing (HMAC-SHA256)

### Threat
An adversary with file system access alters stored model weights or decision thresholds (e.g., lowering a fraud detection threshold to allow illicit transactions).

### Mitigation
- **Cryptographic Checksums:** Every saved file automatically generates an unambiguous SHA-256 digest recorded in `.meta.json`.
- **HMAC Signatures:** Production deployments can pass a secret byte string `auth_key` ($\ge 16$ bytes). The signature is computed via:
  $$\text{HMAC-SHA256}(K, \text{tensor\_bytes})$$
- **Constant-Time Verification:** When loading state with `auth_key`, the key is verified using constant-time comparison (`hmac.compare_digest`) to prevent timing side-channel attacks. Any tampering immediately halts execution with a typed `SerializationError`.

---

## 4. Resource Exhaustion & DoS Defenses (CWE-400 Mitigation)

### Threat
An attacker submits an oversized state file or decompression bomb, causing the application to allocate gigabytes of heap memory and triggering kernel Out-Of-Memory (OOM) killer terminations.

### Mitigation
- **Tensor File Ceiling:** `load_state` inspects file sizes via OS metadata *before* reading contents, enforcing an immutable default ceiling of $5\text{ GB}$ (configurable).
- **Metadata JSON Ceiling:** Companion `.meta.json` files are constrained to a strict $64\text{ MB}$ ceiling.
- **Bounded In-Memory Diagnostics:** `DiagnosticRegistry` maintains an immutable FIFO ring-buffer (`maxlen=1000` default) with thread-safe lock synchronization, ensuring logging never leaks memory.

---

## 5. Zero-PII Privacy & Air-Gap Compliance

### Principles
- **No Data Leakage:** Diagnostic logs and telemetry dictionaries record only aggregated mathematical scalars (mean error rate, step latency in ms, norm of gradients, tier enum names).
- **No Raw Feature Buffers:** Input feature rows and raw labels are never forwarded into diagnostic events or error tracebacks.
- **No Telemetry Sockets:** AdaptiveML contains zero outbound network requests, phone-home telemetry, or external analytics pings. It is $100\%$ air-gapped and offline-compliant.
