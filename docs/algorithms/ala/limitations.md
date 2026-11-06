# ALA 3.0: Known Limitations & Failure Modes

Understanding when an algorithm should *not* be applied is critical for production reliability.

---

## 1. High-Dimensional Sparse Text/Embeddings

- **Behavior**: Hoeffding Trees evaluate information gain split candidates across continuous feature dimensions. When feature dimensionality exceeds several hundred sparse dimensions ($d > 500$, such as TF-IDF or large embedding bags), tree leaf statistical split computations slow down.
- **Recommendation**: Apply dimensionality reduction (PCA, TruncatedSVD) or use linear SGD classifiers (`SGDClassifier`) before ingesting into `AdaptiveClassifier`.

## 2. Extremely Low Grace Periods Under High Noise

- **Behavior**: Setting `grace_period < 5` in high-variance or noisy streams causes leaf nodes to attempt split evaluations before sufficient sample statistics are accumulated. This leads to sub-optimal, noisy splits that degrade tree depth efficiency.
- **Recommendation**: Set `grace_period >= 20` for noisy streams to ensure statistical stability.

## 3. Delayed Label Streams

- **Behavior**: If true labels $y_t$ arrive with significant delay ($\Delta t \gg 100$ steps), prequential evaluation cannot immediately confirm drift.
- **Recommendation**: Use `DelayedLabelQueue` (`adaptive_ml.ala.delayed_labels`) to buffer unlabelled predictions and match them asynchronously when feedback arrives.
