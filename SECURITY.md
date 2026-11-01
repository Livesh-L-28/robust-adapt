# Security Policy

AdaptiveML takes the security and integrity of its machine learning algorithms and software supply chain seriously.

---

## 1. Supported Versions

Security updates are provided for the following releases:

| Version | Supported |
| :--- | :--- |
| `0.1.x` (Development / Pre-release) | :white_check_mark: |
| `< 0.1.0` | :x: |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability within AdaptiveML, please report it via private disclosure rather than opening a public issue.

**Reporting Channel:**  
Please send an email to `maintainers@adaptiveml.internal` with:
- A descriptive summary of the vulnerability.
- Steps to reproduce the issue, including proof-of-concept scripts or input streams.
- The affected component (`ala`, `rla`, `rao`, `ulc`, `state`, `integrations`).
- Potential impact and severity assessment.

You will receive an initial response acknowledging your report within 48 hours.

---

## 3. Security Philosophy & Hardening Standards

AdaptiveML incorporates strict local-first and CPU-first security design principles:

1. **Safe Serialization Only**:
   - Python's standard `pickle` module allows arbitrary code execution upon loading malicious byte streams. **AdaptiveML does not use `pickle` for model checkpointing or public data ingestion.**
   - All state serialization is performed using safe structured formats: **JSON** for hyperparameter configurations and **Safetensors** (`safetensors>=0.4.0`) for array/tensor weights.
2. **Zero Mandatory Telemetry**:
   - AdaptiveML contains **zero** tracking beacons, remote API pings, phone-home features, or automated data uploads.
   - All execution, logging, and diagnostics occur strictly on the local CPU host.
3. **No Dynamic Code Execution**:
   - The package strictly avoids `eval()`, `exec()`, or dynamic code compilation from user-controlled inputs.
4. **Supply Chain Integrity**:
   - Automated Static Application Security Testing (SAST) via **Bandit** in CI.
   - Software Bill of Materials (SBOM) published for all release builds.
