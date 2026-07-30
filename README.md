# 🛡️ VeriAI — Real-Time AI & Live Web Fact-Checker

> **VeriAI** is an advanced, autonomous Real-Time Fact-Checking and Misinformation Detection Engine that combines **Machine Learning Natural Language Processing (NLP)** with **Real-Time Live Web Search & NLI Entailment Verification**.

---

## ✨ Features

- 🌐 **Real-Time Live Web Verification**: Queries 50,000+ live web news feeds and RSS streams to verify breaking claims, movie release dates, sports news, and corporate announcements.
- 🎯 **AI Subject-Entity & Temporal Consistency Engine**: Detects entity-substitution scams (e.g. *Airtel vs Reliance Jio*) and date mismatches (e.g. *August 15 vs Diwali 2026*).
- 💡 **Explainable AI (SHAP Visualization)**: Displays word-level feature contributions and linguistic risk scores using interactive Plotly charts.
- 🎨 **Modern Dark Glassmorphic UI**: High-end user interface built with Google Fonts (`Outfit` + `Space Grotesk`), dynamic progress radars, character counters, and 1-click test prompts.
- ⚡ **Zero-API-Key Architecture**: Operates using open RSS feeds and scikit-learn models without requiring paid third-party API keys.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.13, Flask, Scikit-Learn, NLTK, NumPy, Pandas
- **Live Search**: Google News RSS Engine, DuckDuckGo Search (`ddgs`)
- **Explainability**: SHAP (SHapley Additive exPlanations), Plotly.js
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism & Cyber Mesh Design), Bootstrap 5, FontAwesome 6

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/VeriAI-Fact-Checker.git
cd VeriAI-Fact-Checker
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python3 app.py
```
Open your browser and navigate to **`http://localhost:5001`**.

---

## 📸 Interface Preview

- **Hero Verdict Card**: Prominent status badges (`VERIFIED AS REAL NEWS` / `FLAGGED AS FAKE`), confidence score progress meter, and rationale summary.
- **Live Web Evidence**: Clickable source cards with domain tags, article snippets, and publication timestamps.
- **SHAP Feature Chart**: Color-coded linguistic risk bars vs real news reporting style.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
