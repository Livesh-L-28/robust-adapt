"""ULC-v4 Confidence Engine.

Evaluates joint multi-signal confidence scores across adaptation, noise suppression,
resource throttling, recurring concept restoration, and asymmetric noise mitigation.
"""

from dataclasses import dataclass
from typing import Any, Dict
import numpy as np

from robust_adapt.ulc.v4_evidence import EvidenceVectorV4


@dataclass(frozen=True)
class ConfidenceScores:
    """Confidence distribution across arbitration actions in [0, 1]."""
    adapt: float
    suppress_noise: float
    throttle_resources: float
    restore_concept: float
    mitigate_asymmetric_noise: float


class ConfidenceEngine:
    """Evaluates multi-signal confidence to drive deterministic arbitration."""

    @staticmethod
    def evaluate(evidence: EvidenceVectorV4, tau_r: float = 0.65) -> ConfidenceScores:
        """Compute normalized confidence vector from cross-pillar evidence."""
        delta = evidence.delta_drift
        rel = evidence.mean_reliability
        u_res = evidence.resource_utilization
        sim_rec = evidence.recurring_similarity
        asym_rate = evidence.asymmetric_noise_rate

        # 1. Adaptation Confidence
        # High when drift signal is high AND data reliability is clean
        if delta >= 0.5:
            c_adapt = float(np.clip((delta / 2.0) * rel, 0.0, 1.0))
        else:
            c_adapt = float(np.clip(0.1 * rel, 0.0, 0.5))

        # 2. Noise Suppression Confidence
        # High when drift signal is high BUT data reliability is corrupt
        if delta >= 0.5:
            c_suppress = float(np.clip((delta / 2.0) * (1.0 - rel), 0.0, 1.0))
        else:
            c_suppress = float(np.clip(1.0 - rel, 0.0, 1.0))

        # 3. Resource Throttle Confidence
        c_throttle = float(np.clip((u_res - 0.70) / 0.30, 0.0, 1.0)) if u_res >= 0.70 else 0.0

        # 4. Recurring Concept Restoration Confidence
        c_restore = float(sim_rec) if sim_rec >= 0.75 else 0.0

        # 5. Asymmetric Noise Mitigation Confidence
        c_asym = float(np.clip(asym_rate / 0.40, 0.0, 1.0)) if asym_rate >= 0.15 else 0.0

        return ConfidenceScores(
            adapt=c_adapt,
            suppress_noise=c_suppress,
            throttle_resources=c_throttle,
            restore_concept=c_restore,
            mitigate_asymmetric_noise=c_asym,
        )
