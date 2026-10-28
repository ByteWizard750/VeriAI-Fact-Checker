# 🛡️ VeriAI — Real-Time Fact Verification & Explainable AI Architecture

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/Framework-Flask%203.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Model-Scikit--Learn%20%7C%20DeBERTa--v3-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="Scikit-Learn" />
  <img src="https://img.shields.io/badge/Explainability-SHAP%20(Linear%20Explainer)-FF6F00?style=for-the-badge" alt="SHAP" />
  <img src="https://img.shields.io/badge/Accuracy-88.93%25-10B981?style=for-the-badge" alt="Accuracy" />
  <img src="https://img.shields.io/badge/Inference%20Latency-0.4%20%C2%B5s-0284C7?style=for-the-badge" alt="Latency" />
  <img src="https://img.shields.io/badge/License-MIT-gray?style=for-the-badge" alt="License" />
</p>

---

## 📖 Overview

**VeriAI** is an advanced, autonomous fact-verification and disinformation detection platform that synthesizes **Explainable Artificial Intelligence (XAI)** with **Real-Time Live Web Evidence Retrieval** and **Atomic Proposition Natural Language Inference (NLI)**.

While standard natural language processing (NLP) classifiers operate as uninterpretable "black boxes" and overfit to publisher stylistic metadata (e.g., attribution verbs like *'said'* and news agency tags like *'Reuters'*), VeriAI establishes a **decoupled Dual-Stream Verification Architecture**:
1. **Stream 1 (Statistical NLP + SHAP):** Evaluates vocabulary density, calculates closed-form Shapley game-theoretic word attributions, and computes an auditable **Journalistic Style Index**.
2. **Stream 2 (Real-Time Web Evidence + NLI):** Decomposes complex multi-clause assertions into atomic propositions, executes asynchronous multi-feed web searches (Google News RSS & DuckDuckGo), and cross-examines evidence using a pre-trained **DeBERTa-v3 cross-encoder** augmented by **Gemini 3.5 reasoning**.

---

## 🎓 Academic Submission & Evaluation Deliverables

This repository contains the complete deliverables for the **Decision Analytics (DA) Final Project Review & Technical Viva** at **Vellore Institute of Technology (VIT Chennai)**:

| Deliverable | File Path | Format & Technical Description |
| :--- | :--- | :--- |
| **Final Academic Report (Word)** | [`submission/VeriAI_Final_Academic_Report.docx`](submission/VeriAI_Final_Academic_Report.docx) | Complete 16-section academic report formatted in Microsoft Word with native tables and embedded 300 DPI figures. |
| **Final Academic Report (PDF)** | [`submission/VeriAI_Final_Academic_Report.pdf`](submission/VeriAI_Final_Academic_Report.pdf) | Publication-grade 7-page PDF compiled with running headers, footers, pagination, and high-res vector graphics. |
| **Final Academic Report (LaTeX)** | [`submission/VeriAI_Final_Academic_Report.tex`](submission/VeriAI_Final_Academic_Report.tex) | Complete IEEEtran/academic journal LaTeX source document with mathematical equations and citations. |
| **Final Review Slide Deck** | [`submission/VeriAI_Final_Presentation.pptx`](submission/VeriAI_Final_Presentation.pptx) | Professional 16-slide widescreen (16:9) presentation designed for university project reviews and technical viva defenses. |
| **Empirical Benchmark Records** | [`submission/experiment_results.json`](submission/experiment_results.json) | Full raw evaluation records covering 5 baseline models, 7 formal XAI metrics, and hyperparameter sensitivity sweeps. |
| **High-Resolution Figures** | [`submission/figures/`](submission/figures/) | 6 publication-ready 300 DPI figures (`fig1` architecture through `fig6` sensitivity analysis). |

### 📊 Publication-Grade Figure Inventory

* **Figure 1**: [System Architecture Diagram](submission/figures/fig1_architecture.png) — Dual-stream pipeline linking linguistic SHAP attribution with real-time web retrieval.
* **Figure 2**: [Baseline Performance Comparison](submission/figures/fig2_baseline_comparison.png) — 4-panel comparison of Accuracy, F1-Score, ROC-AUC, and latency across 5 classifiers.
* **Figure 3**: [Confusion Matrix](submission/figures/fig3_confusion_matrix.png) — Normalized confusion matrix for deployed Logistic Regression model ($n=3,000$).
* **Figure 4**: [Global SHAP Feature Importance](submission/figures/fig4_shap_global_importance.png) — Top 10 True-predictive vs. Top 10 Fake-predictive tokens exposing publisher shortcut bias.
* **Figure 5**: [XAI Faithfulness Ablation](submission/figures/fig5_xai_faithfulness_ablation.png) — Top-K vs. Random ablation comprehensiveness and sufficiency retention curves.
* **Figure 6**: [Hyperparameter Sensitivity Analysis](submission/figures/fig6_sensitivity_analysis.png) — Validation F1 curves across vocabulary capacity (1k–15k) and regularization parameter $C$ ($0.01$–$10.0$).

---

## 🔬 Core Academic Breakthrough: Discovering "Linguistic Shortcuts"

When natural language classifiers are trained on static corpora such as **ISOT** (44.9k articles) or **LIAR** (12.8k statements), they inevitably overfit to structural tokens associated with professional newsroom editing rather than underlying factual truth.

Our **Global SHAP Feature Attribution** revealed this phenomenon quantitatively:

```
[TOP TRUE INDICATORS]                             [TOP FAKE INDICATORS]
said             (+8.42) 🟩                       video            (-11.57) 🟥
presid donald    (+5.20) 🟩                       via              (-8.48)  🟥
reuter           (+5.02) 🟩                       imag             (-7.40)  🟥
wednesday        (+4.53) 🟩                       imag via         (-4.64)  🟥
thursday         (+3.95) 🟩                       hillari          (-4.46)  🟥
tuesday          (+3.71) 🟩                       watch            (-4.40)  🟥
spokesman        (+3.11) 🟩                       gop              (-3.93)  🟥
```

> **The Problem:** A completely fabricated narrative written in formal wire syntax (*"Reuters reported on Thursday that WHO declared a new tax..."*) will trick standard NLP models into high-confidence `True` predictions. Conversely, genuine breaking news with informal or accident vocabulary gets falsely flagged as `Fake`.  
>  
> **The VeriAI Solution:** VeriAI's **Live Web Evidence Stream** cross-references the claim against contemporary news feeds. If no corroboration exists, the **DeBERTa NLI module overrides the linguistic prior**, eliminating publisher bias.

---

## 📈 Empirical Evaluation & Benchmarks

All models were evaluated on a **stratified holdout test set of 3,000 samples** (balanced 50/50 True/Fake) sampled from a consolidated benchmark pool of **57,689 records**:

### 1. Baseline Model Performance

| Model Architecture | Accuracy | Precision | Recall | Macro F1 | ROC-AUC | Brier Loss | ECE (10-bin) | Latency / Sample |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Deployed)** | **88.93%** | **0.8741** | **0.9161** | **0.8946** | **0.9625** | **0.0778** | **0.0403** | **0.0004 ms (0.4 µs)** |
| **Multinomial Naive Bayes** | 85.33% | 0.8551 | 0.8596 | 0.8573 | 0.9465 | 0.0939 | 0.0315 | 0.0009 ms (0.9 µs) |
| **Random Forest (100 Trees)** | 88.80% | 0.8373 | 0.9701 | 0.8988 | 0.9613 | 0.1119 | 0.1708 | 0.0128 ms (12.8 µs) |
| **XGBoost (100 Trees)** | 89.13% | 0.8424 | 0.9694 | 0.9015 | 0.9640 | 0.0728 | 0.0188 | 0.0033 ms (3.3 µs) |
| **LightGBM (100 Trees)** | 89.03% | 0.8441 | 0.9642 | 0.9002 | 0.9627 | 0.0738 | 0.0203 | 0.0021 ms (2.1 µs) |

### 2. Formal Explainable AI (XAI) Metrics

| Formal XAI Metric | Mathematical Formulation | Empirical Result | Academic Interpretation |
| :--- | :--- | :---: | :--- |
| **Faithfulness (Comprehensiveness)** | $\Delta P = P(y \mid x) - P(y \mid x \setminus S_k)$ | **0.1275** (top-10) vs. **0.0465** (random) | Removing top-10 SHAP tokens drops confidence by **12.75%** ($2.7\times$ greater drop than random ablation). |
| **Sufficiency** | $\text{Ratio} = P(y \mid S_k) / P(y \mid x)$ | **0.8890 (88.90%)** | Retaining **only the top 10 tokens** preserves **88.90%** of the full model prediction probability. |
| **Fidelity** | Pearson correlation $r(f(x), g(x))$ | **$r = 0.9984$** ($p < 0.001$) | Near-perfect alignment between Linear Explainer surrogate and model decision boundary. |
| **Stability / Robustness** | Jaccard index $J(E(x), E(x_{\text{perturbed}}))$ | **1.0000** | Top-5 explanatory tokens are completely invariant under localized typo and character noise. |
| **Explanation Sparsity** | Gini Concentration Index over $\phi$ | **0.4954** | Attributions are concentrated in a compact, human-interpretable subset of active tokens. |
| **Actionability** | Minimum feature flips to invert $\operatorname{argmax} f(x)$ | **148.27 tokens** | High decision boundary margin preventing trivial adversarial token tampering. |
| **Confidence Calibration** | Expected Calibration Error (ECE across 10 bins) | **$\text{ECE} = 0.0403$** ($\text{Brier} = 0.0778$) | Predicted confidence scores accurately mirror observed empirical accuracy rates. |

---

## 🏗️ System Architecture

```text
                               ┌────────────────────────────────────────────────────────┐
                               │                    User Claim Input                    │
                               │   "Assam student found dead in hostel room as police   │
                               │          launch preliminary investigation."            │
                               └───────────────────┬────────────────────────────────────┘
                                                   │
                             ┌─────────────────────┴─────────────────────┐
                             ▼                                           ▼
               [STREAM 1: Linguistic & SHAP Engine]        [STREAM 2: Web Evidence Engine]
               • TF-IDF Vectorization (10,000 n-grams)     • Dynamic Boolean Query Formulation
               • Calibrated Logistic Regression Model      • Google News RSS + DuckDuckGo Feeds
               • Closed-Form Linear SHAP Attribution       • Domain Authority Ranking & Deduplication
                             │                                           │
                             ▼                                           ▼
               [Linguistic Credibility Profile]            [Atomic NLI Reasoning Engine]
               • Interactive Token Attribution             • Claim Decomposition (Sub-Propositions)
               • Journalistic Style Index (0–100%)         • DeBERTa-v3 Cross-Encoder Entailment
               • Promotional & Emotional Risk Indicators   • Gemini 3.5 Subject-Entity Consistency
                             │                                           │
                             └─────────────────────┬─────────────────────┘
                                                   ▼
                                     [Calibrated Hybrid Synthesis]
                               • Reconciles Linguistic Style with Live Ground Truth
                               • Overrides Stylistic Shortcut False Positives
                               • Unified Verdict: VERIFIED / CONTRADICTED / PARTIAL
```

---

## 🎯 5 Live Demo Scenarios (Viva & Review Cheatsheet)

Use these curated demo claims during presentations to showcase different technical capabilities of VeriAI:

### 1. Verified Real News (Scientific Milestone)
* **Claim:** `ISRO successfully launched Chandrayaan-3 and landed the Vikram lander on the Moon.`
* **Demonstrates:** High credibility, green SHAP attribution on institutional verbs (`launched`, `successfully`), and multiple corroborated live evidence cards.
* **Expected Verdict:** `VERIFIED AS REAL NEWS` (Confidence: 95–100%).

### 2. Viral Social Media Scam (Phishing Hoax)
* **Claim:** `Government announced free 500GB 5G recharge for all mobile users on WhatsApp.`
* **Demonstrates:** Red SHAP attribution on clickbait tokens (`free`, `recharge`, `whatsapp`), high promotional risk flag, and fact-checker contradiction alerts.
* **Expected Verdict:** `FLAGGED AS FAKE / CONTRADICTED`.

### 3. The "Linguistic Shortcut Bias" Breakthrough ⭐ *(Star Technical Viva Demo)*
* **Claim:** `Reuters reported on Thursday that WHO declared a mandatory global salt tax effective November.`
* **Demonstrates:** **Dual-Stream Intervention!** Standalone NLP models get fooled by wire keywords (`Reuters`, `reported`, `Thursday`). VeriAI's evidence stream detects zero real-world corroboration and overrides the stylistic prior.
* **Expected Verdict:** `UNVERIFIED / CONTRADICTED`.

### 4. Real Breaking News with "Sensational" Vocabulary *(Evidence Stream Rescue)*
* **Claim:** `Assam student found dead in hostel room as police launch preliminary investigation.`
* **Demonstrates:** Traditional bag-of-words models penalize words like `dead` and `police`. VeriAI retrieves regional police and municipal press bulletins to validate the story.
* **Expected Verdict:** `VERIFIED AS REAL NEWS`.

### 5. Nuanced Multi-Clause Assertion *(Atomic Claim Decomposition)*
* **Claim:** `Elon Musk acquired Twitter for 44 billion dollars and renamed it to Apple.`
* **Demonstrates:** Clause 1 is True (acquired for $44B), but Clause 2 is False (renamed to X, not Apple). Shows the atomic decomposition accordion displaying one entailed proposition and one contradicted proposition.
* **Expected Verdict:** `PARTIALLY SUPPORTED / MIXED`.

---

## 📂 Repository Structure

```text
fake_news_detect/
│
├── app.py                         # Primary Flask web application entrypoint (python app.py)
├── fake_news_detector.py          # Statistical NLP classifier & SHAP Linear Explainer
├── verification_agent.py          # Multi-stage claim verification & evidence corroboration agent
├── evidence_collector.py          # Asynchronous web evidence retrieval (Google News RSS & DuckDuckGo)
├── gemini_verifier.py             # Structured reasoning, entity extraction, and claim decomposition
├── nli_verifier.py                # Neural Transformer NLI cross-encoder (DeBERTa-v3-small)
├── requirements.txt               # Python package dependencies
├── README.md                      # Project documentation & submission guide
├── LICENSE                        # Open-source MIT License
├── .env.example                   # Environment configuration template
│
├── submission/                    # 🎓 FINAL ACADEMIC SUBMISSION DELIVERABLES
│   ├── VeriAI_Final_Academic_Report.docx  # Full 16-section report in Microsoft Word
│   ├── VeriAI_Final_Academic_Report.pdf   # Publication-ready PDF with running headers & footers
│   ├── VeriAI_Final_Academic_Report.tex   # Academic LaTeX source document
│   ├── VeriAI_Final_Presentation.pptx     # 16-slide final review deck (16:9 widescreen)
│   ├── experiment_results.json            # Verified empirical benchmark records
│   └── figures/                           # 6 publication-ready 300 DPI figures (fig1–fig6)
│
├── scripts/                       # ⚙️ BENCHMARK & DELIVERABLE BUILD SCRIPTS
│   ├── run_experiments.py         # Empirical evaluation & XAI metric benchmark suite
│   ├── generate_reports.py        # Compiles DOCX, PDF, and LaTeX reports
│   └── build_presentation.py      # Compiles PowerPoint presentation
│
├── tests/                         # 🧪 AUTOMATED TESTS & AUDIT SCRIPTS
│   ├── run_audit.py               # Rigorous multi-claim verification audit
│   ├── run_live_api_tests.py      # Endpoint integration tests
│   ├── test_verification_agent.py # Verification agent unit tests
│   ├── test_gemini_fact_checker.py# Category-based claim tests
│   └── test_examples.txt          # Sample test prompts & claims
│
├── templates/                     # 🌐 JINJA2 FRONTEND UI TEMPLATES
│   ├── index.html                 # Interactive verification dashboard
│   ├── base.html                  # Global layout & navigation bar
│   └── about.html                 # Architectural documentation page
│
├── models/                        # 🧠 TRAINED MACHINE LEARNING ARTIFACTS
│   └── fake_news_model.pkl        # Serialized TF-IDF + Logistic Regression model
│
└── data/                          # 📊 DATASETS (ISOT & LIAR Corpora)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10 to 3.13
* Virtual environment tool (`venv`)
* Internet connection (for live RSS news feeds and pre-trained DeBERTa weights)

### 2. Installation
```bash
# 1. Clone repository
git clone https://github.com/ByteWizard750/VeriAI-Fact-Checker.git
cd VeriAI-Fact-Checker

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
```bash
cp .env.example .env
# Open .env and add your GEMINI_API_KEY if testing generative decomposition fallback
```

### 4. Running the Web Application
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5001`**

### 5. Running Tests & Audits
```bash
# Run the verification audit suite
python tests/run_audit.py

# Run live endpoint tests
python tests/run_live_api_tests.py
```

### 6. Reproducing Benchmarks & Regenerating Deliverables
```bash
# Re-run full 5-model benchmark & XAI metric evaluation
python scripts/run_experiments.py

# Recompile final DOCX, PDF, and LaTeX academic reports
python scripts/generate_reports.py

# Recompile final 16-slide PowerPoint presentation
python scripts/build_presentation.py
```

---

## 👥 Project Team & Institutional Information

* **Rohan** (`rayavarapurohan2006@gmail.com`)
* **Lakshya Kumar Singh** (`lakshyakumarsingh1@gmail.com`)

* **Department:** School of Computer Science and Engineering (SCOPE)
* **Institution:** Vellore Institute of Technology (VIT), Chennai, India
* **Curriculum / Review:** Decision Analytics (DA) Final Project Review & Technical Viva (2026)

---

## 📚 Key Academic References

1. **Lundberg, S. M., & Lee, S.-I. (2017).** A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30.
2. **Ribeiro, M. T., Singh, S., & Guestrin, C. (2016).** "Why should I trust you?": Explaining the predictions of any classifier. *ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD)*, 1135–1144.
3. **Wang, W. Y. (2017).** "Liar, liar pants on fire": A new benchmark dataset for fake news detection. *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (ACL)*, 422–426.
4. **Thorne, J., Vlachos, A., Christodoulopoulos, C., & Mittal, A. (2018).** FEVER: A large-scale dataset for fact extraction and verification. *Proceedings of NAACL-HLT*, 809–819.
5. **He, P., Liu, X., Gao, J., & Chen, W. (2021).** DeBERTa: Decoding-enhanced BERT with disentangled attention. *International Conference on Learning Representations (ICLR)*.
6. **Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017).** On calibration of modern neural networks. *International Conference on Machine Learning (ICML)*, 1321–1330.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.
