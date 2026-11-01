# ULC Known Limitations

**Document ID:** `ULC-LIM-001`  
**Phase:** Phase 11 — Unified Learning Controller (ULC)  
**Status:** READY FOR REVIEW  
**Module:** `adaptive_ml.ulc`

---

## 1. Architectural & Algorithmic Limitations

### 1.1 Fixed Arbitration Threshold ($\tau_R$)
- The current arbitration threshold $\tau_R$ (default $0.48 - 0.65$) is constant across data streams.
- If an entire dataset naturally has severe intrinsic label noise ($>40\%$ base noise), the static threshold may classify persistent background noise as continuous bursts.
- **Future Work**: Dynamic adaptive thresholding based on rolling historical reliability percentiles.

### 1.2 Binary Discrete State Space
- The 5 states are discrete operational modes.
- Continuous blending of drift adaptation and noise mitigation is not currently supported; the controller switches categorically between modes.

### 1.3 Latency on High-Dimensional Density Estimation
- When batch size $B$ or feature dimension $D$ is extremely large, nearest-neighbor distance computations for reliability estimation can increase controller latency.
- **Mitigation**: Downsampling or random projection approximations can be enabled for $D > 500$.

