"""
Example 06: PyTorch Neural Model with ULC Cross-Pillar Coordination.

Demonstrates controlling a PyTorch model's training dynamics (learning rate,
loss weighting, and safe checkpointing) via ROBUST-ADAPT's Unified Learning Controller (ULC).
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import torch
import torch.nn as nn
import numpy as np

from robust_adapt.integrations.torch_callback import TorchCheckpointAdapter
from robust_adapt.integrations.torch_module import TorchSymmetricCrossEntropyLoss
from robust_adapt.ulc.controller import AdaptiveLearningController
from robust_adapt.ulc.directives import ControllerState


def main():
    print("=====================================================================")
    print("ROBUST-ADAPT Example 06: PyTorch Training with ULC Coordination")
    print("=====================================================================")

    torch.manual_seed(42)
    rng = np.random.default_rng(42)

    n_features = 16
    n_classes = 2
    base_lr = 1e-3

    # 1. Neural Model & Robust Criterion
    model = nn.Sequential(
        nn.Linear(n_features, 32),
        nn.ReLU(),
        nn.Linear(32, n_classes),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=base_lr)
    criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.5)

    # 2. ULC Controller Facade
    controller = AdaptiveLearningController()

    print("Simulating non-stationary streaming training with ULC arbitration...\n")

    n_phases = 4
    steps_per_phase = 25

    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = Path(tmp_dir) / "ulc_coordinated_model.safetensors"

        for phase in range(1, n_phases + 1):
            if phase == 1:
                phase_name = "Stationary Clean Stream"
                drift_div = 0.02
            elif phase == 2:
                phase_name = "Abrupt Concept Drift Detected"
                drift_div = 1.25
            elif phase == 3:
                phase_name = "Noisy Stream with Label Perturbation"
                drift_div = 0.15
            else:
                phase_name = "Post-Drift Stabilization"
                drift_div = 0.05

            losses = []
            for _ in range(steps_per_phase):
                # Streaming batch
                x_np = rng.standard_normal((32, n_features)).astype(np.float32)
                y_np = (x_np[:, 0] + x_np[:, 1] > 0).astype(np.int64)

                x = torch.from_numpy(x_np)
                y = torch.from_numpy(y_np)

                out = model(x)
                loss = criterion(out, y)

                # Query ULC controller with batch telemetry
                logits_np = out.detach().cpu().numpy()
                directive, info = controller.step(
                    X=x_np,
                    y=y_np,
                    logits=logits_np,
                    current_loss=loss.item(),
                    delta_drift=drift_div,
                )

                # Dynamic Learning Rate scaling from ULC directive
                effective_lr = base_lr * directive.learning_rate_scale
                for param_group in optimizer.param_groups:
                    param_group["lr"] = effective_lr

                optimizer.zero_grad()
                loss.backward()

                # Dynamic gradient clipping if suggested by ULC
                if directive.gradient_clip_factor < 1.0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=directive.gradient_clip_factor)

                optimizer.step()
                losses.append(loss.item())

            mean_loss = np.mean(losses)
            print(f"Phase {phase} [{phase_name}]:")
            print(f"  ULC State: {directive.state.value} | LR Scale: {directive.learning_rate_scale:.2f}x (Effective LR: {effective_lr:.5f})")
            print(f"  Training Outcome -> Mean Loss: {mean_loss:.4f}\n")

        # 3. Save safe hybrid checkpoint
        print("Saving safe hybrid checkpoint (SafeTensors + JSON metadata)...")
        saved_file = TorchCheckpointAdapter.save_hybrid_checkpoint(
            model=model,
            optimizer=optimizer,
            controller=controller,
            filepath=ckpt_path,
        )
        print(f"Saved checkpoint successfully to: {saved_file}")
        print(f"Checkpoint size: {saved_file.stat().st_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()
