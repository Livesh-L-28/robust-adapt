"""
Stage 12 — Workstream G: Controlled Ablation Studies Benchmark.

Isolates individual architectural mechanisms across all four pillars and ULC:
1. ALA 3.0 Ablations:
   - ala_full: Complete ALA 3.0 (Fingerprint + Recurring Memory + Cooldown)
   - ala_no_memory: Ablates Concept Memory (forces blind reset upon drift)
   - ala_no_cooldown: Ablates Cooldown (cooldown_steps = 0)
2. Minority 2.0 Ablations:
   - min_full: Complete Minority 2.0 (PID FP Budget + Sublinear Cost + Beta Prior)
   - min_no_budget: Ablates Dynamic Budget (fixed threshold = 0.50)
   - min_linear_cost: Ablates Sublinear Cost (uses brute 556:1 linear cost)
3. RAO 2.0 Ablations:
   - rao_full: Complete RAO 2.0 (Vectorized + 1D float32 + gradient clipping + clamped denom)
   - rao_unclamped_denom: Ablates Clamped Denominator (eps=1e-8)
4. ULC-v5 Ablations:
   - ulc_v5_full: Complete ULC-v5 (Multi-Tier Utility + Memory + Cooldown)
   - ulc_v5_no_utility: Ablates Utility Scoring (always executes hard structural reset)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

from experiments.stage_12.ala_3_0.recurrent_ala import ALA30AdaptiveLearner
from experiments.stage_12.minority_2_0.calibrated_minority import MinorityIntelligence20Learner
from experiments.stage_12.ulc_v5.calibrated_ulc_v5 import UnifiedLearningControllerV5

SEEDS = [42, 101, 202, 303, 404]
BATCH_SIZE = 50


def run_ala_ablation(variant: str, X: np.ndarray, y: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_batches = len(X) // BATCH_SIZE
    y_true, y_pred = [], []

    if variant == "ala_full":
        learner = ALA30AdaptiveLearner(n_features=X.shape[1], n_classes=2, similarity_threshold=0.82, cooldown_steps=5, max_concepts=5)
    elif variant == "ala_no_memory":
        # Disables concept memory matching (threshold > 1.0 ensures no match)
        learner = ALA30AdaptiveLearner(n_features=X.shape[1], n_classes=2, similarity_threshold=2.0, cooldown_steps=5, max_concepts=0)
    elif variant == "ala_no_cooldown":
        # Cooldown = 0
        learner = ALA30AdaptiveLearner(n_features=X.shape[1], n_classes=2, similarity_threshold=0.82, cooldown_steps=0, max_concepts=5)
    else:
        raise ValueError(variant)

    t0 = time.perf_counter()
    for b in range(n_batches):
        X_b, y_b = X[b*BATCH_SIZE:(b+1)*BATCH_SIZE], y[b*BATCH_SIZE:(b+1)*BATCH_SIZE]
        probas = learner.predict_proba(X_b)
        y_pred.extend(np.argmax(probas, axis=1).tolist())
        y_true.extend(y_b.tolist())
        learner.update(X_b, y_b)
    t_tot = time.perf_counter() - t0

    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, average="macro"))

    return {
        "pillar": "ALA_3_0",
        "variant": variant,
        "seed": seed,
        "primary_metric": acc,
        "macro_f1": f1,
        "resets": learner.drift_resets,
        "restores": learner.recurring_restorations,
        "total_time_sec": t_tot,
    }


def run_minority_ablation(variant: str, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_batches = int(np.ceil(len(X_train) / 500))

    if variant == "min_full":
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5, sublinear_cost_power=0.52)
        learner.threshold_mgr.max_threshold = 0.65
    elif variant == "min_no_budget":
        # Fixed threshold = 0.50
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5, sublinear_cost_power=0.52)
        learner.threshold_mgr.threshold = 0.50
        learner.threshold_mgr.step = lambda y_b, p_b: 0.50
    elif variant == "min_linear_cost":
        # Linear cost power = 1.0 (556:1)
        learner = MinorityIntelligence20Learner(target_fp_budget_per_1k=1.5, sublinear_cost_power=1.0)
        learner.threshold_mgr.max_threshold = 0.65
    else:
        raise ValueError(variant)

    t0 = time.perf_counter()
    for b in range(n_batches):
        idx_start = b * 500
        idx_end = min(idx_start + 500, len(X_train))
        learner.fit_batch(X_train[idx_start:idx_end], y_train[idx_start:idx_end])
    t_tot = time.perf_counter() - t0

    preds = learner.predict(X_test)
    rec = float(recall_score(y_test, preds, pos_label=1))
    prec = float(precision_score(y_test, preds, pos_label=1, zero_division=0))
    f1 = float(f1_score(y_test, preds, pos_label=1))
    cm = confusion_matrix(y_test, preds)

    return {
        "pillar": "Minority_2_0",
        "variant": variant,
        "seed": seed,
        "primary_metric": rec,
        "precision": prec,
        "minority_f1": f1,
        "false_positives": int(cm[0, 1]),
        "total_time_sec": t_tot,
    }


def run_ulc_ablation(variant: str, X: np.ndarray, y: np.ndarray, seed: int) -> Dict[str, Any]:
    np.random.seed(seed)
    n_batches = len(X) // BATCH_SIZE
    y_true, y_pred = [], []

    controller = UnifiedLearningControllerV5(n_features=X.shape[1], n_classes=2, similarity_threshold=0.82)
    if variant == "ulc_v5_no_utility":
        # Disable utility damping: always execute soft reset upon drift
        from experiments.stage_12.ulc_v5.calibrated_ulc_v5 import InterventionTier
        orig_step = controller.step

        def modified_step(X_b, y_b):
            directive, tel = orig_step(X_b, y_b)
            # If damping was selected, override with reset
            if directive.tier == InterventionTier.TIER_1_PARAM_DAMPING:
                controller.classifier = type(controller.classifier)(
                    n_features=controller.n_features, n_classes=controller.n_classes,
                    grace_period=controller.grace_period, delta=controller.delta
                )
                controller.total_resets += 1
            return directive, tel

        controller.step = modified_step

    t0 = time.perf_counter()
    for b in range(n_batches):
        X_b, y_b = X[b*BATCH_SIZE:(b+1)*BATCH_SIZE], y[b*BATCH_SIZE:(b+1)*BATCH_SIZE]
        probas = controller.predict_proba(X_b)
        y_pred.extend(np.argmax(probas, axis=1).tolist())
        y_true.extend(y_b.tolist())
        controller.step(X_b, y_b)
    t_tot = time.perf_counter() - t0

    acc = float(accuracy_score(y_true, y_pred))
    f1 = float(f1_score(y_true, y_pred, average="macro"))

    return {
        "pillar": "ULC_v5",
        "variant": variant,
        "seed": seed,
        "primary_metric": acc,
        "macro_f1": f1,
        "resets": controller.total_resets,
        "restores": controller.total_restores,
        "total_time_sec": t_tot,
    }


def run_rao_ablation(variant: str, seed: int) -> Dict[str, Any]:
    import torch
    import torch.nn as nn
    from experiments.stage_12.rao_2_0.run_rao_2_0_covertype_experiment import CoverTypeMLP
    from experiments.stage_12.rao_2_0.vectorized_adamw import VectorizedLowMemoryAdamW

    torch.manual_seed(seed)
    np.random.seed(seed)

    model = CoverTypeMLP(in_features=54, n_classes=7)
    criterion = nn.CrossEntropyLoss()

    if variant == "rao_full":
        optimizer = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-3, eps=1e-4)
    elif variant == "rao_small_eps":
        optimizer = VectorizedLowMemoryAdamW(model.parameters(), lr=1e-3, eps=1e-8)
    else:
        raise ValueError(variant)

    # Run 100 synthetic steps to test numerical stability and final loss
    losses = []
    t0 = time.perf_counter()
    for _ in range(100):
        x = torch.randn(128, 54)
        y = torch.randint(0, 7, (128,))
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    t_tot = time.perf_counter() - t0

    final_loss = float(losses[-1])
    is_diverged = bool(np.isnan(final_loss) or final_loss > 10.0)

    return {
        "pillar": "RAO_2_0",
        "variant": variant,
        "seed": seed,
        "primary_metric": final_loss,
        "diverged": is_diverged,
        "final_loss": final_loss,
        "total_time_sec": t_tot,
    }


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 12: Workstream G — Controlled Ablation Benchmark")
    print("=====================================================================")

    all_results = []

    # 1. Load Electricity for ALA and ULC ablations
    df_elec = pd.read_csv("experiments/stage_11/datasets/electricity.csv.gz")
    f_cols_e = [c for c in df_elec.columns if c not in ["class", "target"]]
    X_elec = StandardScaler().fit_transform(df_elec[f_cols_e].values)
    y_elec = df_elec["target"].values

    # 2. Load Credit Card for Minority ablations
    df_cc = pd.read_csv("experiments/stage_11/datasets/creditcard.csv.gz")
    f_cols_c = [c for c in df_cc.columns if c not in ["Time", "Class", "target"]]
    X_cc = StandardScaler().fit_transform(df_cc[f_cols_c].values)
    y_cc = df_cc["target"].values
    X_cc_tr, y_cc_tr = X_cc[:180000], y_cc[:180000]
    X_cc_te, y_cc_te = X_cc[180000:], y_cc[180000:]

    # ALA Ablations
    print("\nEvaluating ALA 3.0 Ablations...")
    for var in ["ala_full", "ala_no_memory", "ala_no_cooldown"]:
        for s in SEEDS:
            r = run_ala_ablation(var, X_elec, y_elec, s)
            all_results.append(r)
        sub = [x for x in all_results if x.get("variant") == var]
        print(f"  {var:18s} | Acc: {np.mean([x['primary_metric'] for x in sub])*100:.2f}% | Mean Resets: {np.mean([x['resets'] for x in sub]):.1f}")

    # Minority Ablations
    print("\nEvaluating Minority 2.0 Ablations...")
    for var in ["min_full", "min_no_budget", "min_linear_cost"]:
        for s in SEEDS:
            r = run_minority_ablation(var, X_cc_tr, y_cc_tr, X_cc_te, y_cc_te, s)
            all_results.append(r)
        sub = [x for x in all_results if x.get("variant") == var]
        print(f"  {var:18s} | Recall: {np.mean([x['primary_metric'] for x in sub])*100:.2f}% | Mean FP: {np.mean([x['false_positives'] for x in sub]):.1f}")

    # ULC Ablations
    print("\nEvaluating ULC-v5 Ablations...")
    for var in ["ulc_v5_full", "ulc_v5_no_utility"]:
        for s in SEEDS:
            r = run_ulc_ablation(var, X_elec, y_elec, s)
            all_results.append(r)
        sub = [x for x in all_results if x.get("variant") == var]
        print(f"  {var:18s} | Acc: {np.mean([x['primary_metric'] for x in sub])*100:.2f}% | Mean Resets: {np.mean([x['resets'] for x in sub]):.1f}")

    # RAO Ablations
    print("\nEvaluating RAO 2.0 Ablations...")
    for var in ["rao_full", "rao_small_eps"]:
        for s in SEEDS:
            r = run_rao_ablation(var, s)
            all_results.append(r)
        sub = [x for x in all_results if x.get("variant") == var]
        print(f"  {var:18s} | Final Loss: {np.mean([x['final_loss'] for x in sub]):.4f} | Diverged: {any(x['diverged'] for x in sub)}")

    out_dir = Path("experiments/stage_12/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "ablation_results.json"
    out_csv = out_dir / "ablation_results.csv"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nAll Ablation results successfully saved to {out_json} and {out_csv}")


if __name__ == "__main__":
    main()
