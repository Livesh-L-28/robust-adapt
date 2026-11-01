# Phase 12 Reproducibility Report

**Document ID:** `DOC-RES-P12-009`  
**Phase:** Phase 12 — Research Experiments & Benchmarking  
**Status:** READY FOR REVIEW  

---

## 1. Reproduction Package Instructions

All benchmarks can be reproduced on any standard Windows, Linux, or macOS workstation with Python 3.10+ and standard dependencies:

```bash
# 1. Install editable repository dependencies
pip install -e .

# 2. Run the complete master benchmark suite
python benchmarks/phase-12/scripts/run_all_benchmarks.py

# 3. Or run individual pillar benchmarks
python benchmarks/phase-12/ala/benchmark_ala.py
python benchmarks/phase-12/rla/benchmark_rla.py
python benchmarks/phase-12/rao/benchmark_rao.py
python benchmarks/phase-12/ulc/benchmark_ulc.py
```

---

## 2. Preserved Artifacts

- **Raw Results File:** [`benchmarks/phase-12/results/benchmark_results.json`](file:///c:/projects/AdaptiveML/benchmarks/phase-12/results/benchmark_results.json)
- **ASCII Visualizations:** [`benchmarks/phase-12/plots/benchmark_visualizations.txt`](file:///c:/projects/AdaptiveML/benchmarks/phase-12/plots/benchmark_visualizations.txt)
- **Dataset Generators:** [`benchmarks/phase-12/datasets/generators.py`](file:///c:/projects/AdaptiveML/benchmarks/phase-12/datasets/generators.py)
