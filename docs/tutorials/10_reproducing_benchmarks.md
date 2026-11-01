# Tutorial 10: Reproducing Benchmark Experiments

**Objective**: Execute the multi-seed benchmark suite locally, capture host hardware telemetry, and verify experimental claims.

---

## 1. Running the Complete Benchmark Suite

The complete benchmark harness is located in `benchmarks/phase-12/scripts/run_all_benchmarks.py`.

Execute the suite directly from terminal:

```bash
python benchmarks/phase-12/scripts/run_all_benchmarks.py
```

---

## 2. Benchmark Script Breakdown

The script sequentially runs all 4 benchmark pillars:
1. `benchmarks/phase-12/ala/benchmark_ala.py`: Evaluates `AdaptiveClassifier` across 4 SEA concepts and verifies drift adaptation vs static models.
2. `benchmarks/phase-12/rla/benchmark_rla.py`: Evaluates `RobustLearningPipeline` on clean, 20% noise, 40% noise, and 100:1 severe imbalance. Proves Theorem 2 ($60.0\%$ minority recall vs $0.0\%$ for CE).
3. `benchmarks/phase-12/rao/benchmark_rao.py`: Evaluates `LowMemoryAdamW` vs FP32 AdamW on parameter scales up to $10^6$ parameters, verifying $73.44\%$ state RAM reduction and convex convergence.
4. `benchmarks/phase-12/ulc/benchmark_ulc.py`: Evaluates multi-regime streaming arbitration under noise bursts and concept drift.

---

## 3. Inspecting the Results

All raw JSON telemetry and ASCII visualizations are automatically written to disk:
- Raw metrics: `benchmarks/phase-12/results/benchmark_results.json`
- Visualizations: `benchmarks/phase-12/plots/benchmark_visualizations.txt`
