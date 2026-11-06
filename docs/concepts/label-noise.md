# Label Noise & Sample Reliability

In real-world data streams, ground truth labels $y \in \{0, \dots, K-1\}$ are frequently corrupted, producing an observed noisy label $\tilde{y}$.

---

## 1. Noise Taxonomy

```
+-------------------------------------------------------------------------+
| Uniform Symmetric Noise                                                 |
| Any true class k is flipped to any other class with equal probability: |
| P(y_tilde = j | y = k) = eta / (K - 1)                                   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Asymmetric (Class-Conditional) Noise                                    |
| Corruption probability depends specifically on the source and target:    |
| P(y_tilde = j | y = k) = T_{kj} (Transition Matrix T)                    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
| Instance-Dependent Feature Noise                                        |
| Corruption probability is a function of both features x and class y:    |
| P(y_tilde = j | x, y = k)                                               |
+-------------------------------------------------------------------------+
```

In high-stakes domains (fraud detection, cybersecurity, medical imaging), label noise is almost always **asymmetric**:
- Fraudulent transactions are often mistakenly labeled as legitimate (false negative in annotation).
- Legitimate transactions are rarely mislabeled as fraud.

---

## 2. Multi-Signal Reliability Estimation

AdaptiveML estimates the true reliability score $r_i \in [0, 1]$ of each incoming sample by synthesizing three orthogonal signals:

### 1. Prediction Margin & Entropy
High model certainty indicates high sample reliability:
$$s_{\text{margin}} = p_{(1)} - p_{(2)}$$
where $p_{(1)}$ and $p_{(2)}$ are the top two predicted class probabilities.

### 2. Spatial Neighborhood Consistency ($k$-NN)
The fraction of the sample's $k$ nearest neighbors in feature space that agree with the reported label $\tilde{y}_i$:
$$s_{\text{neighbor}} = \frac{1}{k} \sum_{j \in \mathcal{N}_k(x_i)} \mathbb{I}(\tilde{y}_j = \tilde{y}_i)$$

### 3. Temporal Consistency
Agreement across sequential predictions over a sliding temporal buffer $H_t$:
$$s_{\text{temporal}} = \frac{1}{|H_t|} \sum_{\tau \in H_t} \mathbb{I}(\hat{y}_{\tau} = \tilde{y}_i)$$

### Composite Reliability Score
The final scalar reliability is a weighted linear combination:
$$r_i = w_m s_{\text{margin}} + w_n s_{\text{neighbor}} + w_t s_{\text{temporal}}$$

Samples with $r_i < \tau_{\text{noise}}$ are either downweighted in the loss function or filtered out before training, insulating the model from corrupt updates.
