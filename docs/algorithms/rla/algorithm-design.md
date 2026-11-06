# RLA 3.0: Algorithm Design & Mathematical Formulation

RLA 3.0 implements a multi-stage defense against noisy labels in continuous streaming settings.

---

## 1. Multi-Signal Scoring Equations

Given incoming sample $(x_i, \tilde{y}_i)$ and current model probability distribution $p(x_i) \in \Delta^{K-1}$:

### Signal 1: Prediction Margin
$$s_{\text{margin}} = p_{(1)} - p_{(2)}$$
When $s_{\text{margin}} \approx 1.0$, the model is highly decisive; when $s_{\text{margin}} \approx 0.0$, the instance lies near the decision boundary.

### Signal 2: Spatial $k$-Nearest-Neighbor Agreement
Over recent spatial buffer $B_{\text{spatial}}$ of size $N_{\text{buf}}$:
$$s_{\text{neighbor}} = \frac{1}{k} \sum_{j \in \mathcal{N}_k(x_i)} \mathbb{I}(\tilde{y}_j = \tilde{y}_i)$$
If neighboring samples disagree with $\tilde{y}_i$, the reported label is statistically suspect.

### Signal 3: Temporal Stability
Agreement across a sliding temporal window of recent predictions $H_{\text{temp}}$:
$$s_{\text{temporal}} = \frac{1}{|H_{\text{temp}}|} \sum_{\tau \in H_{\text{temp}}} \mathbb{I}(\hat{y}_{\tau} = \tilde{y}_i)$$

### Composite Reliability Score
$$r_i = w_m s_{\text{margin}} + w_n s_{\text{neighbor}} + w_t s_{\text{temporal}}$$
where $w_m + w_n + w_t = 1.0$ (defaults: $w_m=0.4, w_n=0.4, w_t=0.2$).

---

## 2. Asymmetric Noise Correction

For asymmetric noise with estimated transition probability $\hat{T}_{kj}$, the corrected posterior probability is computed via Bayes' theorem:

$$P(y = k \mid x, \tilde{y} = j) = \frac{\hat{T}_{kj} \cdot P(y = k \mid x)}{\sum_{m=0}^{K-1} \hat{T}_{mj} \cdot P(y = m \mid x)}$$

This eliminates systematic annotation bias and recovers unbiased gradient estimates during training updates.
