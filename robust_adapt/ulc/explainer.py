"""ULC-v4 Arbitration Explainability Engine.

Generates human-readable, auditable natural language explanations of controller state
transitions, pillar coordination directives, and resolved cross-pillar conflicts.
"""

from typing import Any, Dict
from robust_adapt.ulc.v4_automaton import DirectiveV4
from robust_adapt.ulc.v4_evidence import EvidenceVectorV4


class ULCExplainer:
    """Explains controller arbitration decisions and cross-pillar coordination."""

    @staticmethod
    def explain(
        directive: DirectiveV4,
        evidence: EvidenceVectorV4,
        scenario_name: str = "",
    ) -> Dict[str, Any]:
        """Generate structured and prose explanation for an arbitration decision."""
        ev_dict = evidence.to_dict()

        reasons = []
        if evidence.delta_drift >= 1.0:
            reasons.append(f"significant drift detected (delta={evidence.delta_drift:.2f})")
        if evidence.mean_reliability < 0.65:
            reasons.append(f"elevated sample corruption (reliability={evidence.mean_reliability:.2f})")
        if evidence.resource_utilization >= 0.80:
            reasons.append(f"high resource utilization ({evidence.resource_utilization * 100:.1f}%)")
        if evidence.imbalance_ratio >= 5.0:
            reasons.append(f"severe class imbalance (IR={evidence.imbalance_ratio:.1f}:1)")
        if evidence.recurring_similarity >= 0.75:
            reasons.append(f"recurring concept match (similarity={evidence.recurring_similarity:.2f})")

        reasons_str = "; ".join(reasons) if reasons else "stream steady and within nominal bounds"

        narrative = (
            f"Controller State: {directive.state.value}. "
            f"Primary Drivers: {reasons_str}. "
            f"Arbitration Policy: {scenario_name or 'Nominal Execution'}. "
            f"Action Directives: LR Scale={directive.learning_rate_scale:.1f}x, "
            f"Reset Momentum={directive.reset_momentum}, "
            f"Replay Policy={directive.purge_replay_policy} (Keep Minority={directive.keep_minority_in_replay})."
        )

        return {
            "state": directive.state.value,
            "scenario": scenario_name,
            "confidence": round(directive.confidence, 4),
            "evidence": ev_dict,
            "actions": {
                "learning_rate_scale": directive.learning_rate_scale,
                "reset_momentum": directive.reset_momentum,
                "suppress_adwin": directive.suppress_adwin,
                "freeze_buffer": directive.freeze_buffer,
                "purge_replay_policy": directive.purge_replay_policy,
                "keep_minority_in_replay": directive.keep_minority_in_replay,
                "skip_expensive_ops": directive.skip_expensive_ops,
            },
            "narrative": narrative,
        }
