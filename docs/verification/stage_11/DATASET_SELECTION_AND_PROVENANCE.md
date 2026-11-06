# AdaptiveML Stage 11 — Dataset Selection and Provenance Report
## Workstream A: Candidate Dataset Investigation, Provenance Audits, License Verification, and Suitability Matrix

**Document Identifier:** `AML-DOC-STG11-DATA-001`<br>
**Distribution:** `aml-core` v0.1.0.dev0<br>
**Research Stage:** Stage 11 — Real-World Validation & Applied Research<br>
**Target Date:** 2026-11-06<br>
**Status:** VALIDATED — CANDIDATE SELECTION COMPLETE

---

## 1. Executive Summary & Selection Philosophy

Stage 11 transitions AdaptiveML from synthetic and procedural stream validation to empirical research on genuine real-world datasets. To preserve scientific rigor, datasets were selected according to five strict selection criteria:

1. **Documented Provenance & Established Benchmark Status:** Datasets must possess verifiable academic or industrial origins with recognized peer-reviewed literature citations.
2. **Permissive Open-Source Licensing:** Datasets must be distributed under open licenses (Public Domain, CC0, CC BY 4.0, or Open Database License) permitting scientific research and reproducible benchmarking without proprietary redistribution constraints.
3. **Pillar Alignment:** Datasets must directly challenge the specific hypotheses of the four pillars:
   - **ALA:** Natural temporal distribution shifts and concept drift.
   - **Minority Intelligence:** Severe real-world class imbalance ($\ge 100:1$).
   - **RLA:** Genuine classification tasks with clean reference ground-truth for controlled symmetric/asymmetric label corruption, plus natural annotation uncertainty.
   - **RAO:** Real-world feature representations for deep neural optimization workloads.
   - **ULC-v4.1:** High-dimensional streaming regimes combining drift, noise, and resource limits.
4. **Leakage Immunity:** Datasets must support chronological or strictly isolated train/val/test partitioning.
5. **Compute & Storage Budget Feasibility:** Datasets must run reproducibly on standard workstations within CPU-first memory boundaries.

---

## 2. Dataset Suitability Matrix

| Candidate Dataset | Domain | Instances ($N$) | Features ($D$) | Primary Pillar | Decision | Justification |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **Electricity (Elec2)** | Energy Market | $45,312$ | $8$ | **ALA** | **SELECTED** | Canonical streaming concept drift benchmark. Real market deregulation dynamics. Chronological stream. Public domain. |
| **Credit Card Fraud (ULB)** | Financial Transactions | $284,807$ | $29$ | **Minority / ULC** | **SELECTED** | Canonical extreme imbalance benchmark ($0.172\%$ minority). Real PCA transaction features. Open Database License. |
| **Spambase** | Cybersecurity / NLP | $4,601$ | $57$ | **RLA** | **SELECTED** | Verified clean ground-truth spam/ham labels. $57$ continuous word/character frequencies. Ideal for controlled noise studies. Public domain. |
| **Forest CoverType** | Ecology / Remote Sensing | $581,012$ | $54$ | **ALA / RAO** | **SELECTED** | Large-scale multi-class dataset with natural class imbalance ($48\%$ down to $0.47\%$) and real geographical shifts. Public domain. |
| **NOAA Weather** | Meteorology | $18,159$ | $8$ | **ALA** | **DEFERRED** | Concept drift stream is smaller than Electricity and largely redundant with Elec2 dynamics. Kept for secondary validation. |
| **Mammography** | Medical Diagnostics | $11,183$ | $6$ | **Minority** | **DEFERRED** | Low dimensionality ($D=6$); class imbalance ($2.3\%$) is far less challenging than Credit Card Fraud ($0.17\%$). |
| **Airline (Fly)** | Transportation | $5,810,462$ | $13$ | **ALA** | **REJECTED** | Massive file size ($>100\text{ MB}$ compressed, $\approx 1\text{ GB}$ raw); excessive iteration time for multi-seed confirmatory study. |
| **IEEE-CIS Fraud** | E-commerce | $590,540$ | $434$ | **Minority** | **REJECTED** | Kaggle competition terms restrict commercial redistribution; high missingness ($>50\%$ across 200 features) confounds algorithm testing. |
| **Clothing1M** | Computer Vision | $1,000,000$ | Images | **RLA** | **REJECTED** | Multi-gigabyte image archive requiring GPU clusters; contradicts AdaptiveML's CPU-first lightweight scope. |
| **CIFAR-10N** | Computer Vision | $60,000$ | Images | **RLA** | **DEFERRED** | Excellent noisy label benchmark, but image tensor pipelines are evaluated via tabular and feature-extracted models in Stage 11. |

---

## 3. Provenance & Metadata Cards for Selected Datasets

### 3.1 Electricity Market Stream (Elec2)
- **Dataset Name:** Electricity (Elec2)
- **Original Source / Publisher:** Australian National Electricity Market Management Company (NEMMCO) / University of New South Wales.
- **Academic Citation:** Harries, M., & Wales, S. C. (1999). *Splice-2 Exploring the World of Artificial Neural Networks*. Technical Report, UNSW-CSE-TR-9902.
- **OpenML Reference:** OpenML Data ID `151` / `44008`.
- **License:** Public Domain / Open Access.
- **Collection Period:** May 1996 to December 1998 (readings every 30 minutes, totaling 45,312 sequential instances).
- **Target Variable:** `class` (Binary: `UP` if price increased relative to a 24-hour moving average, `DOWN` if decreased).
- **Class Distribution:** `DOWN`: $26,075$ ($57.5\%$), `UP`: $19,237$ ($42.5\%$).
- **Features ($D=8$):**
  1. `date`: Day index ($0.0 - 1.0$).
  2. `day`: Day of week ($1 - 7$).
  3. `period`: Half-hour interval of the day ($0.0 - 1.0$).
  4. `nswprice`: Electricity price in New South Wales.
  5. `nswdemand`: Electricity demand in New South Wales.
  6. `vicprice`: Electricity price in Victoria.
  7. `vicdemand`: Electricity demand in Victoria.
  8. `transfer`: Scheduled electricity transfer between states.
- **Concept Drift Character:** Natural concept drift resulting from state-level market deregulation, fluctuating demand, and changing inter-state bidding strategies.
- **Leakage Prevention:** Must be processed in strict sequential time order; shuffling or future window leakage is strictly prohibited.

---

### 3.2 Credit Card Fraud Detection (ULB)
- **Dataset Name:** Credit Card Fraud Detection
- **Original Source / Publisher:** Machine Learning Group (MLG), Université Libre de Bruxelles (ULB) & Worldline.
- **Academic Citation:** Dal Pozzolo, A., Caelen, O., Johnson, R. A., & Bontempi, G. (2015). *Calibrating Probability with Undersampling for Unbalanced Classification*. IEEE SSCI 2015.
- **OpenML Reference:** OpenML Data ID `42175` / `1597`.
- **License:** Open Database License (ODbL) v1.0.
- **Collection Period:** Two days in September 2013 (European credit card transactions).
- **Target Variable:** `Class` (Binary: `0` for Legitimate, `1` for Fraudulent).
- **Total Observations:** $284,807$ transactions.
- **Class Distribution:**
  - Legitimate (`0`): $284,315$ ($99.828\%$)
  - Fraudulent (`1`): $492$ ($0.172\%$)
  - **Imbalance Ratio:** **$578:1$** (Extreme imbalance)
- **Features ($D=29$):**
  - `Time`: Elapsed seconds since first transaction in dataset.
  - $V_1, V_2, \dots, V_{28}$: Continuous principal components resulting from PCA transformation (anonymized for user confidentiality).
  - `Amount`: Transaction monetary value.
- **Known Limitations:** Features are PCA-transformed, limiting raw domain feature interpretability; however, this mirrors real-world production fraud scoring pipelines.
- **Leakage Prevention:** Sorting by `Time` enables realistic temporal chronological validation with forward-only train/validation/test splits.

---

### 3.3 Spambase Email Classification
- **Dataset Name:** Spambase Dataset
- **Original Source / Publisher:** Mark Hopkins, Erik Reeber, George Forman, Jaap Suermondt (Hewlett-Packard Labs) / UCI Machine Learning Repository.
- **OpenML Reference:** OpenML Data ID `44`.
- **License:** CC BY 4.0 / Open Access.
- **Target Variable:** `class` (Binary: `1` for Spam, `0` for Non-Spam/Ham).
- **Total Observations:** $4,601$ emails.
- **Class Distribution:** Non-spam (`0`): $2,788$ ($60.6\%$), Spam (`1`): $1,813$ ($39.4\%$).
- **Features ($D=57$):**
  - 48 continuous features measuring percentage of words matching specific keywords (e.g. `make`, `address`, `all`, `3d`, `our`).
  - 6 continuous features measuring percentage of characters matching specific punctuation (`(`, `[`, `!`, `$`, `#`).
  - 3 continuous features measuring length of run-length capitalized letter sequences (`capital_run_length_average`, `capital_run_length_longest`, `capital_run_length_total`).
- **Research Role:** Provides a clean, well-calibrated tabular baseline with verified ground-truth labels for evaluating RLA's robustness against controlled symmetric and asymmetric label corruption.

---

### 3.4 Forest CoverType (CovType)
- **Dataset Name:** Forest CoverType
- **Original Source / Publisher:** Jock A. Blackard & Colorado State University / US Forest Service (USFS).
- **OpenML / scikit-learn Reference:** `fetch_covtype` / OpenML ID `150`.
- **License:** Public Domain.
- **Target Variable:** `Cover_Type` (Multi-class: 7 forest cover types, integer $1 - 7$).
- **Total Observations:** $581,012$ instances.
- **Features ($D=54$):**
  - 10 quantitative continuous cartographic variables (elevation, aspect, slope, horizontal/vertical distance to hydrology, roadways, fire points).
  - 4 binary wilderness area indicator columns.
  - 40 binary soil type indicator columns.
- **Class Distribution:**
  - Class 1 (Spruce/Fir): $211,840$ ($36.46\%$)
  - Class 2 (Lodgepole Pine): $283,301$ ($48.76\%$)
  - Class 3 (Ponderosa Pine): $35,754$ ($6.15\%$)
  - Class 4 (Cottonwood/Willow): $2,747$ ($0.47\%$)
  - Class 5 (Aspen): $9,493$ ($1.63\%$)
  - Class 6 (Douglas-fir): $17,367$ ($2.99\%$)
  - Class 7 (Krummholz): $20,510$ ($3.53\%$)
- **Research Role:** Multi-class imbalanced scaling and neural optimization workload for RAO.

---

## 4. Leakage Prevention and Evaluation Directives

1. **Chronological Splitting for Streams:** Both `Electricity` and `Credit Card Fraud` must be evaluated using forward-only time windows. Never shuffle temporal data across train and test partitions.
2. **Preprocessing Isolation:** Scalers (`StandardScaler`, `MinMaxScaler`) must be fitted strictly on the training partition (or incrementally updated via Welford's algorithm during prequential streaming).
3. **Prequential Evaluation Protocol:** On streaming workloads, evaluate each batch via **test-then-train**:
   $$\text{Predict}(X_t) \longrightarrow \text{Compute Error} \longrightarrow \text{Train / Update}(X_t, y_t)$$
4. **No Test-Set Hyperparameter Tuning:** All threshold optimization and architecture hyperparameter choices must be frozen prior to final test partition evaluation.
