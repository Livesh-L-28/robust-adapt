"""Pytest test suite verifying execution of all 14 realistic examples."""

import subprocess
import sys
from pathlib import Path
import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"

EXAMPLE_SCRIPTS = [
    "01_static_classification_baseline.py",
    "02_abrupt_concept_drift.py",
    "03_gradual_concept_drift.py",
    "04_incremental_learning.py",
    "05_noisy_label_learning.py",
    "06_imbalanced_classification.py",
    "07_minority_aware_learning.py",
    "08_resource_constrained_optimization.py",
    "09_delayed_label_streaming.py",
    "10_ulc_v4_1_integrated_learning.py",
    "11_ala_only_operation.py",
    "12_rla_only_operation.py",
    "13_rao_only_operation.py",
    "14_partial_pillar_ulc_configuration.py",
    "15_ala_3_0_recurring_concepts.py",
    "16_rla_3_0_asymmetric_defense.py",
    "17_minority_2_0_calibrated_stream.py",
    "18_rao_2_0_vectorized_adamw.py",
    "19_ulc_v5_calibrated_controller.py",
]


@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_example_execution(script_name: str):
    """Execute each example script as a subprocess and verify returncode == 0."""
    script_path = EXAMPLES_DIR / script_name
    assert script_path.exists(), f"Example script does not exist: {script_path}"

    res = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode == 0, f"{script_name} failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
