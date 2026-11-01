# Tutorial 03: Incremental Learning

**Objective**: Train an incremental Hoeffding Tree (`VectorizedHoeffdingTree`) sample-by-sample without storing historical data in memory.

---

## 1. Setup & Imports

```python
import numpy as np
from adaptive_ml.ala.tree import VectorizedHoeffdingTree

# Initialize Hoeffding Tree with grace period 20
tree = VectorizedHoeffdingTree(
    max_depth=5,
    grace_period=20,
    split_confidence=0.001
)
```

---

## 2. Online Sample-by-Sample Ingestion

```python
np.random.seed(42)

for i in range(150):
    # Single sample streaming in
    x = np.random.randn(4).astype(np.float32)
    y = int(x[0] > 0.0)
    
    tree.update(x, y)
    
    if (i + 1) % 30 == 0:
        print(f"Step {i + 1:03d} | Total Nodes: {tree.n_nodes} | Tree Depth: {tree.depth}")
```

---

## 3. Evaluation on Test Batch

```python
X_eval = np.random.randn(20, 4).astype(np.float32)
y_eval = (X_eval[:, 0] > 0.0).astype(np.int64)

preds = tree.predict(X_eval)
accuracy = np.mean(preds == y_eval)
print(f"Test Evaluation Accuracy: {accuracy:.1%}")
```

**Output**:
```
Step 030 | Total Nodes: 1 | Tree Depth: 1
Step 060 | Total Nodes: 3 | Tree Depth: 2
Step 090 | Total Nodes: 5 | Tree Depth: 3
Step 120 | Total Nodes: 7 | Tree Depth: 3
Step 150 | Total Nodes: 9 | Tree Depth: 4
Test Evaluation Accuracy: 95.0%
```
