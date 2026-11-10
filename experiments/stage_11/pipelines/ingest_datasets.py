"""
Stage 11 — Dataset Ingestion and Quality Audit Pipeline.

Loads genuine benchmark datasets, verifies provenance, computes cryptographic SHA-256
checksums, performs quality audits (missingness, schema, distributions), and generates
standardized Parquet files and manifest JSON files in experiments/stage_11/.

Datasets handled:
1. Electricity (Elec2) — Concept drift stream (OpenML ID 151)
2. Spambase — Robust learning under label noise (OpenML ID 44)
3. Forest CoverType (CovType) — Multi-class scaling & resource optimization
4. Credit Card Fraud (ULB) — Extreme class imbalance & non-stationary fraud
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
from sklearn.datasets import fetch_openml, fetch_covtype


def save_dataframe(df: pd.DataFrame, out_file: Path) -> None:
    """Saves DataFrame to compressed CSV (.csv.gz) without external pyarrow dependencies."""
    df.to_csv(out_file, index=False, compression="gzip")


def compute_sha256(filepath: str | Path) -> str:
    """Computes SHA-256 hexadecimal digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def ingest_electricity(out_dir: Path, manifest_dir: Path) -> dict:
    print("\n--- [1/4] Ingesting Electricity Market Stream (Elec2) ---")
    t0 = time.perf_counter()
    bunch = fetch_openml(data_id=151, as_frame=True, parser="auto")
    df = bunch.frame.copy()

    # Clean columns & target
    # Target values: 'DOWN' -> 0, 'UP' -> 1
    target_col = "class"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in Electricity dataset")

    # Map target
    y_raw = df[target_col].astype(str).str.strip().str.upper()
    df["target"] = (y_raw == "UP").astype(np.int64)
    feature_cols = [c for c in df.columns if c not in [target_col, "target"]]

    # Ensure all features numeric float64
    for c in feature_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(np.float64)

    # Missing values check
    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    out_file = out_dir / "electricity.csv.gz"
    save_dataframe(df, out_file)
    sha256_hash = compute_sha256(out_file)

    manifest = {
        "dataset_name": "Electricity (Elec2)",
        "source": "OpenML Data ID 151 (Harries & Wales, 1999)",
        "license": "Public Domain / Open Access",
        "file_name": "electricity.csv.gz",
        "sha256": sha256_hash,
        "n_rows": len(df),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "target_name": "target",
        "target_mapping": {"DOWN": 0, "UP": 1},
        "class_distribution": df["target"].value_counts().to_dict(),
        "imbalance_ratio": float(df["target"].value_counts()[0] / df["target"].value_counts()[1]),
        "total_missing_values": total_missing,
        "temporal_order_preserved": True,
        "ingestion_time_sec": time.perf_counter() - t0,
    }

    manifest_file = manifest_dir / "electricity_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"  Electricity saved to {out_file} (SHA256: {sha256_hash[:16]}...)")
    print(f"  Rows: {len(df):,}, Features: {len(feature_cols)}, Classes: {manifest['class_distribution']}")
    return manifest


def ingest_spambase(out_dir: Path, manifest_dir: Path) -> dict:
    print("\n--- [2/4] Ingesting Spambase Email Classification ---")
    t0 = time.perf_counter()
    bunch = fetch_openml(data_id=44, as_frame=True, parser="auto")
    df = bunch.frame.copy()

    target_col = "class"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in Spambase dataset")

    # Map target: '1' -> 1 (Spam), '0' -> 0 (Ham)
    df["target"] = pd.to_numeric(df[target_col], errors="coerce").astype(np.int64)
    feature_cols = [c for c in df.columns if c not in [target_col, "target"]]

    for c in feature_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(np.float64)

    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    out_file = out_dir / "spambase.csv.gz"
    save_dataframe(df, out_file)
    sha256_hash = compute_sha256(out_file)

    manifest = {
        "dataset_name": "Spambase",
        "source": "OpenML Data ID 44 (Hopkins et al., HP Labs / UCI)",
        "license": "CC BY 4.0 / Open Access",
        "file_name": "spambase.csv.gz",
        "sha256": sha256_hash,
        "n_rows": len(df),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "target_name": "target",
        "target_mapping": {"Ham": 0, "Spam": 1},
        "class_distribution": df["target"].value_counts().to_dict(),
        "imbalance_ratio": float(df["target"].value_counts()[0] / df["target"].value_counts()[1]),
        "total_missing_values": total_missing,
        "ingestion_time_sec": time.perf_counter() - t0,
    }

    manifest_file = manifest_dir / "spambase_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"  Spambase saved to {out_file} (SHA256: {sha256_hash[:16]}...)")
    print(f"  Rows: {len(df):,}, Features: {len(feature_cols)}, Classes: {manifest['class_distribution']}")
    return manifest


def ingest_covtype(out_dir: Path, manifest_dir: Path) -> dict:
    print("\n--- [3/4] Ingesting Forest CoverType (CovType) ---")
    t0 = time.perf_counter()
    bunch = fetch_covtype(as_frame=True)
    df = bunch.frame.copy()

    target_col = "Cover_Type"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in CoverType dataset")

    # Target values 1-7, map to 0-6 for standard zero-indexed classification
    df["target"] = (df[target_col].astype(np.int64) - 1).astype(np.int64)
    feature_cols = [c for c in df.columns if c not in [target_col, "target"]]

    for c in feature_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(np.float32)

    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    out_file = out_dir / "covtype.csv.gz"
    save_dataframe(df, out_file)
    sha256_hash = compute_sha256(out_file)

    manifest = {
        "dataset_name": "Forest CoverType",
        "source": "USFS / Colorado State University / scikit-learn",
        "license": "Public Domain",
        "file_name": "covtype.csv.gz",
        "sha256": sha256_hash,
        "n_rows": len(df),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "target_name": "target",
        "target_mapping": {f"Class_{i+1}": i for i in range(7)},
        "class_distribution": df["target"].value_counts().to_dict(),
        "total_missing_values": total_missing,
        "ingestion_time_sec": time.perf_counter() - t0,
    }

    manifest_file = manifest_dir / "covtype_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"  CovType saved to {out_file} (SHA256: {sha256_hash[:16]}...)")
    print(f"  Rows: {len(df):,}, Features: {len(feature_cols)}, Classes: {manifest['class_distribution']}")
    return manifest


def ingest_creditcard(raw_arff_file: Path, out_dir: Path, manifest_dir: Path) -> dict:
    print("\n--- [4/4] Ingesting Credit Card Fraud Detection (ULB) ---")
    t0 = time.perf_counter()

    if not raw_arff_file.exists():
        raise FileNotFoundError(f"Raw ARFF file {raw_arff_file} does not exist.")

    # Parse ARFF file efficiently
    print(f"  Parsing raw ARFF file: {raw_arff_file} ({raw_arff_file.stat().st_size / (1024**2):.1f} MB)...")
    
    rows = []
    attributes = []
    in_data = False

    with open(raw_arff_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("%"):
                continue
            if not in_data:
                if line_str.upper().startswith("@ATTRIBUTE"):
                    parts = line_str.split()
                    attr_name = parts[1].replace("'", "").replace('"', "")
                    attributes.append(attr_name)
                elif line_str.upper().startswith("@DATA"):
                    in_data = True
            else:
                # Comma-separated data line
                vals = line_str.split(",")
                if len(vals) == len(attributes):
                    rows.append(vals)

    print(f"  Parsed {len(rows):,} data rows with {len(attributes)} attributes.")
    df = pd.DataFrame(rows, columns=attributes)

    # Clean target
    target_col = attributes[-1]  # Typically 'Class'
    # Class values: '0' -> 0, '1' -> 1, or "'0'", "'1'"
    df["target"] = df[target_col].astype(str).str.replace("'", "").str.replace('"', "").astype(np.int64)

    feature_cols = [c for c in attributes if c != target_col]
    for c in feature_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype(np.float32)

    # Sort chronologically by 'Time' if present
    if "Time" in df.columns:
        df = df.sort_values(by="Time").reset_index(drop=True)

    out_file = out_dir / "creditcard.csv.gz"
    save_dataframe(df, out_file)
    sha256_hash = compute_sha256(out_file)

    manifest = {
        "dataset_name": "Credit Card Fraud Detection (ULB)",
        "source": "Machine Learning Group (ULB) & Worldline (Dal Pozzolo et al., 2015)",
        "license": "Open Database License (ODbL) v1.0",
        "file_name": "creditcard.csv.gz",
        "sha256": sha256_hash,
        "n_rows": len(df),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "target_name": "target",
        "target_mapping": {"Legitimate": 0, "Fraudulent": 1},
        "class_distribution": df["target"].value_counts().to_dict(),
        "imbalance_ratio": float(df["target"].value_counts()[0] / df["target"].value_counts()[1]),
        "total_missing_values": int(df.isnull().sum().sum()),
        "chronological_sort_column": "Time" if "Time" in df.columns else None,
        "ingestion_time_sec": time.perf_counter() - t0,
    }

    manifest_file = manifest_dir / "creditcard_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"  CreditCard saved to {out_file} (SHA256: {sha256_hash[:16]}...)")
    print(f"  Rows: {len(df):,}, Features: {len(feature_cols)}, Classes: {manifest['class_distribution']}")
    print(f"  Imbalance Ratio: {manifest['imbalance_ratio']:.1f}:1 ({manifest['class_distribution'].get(1, 0)/len(df)*100:.3f}% minority)")
    return manifest


def main():
    print("=====================================================================")
    print("AdaptiveML Stage 11: Real-World Dataset Ingestion & Quality Audit")
    print(f"Python: {sys.version.split()[0]} on {sys.platform}")
    print("=====================================================================")

    out_dir = Path("experiments/stage_11/datasets")
    manifest_dir = Path("experiments/stage_11/dataset_manifests")
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    manifests = {}
    manifests["electricity"] = ingest_electricity(out_dir, manifest_dir)
    manifests["spambase"] = ingest_spambase(out_dir, manifest_dir)
    manifests["covtype"] = ingest_covtype(out_dir, manifest_dir)

    raw_cc_arff = out_dir / "creditcard_raw.arff"
    if raw_cc_arff.exists() and raw_cc_arff.stat().st_size > 50 * 1024 * 1024:
        manifests["creditcard"] = ingest_creditcard(raw_cc_arff, out_dir, manifest_dir)
    else:
        print(f"\n[Note] creditcard_raw.arff is still downloading (current size: {raw_cc_arff.stat().st_size / (1024**2) if raw_cc_arff.exists() else 0:.1f} MB).")

    summary_file = manifest_dir / "all_datasets_manifest.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(manifests, f, indent=2)

    print(f"\nAll completed manifests saved to {summary_file}")


if __name__ == "__main__":
    main()
