# Minority Intelligence: Algorithm Design & Mathematical Formulation

Adaptive Minority Intelligence 2.0 addresses extreme class imbalance through Bayesian prior modeling, sublinear loss weighting, and feedback control.

---

## 1. Beta-Binomial Conjugate Prior Tracking

Let minority arrivals be modeled as a Bernoulli process with unknown parameter $\pi \in (0, 1)$. Using a conjugate $\text{Beta}(\alpha, \beta)$ prior with exponential discount factor $\gamma \in (0, 1)$:

$$\alpha_{t} = \gamma \alpha_{t-1} + y_t$$
$$\beta_{t} = \gamma \beta_{t-1} + (1 - y_t)$$

The posterior mean estimate of the streaming class prior is:
$$\hat{\pi}_t = \frac{\alpha_t}{\alpha_t + \beta_t}$$

By choosing default hyper-priors $\alpha_0 = 1.0, \beta_0 = 100.0$, the tracker initializes with an uninformative prior centered around $1\%$, adapting smoothly as samples arrive.

---

## 2. Sublinear Cost Scaling

Linear inverse frequency weighting ($w_1 = 1 / \pi$) leads to severe gradient variance spikes when $\pi \to 0$ (e.g. $w_1 = 1,000$ when $\pi = 0.001$), destabilizing gradient updates.

AdaptiveML employs **sublinear cost power scaling**:
$$w_1 = \left(\frac{1}{\hat{\pi}_t}\right)^\alpha, \quad \alpha \in (0, 1) \quad (\text{default: } \alpha = 0.52)$$

When $\pi = 0.001$, sublinear scaling provides a bounded, stable penalty multiplier ($w_1 \approx 36.3$) rather than $1,000$, ensuring stable optimization.

---

## 3. Dynamic PID Threshold Regulation

To maintain a target false-positive budget (e.g., $E_{\text{target}} = 1.5$ false alarms per 1,000 samples), the classification threshold $\theta_t$ is dynamically regulated via a Proportional-Integral-Derivative (PID) control loop:

$$e_t = \text{FPR}_t - \text{FPR}_{\text{target}}$$
$$\Delta \theta_t = K_p e_t + K_i \int e_t \, dt + K_d \frac{de_t}{dt}$$
$$\theta_{t+1} = \text{clip}\left(\theta_t + \Delta \theta_t, \theta_{\text{min}}, \theta_{\text{max}}\right)$$

- **Proportional term ($K_p$)**: Corrects immediate spikes in false positives.
- **Integral term ($K_i$)**: Eliminates steady-state budget drift. Anti-windup clamping prevents integral saturation.
- **Derivative term ($K_d$)**: Dampens threshold oscillation.
- **Deadband ($\tau_{\text{db}}$)**: Ignores micro-fluctuations $|e_t| < \tau_{\text{db}}$ to preserve decision stability.
