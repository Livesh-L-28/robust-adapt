# Supported Environments & Compatibility Matrix

ROBUST-ADAPT is designed for portability across standard platforms, Python versions, and ecosystem libraries.

---

## Operating System Matrix

| Operating System | Architecture | Support Tier | Validation Status |
| :--- | :--- | :--- | :--- |
| **Ubuntu Linux 22.04 / 24.04** | x86_64 | Tier 1 (Primary) | Fully verified in CI matrix |
| **Windows 10 / 11** | x86_64 | Tier 1 (Primary) | Fully verified on local host & CI |
| **macOS 13 / 14 / 15** | ARM64 (Apple Silicon) & x86_64 | Tier 1 (Primary) | Fully verified in CI matrix |
| **Debian / RHEL / Alpine** | x86_64 | Tier 2 (Compatible) | Standard pure-Python execution |

---

## Python Version Compatibility

| Python Version | Status | Notes |
| :--- | :--- | :--- |
| **Python 3.10** | Supported | Verified baseline version |
| **Python 3.11** | Supported | Production recommended |
| **Python 3.12** | Supported | Production recommended |
| **Python 3.13** | Supported | Verified |
| **Python 3.14** | Supported | Verified on local host (`Python 3.14.3`) |
| **Python < 3.10** | Unsupported | End-of-life upstream; missing modern typing syntax |

---

## Ecosystem Integration Matrix

| Framework | Version Range | Module in ROBUST-ADAPT | Validation Status |
| :--- | :--- | :--- | :--- |
| **NumPy** | `>= 1.24.0, <= 2.4.x` | `robust_adapt.backends.numpy_backend` | Mandatory core dependency (100% verified) |
| **Scikit-learn** | `>= 1.2.0, <= 1.8.x` | `robust_adapt.integrations.sklearn` | Optional adapter (3/3 integration tests passing) |
| **PyTorch** | `>= 2.0.0, <= 2.12.x` | `robust_adapt.integrations.torch_optim`, `torch_module` | Optional adapter (2/2 integration tests passing) |
| **SafeTensors** | `>= 0.4.0` | `robust_adapt.state.serializer` | Optional safe binary serialization |
