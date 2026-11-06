# ALA 3.0: Algorithm Design & Mathematical Formulation

ALA 3.0 integrates tree-based online induction, dynamic windowing, and recurring concept matching into a closed-loop streaming learner (`ALA30AdaptiveLearner`).

---

## 1. Hoeffding Tree Induction Mechanics

At any leaf node $l$ in the streaming decision tree, the learner observes streaming attributes $X$ and labels $y$. After observing a `grace_period` of $n$ samples, the leaf evaluates the information gain $G(X_i)$ for each candidate split attribute $X_i$.

Let $X_a$ and $X_b$ be the attributes with the highest and second-highest information gain. The difference is:
$$\Delta G = G(X_a) - G(X_b)$$

The **Hoeffding Bound** states that with probability $1 - \delta$, the true mean difference is at least $\Delta G - \epsilon$, where:
$$\epsilon = \sqrt{\frac{R^2 \ln(1/\delta)}{2n}}$$
($R = \ln(K)$ for information gain with $K$ classes).

- If $\Delta G > \epsilon$, the leaf node splits on attribute $X_a$ with statistical confidence $1 - \delta$.
- If $\Delta G \le \epsilon$ and $\epsilon < \tau_{\text{tie}}$, a tie is declared and the node splits on $X_a$.

---

## 2. Statistical Concept Fingerprinting

To detect recurring concepts, `ConceptFingerprinter` calculates a compact statistical representation of an observed data batch:

$$\text{FP} = \left[ \mu, \sigma^2, \pi \right]$$
where:
- $\mu \in \mathbb{R}^d$: Feature centroid vector.
- $\sigma^2 \in \mathbb{R}^d$: Feature variance vector.
- $\pi \in \mathbb{R}^K$: Empirical class prior distribution.

### Similarity Function
Similarity between an active fingerprint $\text{FP}_{\text{active}}$ and a stored historical fingerprint $\text{FP}_{\text{stored}}$ is computed via normalized Gaussian kernel distance:

$$D = \frac{1}{d} \sum_{i=1}^d \frac{|\mu_{\text{active}, i} - \mu_{\text{stored}, i}|}{\sqrt{\sigma_{\text{active}, i}^2 + \sigma_{\text{stored}, i}^2 + \epsilon}}$$
$$\text{Sim} = \exp\left(-\frac{1}{2} D^2\right) \in [0, 1]$$

When $\text{Sim} \ge \tau_{\text{sim}}$ (default 0.75-0.82), a recurring concept is declared.
