"""
Integration test suite verifying execution of all 8 realistic integration examples.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

INTEGRATION_EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples" / "integrations"

INTEGRATION_SCRIPTS = [
    "01_sklearn_static_pipeline.py",
    "02_sklearn_incremental_drift.py",
    "03_sklearn_imbalanced_minority.py",
    "04_torch_neural_rao.py",
    "05_torch_training_rla_reliability.py",
    "06_torch_model_ulc_coordination.py",
    "07_cross_framework_data_conversion.py",
    "08_core_only_workflow.py",
]


@pytest.mark.parametrize("script_name", INTEGRATION_SCRIPTS)
def test_integration_example_execution(script_name: str) -> None:
    """Execute each integration example script as a subprocess and verify returncode == 0."""
    script_path = INTEGRATION_EXAMPLES_DIR / script_name
    assert script_path.exists(), f"Integration script does not exist: {script_path}"

    res = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode == 0, f"{script_name} failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
