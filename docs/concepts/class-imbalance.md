# Class Imbalance & Minority Intelligence

Streaming class imbalance occurs when one or more target classes arrive with extremely low frequency ($<1\%$ or $<0.1\%$ of the stream).

---

## 1. The Imbalance Trap

Under severe class imbalance (e.g. 999 legitimate events vs. 1 fraud event per 1,000 samples):
- A trivial model predicting the majority class exclusively achieves **$99.9\%$ accuracy**.
- However, its minority recall is **$0.0\%$**, rendering it useless for practical fraud detection or security defense.
- Standard loss functions prioritize minimizing total error, effectively suppressing gradients from rare minority classes.

---

## 2. Online Beta-Binomial Prior Tracking

In non-stationary data streams, the true class prior $\pi_t = P_t(Y=1)$ fluctuates over time. AdaptiveML tracks this prior continuously using a **decaying Beta-Binomial Bayesian conjugate prior**:

$$\alpha_{t} = \gamma \alpha_{t-1} + y_t$$
$$\beta_{t} = \gamma \beta_{t-1} + (1 - y_t)$$

where $\gamma \in (0, 1)$ is an exponential discount factor. The expected posterior class prior at step $t$ is:

$$\hat{\pi}_t = \mathbb{E}[\pi \mid \alpha_t, \beta_t] = \frac{\alpha_t}{\alpha_t + \beta_t}$$

This allows the model to immediately detect whether minority arrival frequency is increasing or diminishing without hardcoded historical thresholds.

---

## 3. Dynamic False-Positive Budget Management

In production operations, human review capacity or customer tolerance sets a strict upper bound on the allowable False Positive Rate ($\text{FPR} \le \text{budget}_{\text{FP}}$, e.g. $2\%$).

Instead of using a static decision threshold ($0.50$):
1. The threshold manager dynamically slides threshold $\theta_t \in (0, 1)$ to maximize minority recall subject to:
   $$\text{FPR}(\theta_t) \le \text{budget}_{\text{FP}}$$
2. Threshold adjustments are smoothed with exponential moving averages to prevent oscillation across consecutive samples.
3. Sublinear cost weighting scales loss penalties inversely with prior $\hat{\pi}_t$, ensuring the classifier maintains sharp discrimination boundaries for rare classes.
