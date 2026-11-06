# Verifying Your Installation

After installing `robust-adapt`, run these verification steps to confirm that your environment is properly configured.

---

## 1. Quick One-Line Verification

Run the following command from your terminal:

```bash
python -c "import robust_adapt; print(f'ROBUST-ADAPT version: {robust_adapt.__version__}'); from robust_adapt.ulc import UnifiedLearningControllerV5; print('Core algorithms loaded successfully!')"
```

Expected output:
```text
ROBUST-ADAPT version: 0.1.0.dev0
Core algorithms loaded successfully!
```

---

## 2. Comprehensive Diagnostics Script

Create a script `check_environment.py`:

```python
import sys
import numpy as np
import robust_adapt
from robust_adapt.ala import AdaptiveClassifier
from robust_adapt.rla import MultiSignalReliabilityEngine
from robust_adapt.ulc import UnifiedLearningControllerV5

print("==================================================")
print(f"Python Runtime:       {sys.version.split()[0]}")
print(f"Platform:             {sys.platform}")
print(f"NumPy Version:        {np.__version__}")
print(f"ROBUST-ADAPT Version: {robust_adapt.__version__}")
print("==================================================")

# 1. Test basic instantiation
clf = AdaptiveClassifier(n_features=2, n_classes=2)
print("[OK] AdaptiveClassifier initialized")

# 2. Test prequential update
X = np.array([[1.0, 2.0], [-1.0, -2.0]])
y = np.array([1, 0])
clf.partial_fit(X, y)
probs = clf.predict_proba(X)
assert probs.shape == (2, 2)
print("[OK] Streaming prequential inference verified")

# 3. Test ULC-v5
ulc = UnifiedLearningControllerV5(n_features=2, n_classes=2)
directive, telemetry = ulc.step(X, y)
print(f"[OK] ULC-v5 operational (Initial Tier: {directive.tier.value})")

# 4. Check optional framework availability
try:
    import torch
    print(f"[Optional] PyTorch available: {torch.__version__}")
except ImportError:
    print("[Optional] PyTorch: Not installed (optional extra 'robust-adapt[torch]')")

try:
    import sklearn
    print(f"[Optional] Scikit-Learn available: {sklearn.__version__}")
except ImportError:
    print("[Optional] Scikit-Learn: Not installed (optional extra 'robust-adapt[sklearn]')")

try:
    import safetensors
    print(f"[Optional] SafeTensors available: {safetensors.__version__}")
except ImportError:
    print("[Optional] SafeTensors: Not installed (optional extra 'robust-adapt[safetensors]')")

print("==================================================")
print("Environment Verification: ALL CHECKS PASSED")
print("==================================================")
```

Run it via:
```bash
python check_environment.py
```
