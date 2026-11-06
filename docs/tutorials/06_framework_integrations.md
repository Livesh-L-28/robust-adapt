# Tutorial 6: Framework Integrations (scikit-learn & PyTorch)

Learn how to integrate AdaptiveML algorithms into existing scikit-learn pipelines and PyTorch neural network training workflows.

---

## 1. scikit-learn Pipeline Integration

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from robust_adapt.integrations.sklearn import SklearnAdaptiveClassifier

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", SklearnAdaptiveClassifier(n_features=4, n_classes=2, grace_period=20)),
])

X = np.random.randn(100, 4)
y = (X[:, 0] > 0.0).astype(int)

# Fit pipeline
pipe.fit(X, y)

# Predict
preds = pipe.predict(X)
accuracy = pipe.score(X, y)
print(f"Pipeline Accuracy: {accuracy * 100:.1f}%")
```

---

## 2. PyTorch Deep Neural Network Training

```python
import torch
import torch.nn as nn
from robust_adapt.integrations.torch_optim import create_torch_low_memory_adamw
from robust_adapt.integrations.torch_module import TorchSymmetricCrossEntropyLoss

model = nn.Sequential(nn.Linear(8, 32), nn.ReLU(), nn.Linear(32, 2))
optimizer = create_torch_low_memory_adamw(model.parameters(), lr=1e-3, block_size=64)
criterion = TorchSymmetricCrossEntropyLoss(alpha=1.0, beta=0.1)

# Training loop
for epoch in range(5):
    inputs = torch.randn(64, 8)
    labels = torch.randint(0, 2, (64,))

    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch + 1} | Loss: {loss.item():.4f}")
```

Executable demos available at [`examples/integrations/sklearn_pipeline_example.py`](file:///c:/projects/AdaptiveML/examples/integrations/sklearn_pipeline_example.py) and [`examples/integrations/torch_training_example.py`](file:///c:/projects/AdaptiveML/examples/integrations/torch_training_example.py).
