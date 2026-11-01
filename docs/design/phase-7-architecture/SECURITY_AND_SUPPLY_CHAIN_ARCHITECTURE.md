# AdaptiveML — Security & Supply Chain Architecture

> **Document Status**: Complete Baseline Deliverable (Phase 7)  
> **Document Identifier**: `DOC-DES-P7-010`  
> **Last Updated**: 2026-11-01  
> **Scope**: Local-first security boundaries, zero-telemetry enforcement, supply chain integrity, and clean-room IP  
> **Target Audience**: Security Engineers, Release Managers, Legal Counsel

---

## 1. Security Architecture Principles

AdaptiveML enforces four foundational security principles:
1. **Zero-Telemetry Boundary**: The library contains zero analytics, tracking, telemetry, or network-bound callouts. It is 100% air-gappable by design.
2. **Safe Deserialization**: Rejection of Python `pickle` on untrusted inputs, eliminating deserialization Remote Code Execution (RCE) vectors.
3. **Minimal Attack Surface**: The core runtime relies on a single external dependency (`numpy`), dramatically reducing supply-chain vulnerability exposure.
4. **Clean-Room IP Governance**: Strict adherence to the Apache-2.0 license, ensuring no code is derived or copy-pasted from copyleft (AGPL) libraries (such as Cleanlab).

---

## 2. Air-Gapped Zero-Telemetry Verification

AdaptiveML undergoes automated static analysis in continuous integration (CI) to verify zero network access:
- **Socket Prohibition**: Static AST scanning verifies that modules do not import `socket`, `urllib`, `requests`, `aiohttp`, or `httpx` in runtime packages.
- **Subprocess Lockdown**: Modules in `adaptive_ml/` are prohibited from invoking `subprocess`, `os.system`, or shell execution commands.
- **Air-Gapped Test Runner**: Test suites execute with simulated network disconnection (`--network-none` in container builds) to verify that zero tests or initializers attempt external connections.

---

## 3. Safe Deserialization Security Protocol

Model serialization vulnerabilities represent the primary threat vector in modern ML infrastructure. AdaptiveML mitigates this threat via the `Safetensors` standard:
1. **Header Length Enforcement**: Deserialization limits the metadata header to a maximum of 10 MB to prevent memory-exhaustion denial-of-service attacks.
2. **Memory Offset Validation**: Validates that all tensor byte offsets fall strictly within the physical bounds of the file, preventing out-of-bounds memory reads.
3. **Pure Numeric Array Storage**: Deserializes only fixed-type numerical arrays (`float32`, `int8`, `uint8`, `int64`), preventing arbitrary Python code execution.

---

## 4. Supply Chain Security & SBOM Generation

### 4.1 Dependency Locking & Vulnerability Auditing
- Production dependencies are pinned with SHA-256 integrity hashes using `uv` or `pip-compile --generate-hashes`.
- Continuous integration automatically runs `pip-audit` on every commit, blocking merges if any known Common Vulnerabilities and Exposures (CVEs) exist in the dependency tree.

### 4.2 Software Bill of Materials (SBOM)
- Every release artifact generates an automated CycloneDX (`sbom.json`) and SPDX (`sbom.spdx`) document.
- Cryptographically signed release hashes are published via Sigstore/cosign on GitHub Releases.

---

## 5. Clean-Room IP Governance Matrix

Following the findings of Phase 3 (`DOC-RES-P3-001` through `DOC-RES-P3-008`):
- All RLA algorithms (Margin Scoring, GCE, SCE, Class-Balanced Weights) are derived **clean-room from primary academic literature** (e.g., Wang et al., 2019; Zhang et al., 2018; Cui et al., 2019).
- Cleanlab code (licensed under AGPL-3.0) is quarantined; zero lines of code, variable identifiers, or internal architectures from Cleanlab are utilized.
- All original AdaptiveML code is published strictly under the **Apache License, Version 2.0**.
