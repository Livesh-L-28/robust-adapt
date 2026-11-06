# Security Policy & Vulnerability Disclosure

**Document ID:** `docs/community/security.md`<br>
**Distribution Package:** `aml-core` v0.1.0.dev0<br>
**Import Namespace:** `adaptive_ml`<br>

AdaptiveML takes the security of its machine learning runtime and state serialization engine seriously. We appreciate responsible disclosure of security vulnerabilities.

---

## 1. Supported Versions

We provide security patches and vulnerability evaluations for the following distribution versions:

| Version | Supported | Status |
| :--- | :---: | :--- |
| `0.1.0.dev0` (current development baseline) | Yes | Active Security Hardening |
| `< 0.1.0` | No | Experimental Prototypes |

---

## 2. Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you believe you have discovered a security vulnerability in AdaptiveML, please report it privately via email:

- **Security Team Email:** `security@adaptiveml.internal`
- **PGP Encryption:** Available upon request.

Please include:
1. A detailed description of the vulnerability and its potential impact.
2. A minimal, self-contained Python reproduction script demonstrating the issue.
3. Relevant environment information (OS, Python version, installed extras).

---

## 3. Response Process & SLA

1. **Initial Acknowledgment:** Within 48 hours of receiving your disclosure.
2. **Triaging & Severity Assessment:** Within 5 business days, evaluating CVSS score.
3. **Patch Development:** A private patch will be prepared and tested across all supported Python versions (3.10–3.14).
4. **Coordinated Disclosure:** We adhere to a 90-day coordinated vulnerability disclosure policy before public publication of advisory notes and CVE numbers.

---

## 4. Key Security Invariants

When evaluating vulnerabilities, please note the following explicit security invariants enforced by AdaptiveML:
- **Zero-Pickle Rule:** The use of Python's standard `pickle` for model weight deserialization is classified as an automatic high-severity defect.
- **Denial-of-Service Size Ceilings:** State loading functions enforce a strict $5\text{ GB}$ ceiling on tensor files and a $64\text{ MB}$ ceiling on JSON metadata.
- **Cryptographic Signatures:** Deserialization with an `auth_key` must strictly reject tampered files via constant-time comparison (`hmac.compare_digest`).
