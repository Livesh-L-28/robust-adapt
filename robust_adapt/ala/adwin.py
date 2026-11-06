"""Reliability-Weighted ADWIN (RW-ADWIN) concept drift detector.

Mathematical formulation specified in DOC-DES-P6-003 and DOC-DES-P6-009 (Algorithm 3).
"""

import math
from typing import Any, Dict, List, Optional, Tuple
from robust_adapt.core.constants import EPS_DIV, EPS_RELIABILITY
from robust_adapt.core.exceptions import ValidationError


class _Bucket:
    """Compressed exponential histogram bucket."""

    __slots__ = ("w", "val", "w_sq", "count")

    def __init__(self, w: float, val: float, w_sq: float, count: int) -> None:
        self.w = float(w)          # Sum of weights (reliabilities)
        self.val = float(val)      # Sum of weighted values (w * loss)
        self.w_sq = float(w_sq)    # Sum of squared weights
        self.count = int(count)    # Number of original observations


class ReliabilityWeightedADWIN:
    """Reliability-Weighted Adaptive Sliding Window (RW-ADWIN) drift detector.

    Maintains a variable-length window partitioned into sub-windows W = W0 . W1,
    weighting observations by sample reliability to suppress false-positive drift alarms
    caused by label corruption while preserving rapid detection of true concept shifts.

    Parameters
    ----------
    delta : float, default=0.002
        Confidence value for the Hoeffding cut bound (1 - delta detection confidence).
    min_subwindow_weight : float, default=5.0
        Minimum cumulative sample reliability required in sub-windows to test split.
    eps_r : float, default=1e-4
        Lower-bound epsilon guard on reliability weights.
    max_buckets_per_level : int, default=5
        Maximum number of buckets of equal size before compression.
    """

    def __init__(
        self,
        delta: float = 0.002,
        min_subwindow_weight: float = 5.0,
        eps_r: float = EPS_RELIABILITY,
        max_buckets_per_level: int = 5,
    ) -> None:
        if delta <= 0.0 or delta >= 1.0:
            raise ValidationError(f"delta must be in (0, 1), got {delta}")
        if min_subwindow_weight <= 0.0:
            raise ValidationError(f"min_subwindow_weight must be positive, got {min_subwindow_weight}")

        self.delta = float(delta)
        self.min_subwindow_weight = float(min_subwindow_weight)
        self.eps_r = float(eps_r)
        self.max_buckets_per_level = int(max_buckets_per_level)

        self._buckets: List[_Bucket] = []
        self.window_total_count: int = 0
        self.window_weight_sum: float = 0.0
        self.window_weighted_val_sum: float = 0.0
        self.window_weight_sq_sum: float = 0.0
        self.last_delta_drift: float = 0.0

    @property
    def total_samples(self) -> int:
        """Total observations currently in the active window."""
        return self.window_total_count

    @property
    def weighted_mean(self) -> float:
        """Current reliability-weighted mean of observations in the active window."""
        if self.window_weight_sum <= 0.0:
            return 0.0
        return self.window_weighted_val_sum / self.window_weight_sum

    def update(self, loss: float, reliability: float = 1.0) -> bool:
        """Ingest a new observation and return True if concept drift is detected.

        Parameters
        ----------
        loss : float
            Instantaneous error or loss value, typically in [0.0, 1.0].
        reliability : float, default=1.0
            Sample reliability score in [eps_r, 1.0].

        Returns
        -------
        drift_detected : bool
            True if statistical drift bound was violated and window cut was performed.
        """
        loss = float(loss)
        reliability = float(reliability)

        # Numerical bounds validation
        if math.isnan(loss) or math.isinf(loss):
            raise ValidationError(f"Loss must be finite, got {loss}")
        if reliability < self.eps_r:
            reliability = self.eps_r
        elif reliability > 1.0:
            reliability = 1.0

        # Step 1: Insert new observation at the head (newest end)
        w = reliability
        v = loss
        self.window_total_count += 1
        self.window_weight_sum += w
        self.window_weighted_val_sum += w * v
        self.window_weight_sq_sum += w * w

        self._buckets.append(_Bucket(w=w, val=w * v, w_sq=w * w, count=1))
        self._compress_buckets()

        # Step 2: Check sub-window partitions W = W0 . W1 from tail (oldest end)
        drift_detected = False
        self.last_delta_drift = 0.0

        if self.window_weight_sum < 2.0 * self.min_subwindow_weight:
            return False

        W0_w = 0.0
        W0_val = 0.0
        W0_w_sq = 0.0
        W_total_w = self.window_weight_sum
        W_total_val = self.window_weighted_val_sum

        cut_idx = -1
        n_buckets = len(self._buckets)

        for i in range(n_buckets - 1):
            b = self._buckets[i]
            W0_w += b.w
            W0_val += b.val
            W0_w_sq += b.w_sq

            W1_w = W_total_w - W0_w
            W1_val = W_total_val - W0_val
            W1_w_sq = self.window_weight_sq_sum - W0_w_sq

            if W0_w < self.min_subwindow_weight or W1_w < self.min_subwindow_weight:
                continue

            # Effective sample sizes via Kish's formula
            N_eff_0 = (W0_w * W0_w) / (W0_w_sq + EPS_DIV)
            N_eff_1 = (W1_w * W1_w) / (W1_w_sq + EPS_DIV)
            m_eff = (N_eff_0 * N_eff_1) / (N_eff_0 + N_eff_1 + EPS_DIV)

            if m_eff <= 0.0:
                continue

            mu_0 = W0_val / W0_w
            mu_1 = W1_val / W1_w
            abs_diff = abs(mu_0 - mu_1)

            # Hoeffding cut bound with effective sample size
            eps_cut = math.sqrt((1.0 / (2.0 * m_eff)) * math.log(4.0 * self.window_total_count / self.delta))

            delta_drift = abs_diff / (eps_cut + EPS_DIV)
            if delta_drift > self.last_delta_drift:
                self.last_delta_drift = delta_drift

            if abs_diff >= eps_cut:
                drift_detected = True
                cut_idx = i
                break

        # Step 3: Execute window cut if drift detected
        if drift_detected and cut_idx >= 0:
            # Delete buckets 0..cut_idx (oldest sub-window W0)
            dropped = self._buckets[: cut_idx + 1]
            self._buckets = self._buckets[cut_idx + 1 :]

            for b in dropped:
                self.window_total_count -= b.count
                self.window_weight_sum -= b.w
                self.window_weighted_val_sum -= b.val
                self.window_weight_sq_sum -= b.w_sq

            # Clean precision drift
            if self.window_total_count <= 0 or len(self._buckets) == 0:
                self.reset()

        return drift_detected

    def _compress_buckets(self) -> None:
        """Merge buckets of identical count if level exceeds max_buckets_per_level."""
        i = 0
        while i < len(self._buckets) - 2:
            b1 = self._buckets[i]
            b2 = self._buckets[i + 1]
            b3 = self._buckets[i + 2]

            # If three consecutive buckets share the same count, merge the oldest two
            if b1.count == b2.count == b3.count:
                merged = _Bucket(
                    w=b1.w + b2.w,
                    val=b1.val + b2.val,
                    w_sq=b1.w_sq + b2.w_sq,
                    count=b1.count + b2.count,
                )
                self._buckets[i] = merged
                del self._buckets[i + 1]
            else:
                i += 1

    def reset(self) -> None:
        """Reset the sliding window to empty state."""
        self._buckets.clear()
        self.window_total_count = 0
        self.window_weight_sum = 0.0
        self.window_weighted_val_sum = 0.0
        self.window_weight_sq_sum = 0.0
        self.last_delta_drift = 0.0

    def state_dict(self) -> Dict[str, Any]:
        """Serialize window state to dictionary."""
        return {
            "delta": self.delta,
            "min_subwindow_weight": self.min_subwindow_weight,
            "eps_r": self.eps_r,
            "window_total_count": self.window_total_count,
            "window_weight_sum": self.window_weight_sum,
            "window_weighted_val_sum": self.window_weighted_val_sum,
            "window_weight_sq_sum": self.window_weight_sq_sum,
            "last_delta_drift": self.last_delta_drift,
            "buckets": [
                {"w": b.w, "val": b.val, "w_sq": b.w_sq, "count": b.count}
                for b in self._buckets
            ],
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        """Restore window state from dictionary."""
        self.delta = float(state["delta"])
        self.min_subwindow_weight = float(state["min_subwindow_weight"])
        self.eps_r = float(state["eps_r"])
        self.window_total_count = int(state["window_total_count"])
        self.window_weight_sum = float(state["window_weight_sum"])
        self.window_weighted_val_sum = float(state["window_weighted_val_sum"])
        self.window_weight_sq_sum = float(state["window_weight_sq_sum"])
        self.last_delta_drift = float(state.get("last_delta_drift", 0.0))
        self._buckets = [
            _Bucket(w=b["w"], val=b["val"], w_sq=b["w_sq"], count=b["count"])
            for b in state.get("buckets", [])
        ]
