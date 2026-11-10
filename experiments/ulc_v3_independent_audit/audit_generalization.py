"""
Comprehensive Generalization Experiment Suite for ULC-v3 Audit.
Evaluates across drift types, noise models, severe class imbalances,
resource dimensions, and realistic streaming domains (Fraud, Predictive Maintenance).
"""

import json
import os
import sys
import time
import numpy as np
from sklearn.metrics import f1_score, accuracy_score, recall_score, precision_score, brier_score_loss

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from experiments.four_pillar_validation_v2.run_experiments import (
    ParamWrapper,
    AdaptiveClassifier,
    LowMemoryAdamW,
    RobustLearningPipeline,
    AdaptiveLearningController,
    ControllerState
)

def run_stream_benchmark(
    stream_generator_fn,
    n_batches=50,
    batch_size=30,
    n_features=4,
    seeds=[42, 101, 2024],
    models=["Static_Baseline", "ALA_Only", "Uncoordinated_Three_Pillars", "Full_ULC_v1", "MultiObjective_ULC_v3"]
):
    results = {m: [] for m in models}
    
    for seed in seeds:
        stream = stream_generator_fn(seed=seed, n_batches=n_batches, batch_size=batch_size, n_features=n_features)
        
        for m in models:
            clf = AdaptiveClassifier(n_features=n_features, n_classes=2, grace_period=20,
                                     enable_drift_detection=True, random_state=seed)
            pipeline = RobustLearningPipeline(n_classes=2)
            p_wrapper = ParamWrapper(np.random.RandomState(seed).randn(n_features, 2) * 0.01)
            opt = LowMemoryAdamW([p_wrapper], lr=0.01)
            controller = AdaptiveLearningController(classifier=clf, pipeline=pipeline, optimizer=opt)
            
            all_y_true = []
            all_y_pred = []
            all_y_prob = []
            false_resets = 0
            
            for b_idx, batch in enumerate(stream, start=1):
                X_b = batch["X"]
                y_obs = batch["y_observed"]
                y_clean = batch["y_clean"]
                delta = batch.get("delta", 0.0)
                is_noise = batch.get("is_noise_burst", False)
                
                # Model inference
                if m == "Static_Baseline":
                    if b_idx == 1:
                        clf.partial_fit(X_b, y_clean)
                    p_pred = clf.predict(X_b)
                    p_prob = clf.predict_proba(X_b)
                    
                elif m == "ALA_Only":
                    if clf.samples_seen_ > 0:
                        p_pred = clf.predict(X_b)
                        p_prob = clf.predict_proba(X_b)
                    else:
                        p_pred = np.zeros(len(X_b), dtype=np.int64)
                        p_prob = np.zeros((len(X_b), 2)) + 0.5
                    clf.partial_fit(X_b, y_obs)
                    if is_noise and getattr(clf, "drift_detected_", False):
                        false_resets += 1
                        
                elif m == "Uncoordinated_Three_Pillars":
                    if clf.samples_seen_ > 0:
                        p_pred = clf.predict(X_b)
                        p_prob = clf.predict_proba(X_b)
                    else:
                        p_pred = np.zeros(len(X_b), dtype=np.int64)
                        p_prob = np.zeros((len(X_b), 2)) + 0.5
                    clf.partial_fit(X_b, y_obs)
                    if is_noise and getattr(clf, "drift_detected_", False):
                        false_resets += 1
                    logits = X_b @ p_wrapper.data
                    p_lin = np.exp(logits - np.max(logits, axis=1, keepdims=True))
                    p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                    p_wrapper.grad = (X_b.T @ (p_lin - np.eye(2)[y_obs])) / len(y_obs)
                    opt.step()
                    
                elif m == "Full_ULC_v1":
                    if clf.samples_seen_ > 0:
                        p_pred = clf.predict(X_b)
                        p_prob = clf.predict_proba(X_b)
                    else:
                        p_pred = np.zeros(len(X_b), dtype=np.int64)
                        p_prob = np.zeros((len(X_b), 2)) + 0.5
                    logits = X_b @ p_wrapper.data
                    directive, info = controller.step(X_b, y_obs, logits=logits, delta_drift=delta)
                    if is_noise and directive.state == ControllerState.CONFIRMED_DRIFT:
                        false_resets += 1
                        
                elif m == "MultiObjective_ULC_v3":
                    if clf.samples_seen_ > 0:
                        p_tree = clf.predict_proba(X_b)
                    else:
                        p_tree = np.zeros((len(X_b), 2)) + 0.5
                    logits_lin = X_b @ p_wrapper.data
                    p_lin = np.exp(logits_lin - np.max(logits_lin, axis=1, keepdims=True))
                    p_lin /= np.sum(p_lin, axis=1, keepdims=True)
                    p_ens = 0.50 * p_tree + 0.50 * p_lin
                    p_pred = np.argmax(p_ens, axis=1)
                    p_prob = p_ens
                    
                    logits_aligned = np.log(np.clip(p_tree, 1e-12, 1.0))
                    directive, info = controller.step(X_b, y_obs, logits=logits_aligned, delta_drift=delta)
                    if directive.purge_replay and hasattr(clf, "_replay_buffer") and clf._replay_buffer is not None:
                        clf._replay_buffer.clear()
                    if directive.state == ControllerState.CONFIRMED_DRIFT:
                        if is_noise:
                            false_resets += 1
                        clf.reset()
                        opt.state.clear()
                    if directive.state == ControllerState.NOISE_BURST:
                        weights = np.where(info["mean_reliability"] >= 0.45, 1.0, 0.2)
                    else:
                        weights = 1.0
                    p_wrapper.grad = ((X_b.T @ (p_lin - np.eye(2)[y_obs])) * weights) / len(y_obs)
                    opt.step()
                    
                if b_idx > 1:
                    all_y_true.extend(y_clean.tolist())
                    all_y_pred.extend(p_pred.tolist())
                    all_y_prob.extend(p_prob[:, 1].tolist() if p_prob.ndim == 2 else p_prob.tolist())
                    
            y_t = np.array(all_y_true)
            y_p = np.array(all_y_pred)
            y_pr = np.array(all_y_prob)
            
            results[m].append({
                "accuracy": float(accuracy_score(y_t, y_p)),
                "macro_f1": float(f1_score(y_t, y_p, average="macro", zero_division=0)),
                "minority_recall": float(recall_score(y_t, y_p, pos_label=1, zero_division=0)),
                "minority_f1": float(f1_score(y_t, y_p, pos_label=1, zero_division=0)),
                "brier_score": float(brier_score_loss(y_t, np.clip(y_pr, 0.0, 1.0))),
                "false_resets": false_resets
            })
            
    summary = {}
    for m in models:
        summary[m] = {
            "accuracy": float(np.mean([x["accuracy"] for x in results[m]])),
            "macro_f1": float(np.mean([x["macro_f1"] for x in results[m]])),
            "minority_recall": float(np.mean([x["minority_recall"] for x in results[m]])),
            "minority_f1": float(np.mean([x["minority_f1"] for x in results[m]])),
            "brier_score": float(np.mean([x["brier_score"] for x in results[m]])),
            "false_resets": float(np.mean([x["false_resets"] for x in results[m]]))
        }
    return summary


# --- STREAM GENERATORS ---

def gen_drift_stream(drift_type="abrupt", seed=42, n_batches=50, batch_size=30, n_features=4):
    rng = np.random.RandomState(seed)
    stream = []
    
    mu_0 = np.zeros(n_features)
    mu_1 = np.ones(n_features) * 2.0
    
    for b in range(1, n_batches + 1):
        if drift_type == "abrupt":
            if b > 25:
                # Invert classes
                cur_mu0 = np.ones(n_features) * 2.0
                cur_mu1 = np.zeros(n_features)
                delta = 1.5
            else:
                cur_mu0, cur_mu1, delta = mu_0, mu_1, 0.0
        elif drift_type == "gradual":
            # Shift centroid gradually between batch 20 and 40
            alpha = np.clip((b - 20) / 20.0, 0.0, 1.0)
            cur_mu0 = (1 - alpha) * mu_0 + alpha * (np.ones(n_features) * 2.0)
            cur_mu1 = (1 - alpha) * mu_1 + alpha * np.zeros(n_features)
            delta = float(alpha * 1.5)
        elif drift_type == "incremental":
            # Slow step by step drift
            shift = (b / float(n_batches)) * 1.5
            cur_mu0 = mu_0 + shift
            cur_mu1 = mu_1 - shift
            delta = float(shift)
        elif drift_type == "recurring":
            # Concept A (1-15) -> Concept B (16-35) -> Concept A (36-50)
            if 16 <= b <= 35:
                cur_mu0 = np.ones(n_features) * 2.0
                cur_mu1 = np.zeros(n_features)
                delta = 1.5
            else:
                cur_mu0, cur_mu1, delta = mu_0, mu_1, 0.0
        elif drift_type == "feature_level":
            # Only features 0 and 1 drift; 2 and 3 remain stationary
            cur_mu0 = mu_0.copy()
            cur_mu1 = mu_1.copy()
            if b > 25:
                cur_mu0[:2] = 2.0
                cur_mu1[:2] = 0.0
                delta = 1.0
            else:
                delta = 0.0
                
        # Generate samples: 90:10 imbalance
        n_min = int(0.10 * batch_size)
        n_maj = batch_size - n_min
        
        X_maj = rng.randn(n_maj, n_features) + cur_mu0
        y_maj = np.zeros(n_maj, dtype=np.int64)
        X_min = rng.randn(n_min, n_features) + cur_mu1
        y_min = np.ones(n_min, dtype=np.int64)
        
        X = np.vstack([X_maj, X_min])
        y = np.concatenate([y_maj, y_min])
        perm = rng.permutation(batch_size)
        
        stream.append({
            "batch_idx": b,
            "X": X[perm],
            "y_observed": y[perm],
            "y_clean": y[perm],
            "delta": delta,
            "is_noise_burst": False,
            "is_true_drift": delta > 0.5
        })
    return stream


def gen_noise_stream(noise_type="symmetric", seed=42, n_batches=50, batch_size=30, n_features=4):
    rng = np.random.RandomState(seed)
    stream = []
    mu_0 = np.zeros(n_features)
    mu_1 = np.ones(n_features) * 2.0
    
    for b in range(1, n_batches + 1):
        n_min = int(0.10 * batch_size)
        n_maj = batch_size - n_min
        X = np.vstack([rng.randn(n_maj, n_features) + mu_0, rng.randn(n_min, n_features) + mu_1])
        y = np.concatenate([np.zeros(n_maj, dtype=np.int64), np.ones(n_min, dtype=np.int64)])
        perm = rng.permutation(batch_size)
        X, y = X[perm], y[perm]
        
        y_obs = y.copy()
        is_noise_burst = False
        
        if noise_type == "symmetric":
            # 20% random label noise
            flip_mask = rng.rand(batch_size) < 0.20
            y_obs[flip_mask] = 1 - y_obs[flip_mask]
        elif noise_type == "asymmetric":
            # Class 1 -> 0 with p=0.30, Class 0 -> 1 with p=0.05
            for i in range(batch_size):
                if y[i] == 1 and rng.rand() < 0.30:
                    y_obs[i] = 0
                elif y[i] == 0 and rng.rand() < 0.05:
                    y_obs[i] = 1
        elif noise_type == "instance_dependent":
            # Points near margin have higher flip prob
            dist = np.abs(np.mean(X - 1.0, axis=1))
            flip_prob = np.clip(0.40 - 0.20 * dist, 0.05, 0.50)
            flip_mask = rng.rand(batch_size) < flip_prob
            y_obs[flip_mask] = 1 - y_obs[flip_mask]
        elif noise_type == "noise_burst":
            # Heavy noise burst in batches 16-25 (40% feature perturbation)
            if 16 <= b <= 25:
                X += rng.randn(*X.shape) * 2.5
                is_noise_burst = True
                
        stream.append({
            "batch_idx": b,
            "X": X,
            "y_observed": y_obs,
            "y_clean": y,
            "delta": 0.0,
            "is_noise_burst": is_noise_burst,
            "is_true_drift": False
        })
    return stream


def gen_imbalance_stream(imbalance_ratio=0.10, seed=42, n_batches=50, batch_size=100, n_features=4):
    rng = np.random.RandomState(seed)
    stream = []
    mu_0 = np.zeros(n_features)
    mu_1 = np.ones(n_features) * 2.0
    
    for b in range(1, n_batches + 1):
        n_min = max(1, int(imbalance_ratio * batch_size))
        n_maj = batch_size - n_min
        
        # Abrupt drift at batch 25
        if b > 25:
            cur_mu0, cur_mu1 = np.ones(n_features) * 2.0, np.zeros(n_features)
            delta = 1.5
        else:
            cur_mu0, cur_mu1 = mu_0, mu_1
            delta = 0.0
            
        X = np.vstack([rng.randn(n_maj, n_features) + cur_mu0, rng.randn(n_min, n_features) + cur_mu1])
        y = np.concatenate([np.zeros(n_maj, dtype=np.int64), np.ones(n_min, dtype=np.int64)])
        perm = rng.permutation(batch_size)
        X, y = X[perm], y[perm]
        
        stream.append({
            "batch_idx": b,
            "X": X,
            "y_observed": y,
            "y_clean": y,
            "delta": delta,
            "is_noise_burst": False,
            "is_true_drift": delta > 0.5
        })
    return stream


def gen_financial_fraud_stream(seed=42, n_batches=50, batch_size=50, n_features=6):
    """
    Simulates Financial Transaction Fraud Stream:
    - Highly skewed transactions (98:2 imbalance).
    - Recurring fraud bursts (batches 15-20, 35-40).
    - Covariate drift on transaction amounts.
    """
    rng = np.random.RandomState(seed)
    stream = []
    
    for b in range(1, n_batches + 1):
        is_burst = (15 <= b <= 20) or (35 <= b <= 40)
        imbalance = 0.08 if is_burst else 0.02
        n_fraud = max(1, int(imbalance * batch_size))
        n_legit = batch_size - n_fraud
        
        # Features: [Amount, TimeDiff, Velocity, Distance, GeoRisk, DeviceRisk]
        # Legit: Normal transactions
        legit_X = rng.randn(n_legit, n_features) * 0.8
        # Fraud: Elevated amount, velocity, risk
        fraud_X = rng.randn(n_fraud, n_features) * 1.2 + np.array([2.5, -1.0, 3.0, 2.0, 1.5, 2.0])
        
        # Drift: Inflation drift on amounts (feature 0)
        legit_X[:, 0] += (b / 50.0) * 1.5
        fraud_X[:, 0] += (b / 50.0) * 1.5
        
        X = np.vstack([legit_X, fraud_X])
        y = np.concatenate([np.zeros(n_legit, dtype=np.int64), np.ones(n_fraud, dtype=np.int64)])
        perm = rng.permutation(batch_size)
        
        stream.append({
            "batch_idx": b,
            "X": X[perm],
            "y_observed": y[perm],
            "y_clean": y[perm],
            "delta": 1.2 if is_burst else 0.2,
            "is_noise_burst": False,
            "is_true_drift": is_burst
        })
    return stream


def gen_predictive_maintenance_stream(seed=42, n_batches=50, batch_size=40, n_features=5):
    """
    Simulates Industrial Sensor Predictive Maintenance Stream:
    - Features: [Vibration, Temperature, Pressure, Acoustic, Power]
    - Gradual wear-and-tear drift from normal (0) to imminent failure (1).
    - Heavy sensor noise bursts.
    """
    rng = np.random.RandomState(seed)
    stream = []
    
    for b in range(1, n_batches + 1):
        # Wear increases monotonically over time
        wear = np.clip((b - 10) / 35.0, 0.0, 1.0)
        prob_failure = 0.05 + 0.35 * wear
        n_fail = max(1, int(prob_failure * batch_size))
        n_norm = batch_size - n_fail
        
        # Normal sensors
        norm_X = rng.randn(n_norm, n_features) + np.zeros(n_features)
        # Degrading sensors (high vibration and acoustic emission)
        fail_X = rng.randn(n_fail, n_features) + np.array([2.0 + wear, 1.5 + wear, 0.5, 2.5 + wear, 1.0])
        
        # Sensor glitch noise burst in batches 20-25
        is_glitch = 20 <= b <= 25
        if is_glitch:
            norm_X += rng.randn(*norm_X.shape) * 3.0
            
        X = np.vstack([norm_X, fail_X])
        y = np.concatenate([np.zeros(n_norm, dtype=np.int64), np.ones(n_fail, dtype=np.int64)])
        perm = rng.permutation(batch_size)
        
        stream.append({
            "batch_idx": b,
            "X": X[perm],
            "y_observed": y[perm],
            "y_clean": y[perm],
            "delta": float(wear * 1.5),
            "is_noise_burst": is_glitch,
            "is_true_drift": wear > 0.5
        })
    return stream


def run_full_generalization_battery():
    print("================================================================================")
    print("SECTION 8: FULL GENERALIZATION BENCHMARK BATTERY")
    print("================================================================================\n")
    
    battery_results = {}
    
    # 1. Drift Variations
    print(">>> 1. EVALUATING DRIFT VARIATIONS ...")
    drift_types = ["abrupt", "gradual", "incremental", "recurring", "feature_level"]
    battery_results["drift_variations"] = {}
    
    for dt in drift_types:
        print(f"  - Testing Drift Type: {dt.upper():15s} ...", end=" ", flush=True)
        res = run_stream_benchmark(lambda **kw: gen_drift_stream(drift_type=dt, **kw))
        battery_results["drift_variations"][dt] = res
        ulc_mf1 = res["MultiObjective_ULC_v3"]["macro_f1"]
        base_mf1 = res["Static_Baseline"]["macro_f1"]
        unco_mf1 = res["Uncoordinated_Three_Pillars"]["macro_f1"]
        print(f"Done. ULC-v3 MF1: {ulc_mf1:.3f} | Static: {base_mf1:.3f} | Uncoordinated: {unco_mf1:.3f}")
        
    # 2. Noise Variations
    print("\n>>> 2. EVALUATING NOISE VARIATIONS ...")
    noise_types = ["symmetric", "asymmetric", "instance_dependent", "noise_burst"]
    battery_results["noise_variations"] = {}
    
    for nt in noise_types:
        print(f"  - Testing Noise Type: {nt.upper():18s} ...", end=" ", flush=True)
        res = run_stream_benchmark(lambda **kw: gen_noise_stream(noise_type=nt, **kw))
        battery_results["noise_variations"][nt] = res
        ulc_mf1 = res["MultiObjective_ULC_v3"]["macro_f1"]
        base_mf1 = res["Static_Baseline"]["macro_f1"]
        unco_fres = res["Uncoordinated_Three_Pillars"]["false_resets"]
        ulc_fres = res["MultiObjective_ULC_v3"]["false_resets"]
        print(f"Done. ULC-v3 MF1: {ulc_mf1:.3f} | False Resets (ULC-v3 vs Uncoord): {ulc_fres:.1f} vs {unco_fres:.1f}")
        
    # 3. Class Imbalance Variations
    print("\n>>> 3. EVALUATING EXTREME CLASS IMBALANCES ...")
    imbalances = [(0.10, "90:10"), (0.01, "99:1"), (0.001, "99.9:0.1")]
    battery_results["imbalance_variations"] = {}
    
    for ratio, label in imbalances:
        print(f"  - Testing Imbalance: {label:12s} ...", end=" ", flush=True)
        res = run_stream_benchmark(lambda **kw: gen_imbalance_stream(imbalance_ratio=ratio, **kw), batch_size=100)
        battery_results["imbalance_variations"][label] = res
        ulc_rec = res["MultiObjective_ULC_v3"]["minority_recall"]
        base_rec = res["Static_Baseline"]["minority_recall"]
        print(f"Done. Minority Recall (ULC-v3 vs Static): {ulc_rec*100:5.2f}% vs {base_rec*100:5.2f}%")
        
    # 4. Realistic Public Streaming Benchmarks
    print("\n>>> 4. EVALUATING REALISTIC APPLICATION BENCHMARKS ...")
    print("  - Testing Financial Fraud Stream ...", end=" ", flush=True)
    fraud_res = run_stream_benchmark(lambda **kw: gen_financial_fraud_stream(**kw), batch_size=50, n_features=6)
    battery_results["financial_fraud"] = fraud_res
    print(f"Done. ULC-v3 MF1: {fraud_res['MultiObjective_ULC_v3']['macro_f1']:.3f} | Recall: {fraud_res['MultiObjective_ULC_v3']['minority_recall']*100:.2f}%")
    
    print("  - Testing Predictive Maintenance Stream ...", end=" ", flush=True)
    maint_res = run_stream_benchmark(lambda **kw: gen_predictive_maintenance_stream(**kw), batch_size=40, n_features=5)
    battery_results["predictive_maintenance"] = maint_res
    print(f"Done. ULC-v3 MF1: {maint_res['MultiObjective_ULC_v3']['macro_f1']:.3f} | Recall: {maint_res['MultiObjective_ULC_v3']['minority_recall']*100:.2f}%")
    
    out_file = "experiments/ulc_v3_independent_audit/generalization_battery_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(battery_results, f, indent=2)
    print(f"\nGeneralization battery results saved to {out_file}")

if __name__ == "__main__":
    run_full_generalization_battery()

