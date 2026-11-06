"""Evidence-Based Non-Destructive Label Correction.

Audited and reversible label correction:
When model prediction confidence exceeds tau_conf (e.g. 0.85) AND reported label
reliability falls below tau_noise (e.g. 0.35), proposes high-confidence corrected labels
while retaining a complete immutable audit trail for rollback.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np

from robust_adapt.core.exceptions import ConfigurationError, ValidationError
from robust_adapt.core.validation import check_array_2d, check_labels_1d


@dataclass(frozen=True)
class CorrectionAuditRecord:
    """Immutable audit trail for a single label correction."""
    sample_index: int
    sample_id: str
    original_label: int
    corrected_label: int
    model_confidence: float
    sample_reliability: float
    timestamp: float


class EvidenceBasedLabelCorrector:
    """Proposes high-confidence label corrections for corrupt stream instances.

    Parameters
    ----------
    n_classes : int, default=2
        Number of target classes.
    confidence_threshold : float, default=0.85
        Minimum model posterior probability required to propose correction.
    reliability_threshold : float, default=0.35
        Maximum sample reliability score required to consider label corrupted.
    """

    def __init__(
        self,
        n_classes: int = 2,
        confidence_threshold: float = 0.85,
        reliability_threshold: float = 0.35,
    ) -> None:
        if n_classes < 2:
            raise ConfigurationError(f"n_classes must be >= 2, got {n_classes}")
        if not 0.50 <= confidence_threshold <= 1.0:
            raise ConfigurationError(f"confidence_threshold must be in [0.5, 1.0], got {confidence_threshold}")
        if not 0.0 <= reliability_threshold <= 0.50:
            raise ConfigurationError(f"reliability_threshold must be in [0.0, 0.5], got {reliability_threshold}")

        self.n_classes = int(n_classes)
        self.conf_thresh = float(confidence_threshold)
        self.rel_thresh = float(reliability_threshold)

        # Audit history of all corrections performed
        self.audit_log: List[CorrectionAuditRecord] = []

    def correct_batch(
        self,
        X: np.ndarray,
        y: np.ndarray,
        probas: np.ndarray,
        reliabilities: np.ndarray,
        sample_ids: Optional[Sequence[str]] = None,
        timestamp: float = 0.0,
    ) -> Tuple[np.ndarray, List[CorrectionAuditRecord]]:
        """Evaluate batch and propose non-destructive corrections for corrupt labels.

        Parameters
        ----------
        X : np.ndarray of shape (N, D)
            Feature matrix.
        y : np.ndarray of shape (N,)
            Reported ground truth labels.
        probas : np.ndarray of shape (N, n_classes)
            Model posterior class probabilities.
        reliabilities : np.ndarray of shape (N,)
            Sample reliability scores in [0, 1].
        sample_ids : Optional[Sequence[str]], default=None
            Unique sample identifiers.
        timestamp : float, default=0.0
            Stream timestamp.

        Returns
        -------
        Tuple[np.ndarray, List[CorrectionAuditRecord]]
            (corrected_labels, audit_records_this_batch)
        """
        X_arr = check_array_2d(X, name="X")
        n_samples = X_arr.shape[0]
        y_arr = check_labels_1d(y, expected_len=n_samples, n_classes=self.n_classes, name="y")
        prob_arr = np.asarray(probas, dtype=np.float64)
        rel_arr = np.asarray(reliabilities, dtype=np.float64)

        corrected_y = y_arr.copy()
        batch_records: List[CorrectionAuditRecord] = []

        predicted_labels = np.argmax(prob_arr, axis=1)
        confidences = np.max(prob_arr, axis=1)

        for i in range(n_samples):
            orig_c = int(y_arr[i])
            pred_c = int(predicted_labels[i])
            conf = float(confidences[i])
            rel = float(rel_arr[i])
            s_id = str(sample_ids[i]) if sample_ids is not None else f"sample_{i}"

            # Correction rule: reported label != predicted label AND conf >= tau_conf AND rel < tau_rel
            if orig_c != pred_c and conf >= self.conf_thresh and rel < self.rel_thresh:
                record = CorrectionAuditRecord(
                    sample_index=i,
                    sample_id=s_id,
                    original_label=orig_c,
                    corrected_label=pred_c,
                    model_confidence=conf,
                    sample_reliability=rel,
                    timestamp=float(timestamp),
                )
                corrected_y[i] = pred_c
                batch_records.append(record)
                self.audit_log.append(record)

        return corrected_y, batch_records

    def rollback(self, y_corrected: np.ndarray, audit_records: List[CorrectionAuditRecord]) -> np.ndarray:
        """Revert corrected labels back to their original reported states."""
        reverted = np.array(y_corrected, copy=True)
        for rec in audit_records:
            reverted[rec.sample_index] = rec.original_label
        return reverted
