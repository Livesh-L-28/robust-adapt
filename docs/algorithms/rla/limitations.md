# RLA 3.0: Known Limitations & Adversarial Boundaries

---

## 1. High Recall Does Not Guarantee Adversarial Defense

- **Crucial Security Distiction**: In adversarial data poisoning scenarios, maintaining high recall on nominal test datasets does **not** establish a bulletproof security defense.
- **Risk**: An intelligent adversary who possesses full knowledge of the spatial $k$-NN buffer can construct clustered poison instances that agree with each other, fooling neighborhood consensus.
- **Guidance**: RLA provides robust statistical filtering against stochastic and asymmetric label errors; for cryptographic or adversarial threat models, combine RLA with robust signature verification and anomaly detection.

## 2. Cold-Start Initialization Sensitivity

- **Behavior**: During the first 10-20 steps of a stream, the model's prediction margin $s_{\text{margin}}$ and spatial history buffer $B_{\text{spatial}}$ are not yet populated with sufficient reference instances.
- **Consequence**: Initial reliability estimates have higher variance until the spatial buffer reaches at least $k$ instances.
- **Recommendation**: Set a burn-in period or initialize with a modest pre-trained warm-up buffer where available.

## 3. High Noise Regimes Exceeding 50%

- **Behavior**: If label corruption exceeds $50\%$ on a specific class, majority neighborhood agreement reverses, causing the clean minority to be perceived as outliers.
- **Mitigation**: Enable `security_mode=True` or supply domain class prior estimates to anchor the transition matrix.
