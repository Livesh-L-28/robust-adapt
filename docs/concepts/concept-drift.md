# Concept Drift Fundamentals

In streaming machine learning, **concept drift** refers to changes in the joint probability distribution of the data over time $t$:

$$P_{t}(X, Y) \neq P_{t-1}(X, Y)$$

---

## 1. Types of Concept Drift

```
Feature Value / Time --->

Abrupt Drift:
[ Concept A: P(Y|X) ] --------> | Shock | --------> [ Concept B: P(Y|X) ]

Gradual Drift:
[ Concept A ] ====> [ Transitional Mixture A & B ] ====> [ Concept B ]

Recurring Drift:
[ Concept A ] -------> [ Concept B ] -------> [ Concept A Returns ]
```

### Abrupt Drift
- A sudden, discontinuous change in the data distribution.
- *Examples*: A sudden macroeconomic policy change, COVID-19 lockdown announcement, or hardware sensor failure.
- *Challenge*: The model must rapidly discard outdated statistical split criteria or reset without over-reacting to transient noise.

### Gradual Drift
- A smooth transition where instances from the old and new concepts coexist for a duration, with the proportion of new-concept samples increasing over time.
- *Examples*: Changing fashion trends, creeping inflation, mechanical wear and tear.
- *Challenge*: Balancing plasticity (learning the new distribution) with stability (not forgetting valid historical patterns too early).

### Recurring Concept Drift
- A previously active concept reappears after an absence.
- *Examples*: Seasonal shopping spikes, weekday vs. weekend traffic, day vs. night fraud tactics.
- *Challenge*: Storing historical concept representations in bounded memory and restoring them instantaneously without retraining from scratch.

---

## 2. Real vs. Virtual Drift

- **Real Concept Drift**: Changes in the posterior probability $P(Y \mid X)$ with or without changes in $P(X)$. The true decision boundary moves.
- **Virtual (Covariate) Shift**: Changes in the input feature distribution $P(X)$ while the relationship $P(Y \mid X)$ remains unchanged.

---

## 3. Statistical Detection with ADWIN

Adaptive Windowing (**ADWIN**) maintains a variable-sized window $W$ of recent real-valued observations (typically prediction errors $e_i \in \{0, 1\}$).

ADWIN mathematically checks whether two sub-windows $W_0$ and $W_1$ (where $W = W_0 \cdot W_1$) have statistically significant differences in their means:

$$|\hat{\mu}_{W_0} - \hat{\mu}_{W_1}| \ge \epsilon_{\text{cut}}$$

The cut threshold $\epsilon_{\text{cut}}$ is derived from the Hoeffding/Bennett inequality with user confidence $\delta$:

$$\epsilon_{\text{cut}} = \sqrt{\frac{1}{2m} \ln\left(\frac{4 |W|}{\delta}\right)}$$

where $m$ is the harmonic mean of the sub-window lengths. When this condition is met, older samples from $W_0$ are discarded, confirming drift with rigorous theoretical error bounds.
