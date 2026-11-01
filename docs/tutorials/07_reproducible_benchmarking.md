# Tutorial 7: Reproducible Benchmarking

Learn how to run and verify AdaptiveML's automated empirical benchmark suite.

---

## 1. Running the Complete Benchmark Suite

AdaptiveML includes an automated multi-seed benchmark runner that evaluates all four pillars (ALA, RLA, RAO, ULC) and captures host hardware telemetry:

```bash
python benchmarks/phase-12/scripts/run_all_benchmarks.py
```

---

## 2. Running Individual Benchmarks

```bash
# ALA: SEA concept drift & false alarm resistance
python benchmarks/phase-12/ala/benchmark_ala.py

# RLA: Label noise rates & 100:1 extreme class imbalance
python benchmarks/phase-12/rla/benchmark_rla.py

# RAO: State memory footprint & convergence scaling
python benchmarks/phase-12/rao/benchmark_rao.py

# ULC: In-loop cross-pillar arbitration & noise filtering
python benchmarks/phase-12/ulc/benchmark_ulc.py
```

---

## 3. Benchmark Artifacts

- **Raw JSON Results:** `benchmarks/phase-12/results/benchmark_results.json`
- **ASCII Visualizations:** `benchmarks/phase-12/plots/benchmark_visualizations.txt`
