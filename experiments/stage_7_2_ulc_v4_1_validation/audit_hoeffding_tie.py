"""
Stage 7.2 Workstream C: Hoeffding Tie-Breaking Mathematical & Empirical Audit
=============================================================================
Audits tau_tie in {0.00, 0.01, 0.05, 0.10, 0.15, 0.20, 0.30} on independent
validation streams. Measures tree depth, node count, split frequency, accuracy,
macro F1, minority recall, latency, and memory.
"""

from __future__ import annotations

import csv
import json
import time
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adaptive_ml.ala.tree import VectorizedHoeffdingTree, _SplitNode, _LeafNode
from adaptive_ml.ala.classifier import AdaptiveClassifier
from experiments.stage_7_ulc_v4.run_stage7_experiment import generate_stream, calculate_prequential_metrics


def get_tree_stats(node: Any) -> Tuple[int, int, int]:
    """Returns (max_depth, split_node_count, leaf_node_count)."""
    if isinstance(node, _LeafNode):
        return node.depth, 0, 1
    elif isinstance(node, _SplitNode):
        left_depth, left_splits, left_leaves = get_tree_stats(node.left_child)
        right_depth, right_splits, right_leaves = get_tree_stats(node.right_child)
        return max(left_depth, right_depth), 1 + left_splits + right_splits, left_leaves + right_leaves
    return 0, 0, 0


def run_hoeffding_trial(
    tau_tie: float,
    seed: int,
    grace_period: int = 10,
    n_batches: int = 60,
    batch_size: int = 30,
) -> Dict[str, Any]:
    stream = generate_stream(seed=seed, n_batches=n_batches, batch_size=batch_size)

    init_X = np.vstack([stream[i]["X"] for i in range(3)])
    init_y = np.concatenate([stream[i]["y_observed"] for i in range(3)])

    clf = AdaptiveClassifier(
        n_features=4,
        n_classes=2,
        grace_period=grace_period,
        tau_tie=tau_tie,
        replay_capacity=100,
        enable_drift_detection=True,
        random_state=seed,
    )
    clf.fit(init_X, init_y)

    all_y_clean: List[int] = []
    all_y_pred: List[int] = []
    split_count = 0

    t0 = time.perf_counter()
    for batch in stream[3:]:
        X_b, y_obs, y_clean = batch["X"], batch["y_observed"], batch["y_clean"]
        probs = clf.predict_proba(X_b)
        preds = np.argmax(probs, axis=1)
        all_y_clean.extend(y_clean.tolist())
        all_y_pred.extend(preds.tolist())

        # Measure splits before and after partial_fit
        if hasattr(clf._model, "root"):
            splits_before = get_tree_stats(clf._model.root)[1]
        else:
            splits_before = 0

        clf.partial_fit(X_b, y_obs)

        if hasattr(clf._model, "root"):
            splits_after = get_tree_stats(clf._model.root)[1]
            split_count += max(0, splits_after - splits_before)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    y_true_arr = np.array(all_y_clean)
    y_pred_arr = np.array(all_y_pred)
    acc, macro_f1, recall_min = calculate_prequential_metrics(y_true_arr, y_pred_arr)

    # Compute final tree structure
    if hasattr(clf._model, "root"):
        max_depth, n_splits, n_leaves = get_tree_stats(clf._model.root)
    else:
        max_depth, n_splits, n_leaves = 0, 0, 0

    total_nodes = n_splits + n_leaves

    # Memory approximation of tree
    approx_mem_bytes = total_nodes * 128 + n_leaves * (4 * 32 * 2 * 8)

    return {
        "tau_tie": tau_tie,
        "seed": seed,
        "accuracy": acc * 100.0,
        "macro_f1": macro_f1,
        "minority_recall": recall_min * 100.0,
        "max_depth": max_depth,
        "n_splits": n_splits,
        "n_leaves": n_leaves,
        "total_nodes": total_nodes,
        "split_frequency": split_count / max(1, n_batches - 3),
        "training_latency_ms": elapsed_ms,
        "approx_memory_kb": approx_mem_bytes / 1024.0,
    }


def main() -> None:
    print("=" * 80)
    print("STAGE 7.2 WORKSTREAM C: HOEFFDING TIE-BREAKING PARAMETER AUDIT")
    print("=" * 80)

    # Validation seeds strictly separate from confirmatory test seeds
    val_seeds = [1001, 1002, 1003, 1004, 1005]
    candidate_tau = [0.00, 0.01, 0.05, 0.10, 0.15, 0.20, 0.30]

    out_dir = Path(__file__).resolve().parent
    csv_path = out_dir / "HOEFFDING_EXPERIMENTS.csv"

    all_trials: List[Dict[str, Any]] = []

    for tau in candidate_tau:
        for seed in val_seeds:
            res = run_hoeffding_trial(tau_tie=tau, seed=seed)
            all_trials.append(res)

    # Save to CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "tau_tie", "seed", "accuracy", "macro_f1", "minority_recall",
            "max_depth", "n_splits", "n_leaves", "total_nodes",
            "split_frequency", "latency_ms", "approx_memory_kb"
        ])
        for r in all_trials:
            writer.writerow([
                f"{r['tau_tie']:.2f}", r["seed"], f"{r['accuracy']:.2f}",
                f"{r['macro_f1']:.4f}", f"{r['minority_recall']:.2f}",
                r["max_depth"], r["n_splits"], r["n_leaves"], r["total_nodes"],
                f"{r['split_frequency']:.4f}", f"{r['training_latency_ms']:.3f}",
                f"{r['approx_memory_kb']:.2f}"
            ])

    # Summary table
    print(f"\n{'tau_tie':8s} | {'Accuracy (%)':14s} | {'Macro F1':12s} | {'Min Recall (%)':15s} | {'Depth':6s} | {'Nodes':6s} | {'Splits':7s} | {'Lat (ms)':8s}")
    print("-" * 92)
    for tau in candidate_tau:
        tau_runs = [r for r in all_trials if abs(r["tau_tie"] - tau) < 1e-4]
        acc_m, acc_s = np.mean([r["accuracy"] for r in tau_runs]), np.std([r["accuracy"] for r in tau_runs])
        f1_m, f1_s = np.mean([r["macro_f1"] for r in tau_runs]), np.std([r["macro_f1"] for r in tau_runs])
        rec_m, rec_s = np.mean([r["minority_recall"] for r in tau_runs]), np.std([r["minority_recall"] for r in tau_runs])
        dep_m = np.mean([r["max_depth"] for r in tau_runs])
        nod_m = np.mean([r["total_nodes"] for r in tau_runs])
        spl_m = np.mean([r["n_splits"] for r in tau_runs])
        lat_m = np.mean([r["training_latency_ms"] for r in tau_runs])

        print(
            f"{tau:8.2f} | {acc_m:5.2f} ± {acc_s:4.2f}  | "
            f"{f1_m:5.4f} ± {f1_s:5.4f} | {rec_m:5.2f} ± {rec_s:4.2f}   | "
            f"{dep_m:5.1f}  | {nod_m:5.1f}  | {spl_m:5.1f}   | {lat_m:6.2f}"
        )

    print(f"\nSaved Hoeffding experiments to {csv_path}")


if __name__ == "__main__":
    main()

