# Fake News Detector with SHAP Explanations

An advanced machine learning system that detects fake news and provides detailed explanations using SHAP (SHapley Additive exPlanations) values. The system includes a user-friendly web interface for easy interaction.

## Features

- **Multi-Model Approach**: Uses Random Forest, XGBoost, LightGBM, and Logistic Regression
- **SHAP Explanations**: Provides detailed explanations for why news is classified as fake or true
- **Multiple Datasets**: Trained on 50,000+ examples from various sources
- **Interactive Web Interface**: Beautiful, responsive web UI with real-time analysis
- **Visual Analytics**: Interactive charts showing feature importance

## Datasets Used

1. **News Dataset (Archive)**: 44,000+ news articles from reliable and unreliable sources
2. **LIAR Dataset**: 12,800+ fact-checked statements from PolitiFact
3. **Combined Training**: Over 50,000 labeled examples for robust model training

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd PROJECT_ALPHA
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Train the model** (first time only)
   ```bash
   python fake_news_detector.py
   ```
   This will:
   - Load and preprocess all datasets
   - Train multiple ML models
   - Select the best performing model
   - Save the trained model with SHAP explainer

4. **Run the web application**
   ```bash
   python app.py
   ```

5. **Open your browser** and go to `http://localhost:5000`

## Usage

### Web Interface

1. Open the web application in your browser
2. Paste news text or article in the text area
3. Click **Analyze News** to get predictions
4. View results including:
   - Fake/True prediction with confidence
   - Probability scores
   - SHAP feature importance visualization
   - Top contributing features with explanations

### Python API

```python
from fake_news_detector import FakeNewsDetector

# Initialize detector
detector = FakeNewsDetector()
detector.load_model('models/fake_news_model.pkl')

# Analyze text
result = detector.predict_with_explanation("Your news text here")
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']}")
```

## How It Works

1. **Text Preprocessing**:
   - Converts text to lowercase
   - Removes special characters and digits
   - Tokenizes and removes stopwords
   - Applies stemming

2. **Feature Extraction**:
   - Uses TF-IDF vectorization
   - Extracts n-grams (1-2)
   - Creates 5000 features maximum

3. **Model Training**:
   - Trains multiple models simultaneously
   - Selects best performing model
   - Uses stratified train-test split

4. **SHAP Explanations**:
   - Calculates feature importance for each prediction
   - Identifies words/phrases that influence the decision
   - Provides positive/negative contribution scores

## Model Performance

The system automatically selects the best performing model from:

- **Random Forest**: Ensemble method for robust predictions
- **XGBoost**: Gradient boosting for high accuracy
- **LightGBM**: Fast gradient boosting framework
- **Logistic Regression**: Linear model for interpretability

Typical performance metrics:

- **Accuracy**: ~90–91% (varies by dataset and model)
- **Precision/Recall**: Balanced for both fake and true classes

## File Structure

```text
PROJECT_ALPHA/
├── data/                          # Datasets
│   ├── archive/                   # News articles dataset
│   ├── liar_dataset/             # LIAR fact-checking dataset
│   └── News-_dataset/            # Additional news dataset
├── templates/                     # HTML templates
│   ├── base.html                 # Base template
│   ├── index.html                # Main page
│   └── about.html                # About page
├── models/                        # Saved models (created after training)
│   └── fake_news_model.pkl       # Trained model with SHAP explainer
├── fake_news_detector.py         # Main ML model class
├── app.py                        # Flask web application
├── test_examples.txt             # Ready-made examples for testing
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Technical Details

### Machine Learning Pipeline

1. **Data Loading**: Combines multiple datasets with proper labeling.
2. **Preprocessing**: NLTK-based text cleaning and normalization.
3. **Vectorization**: TF-IDF with optimized parameters.
4. **Model Selection**: Automated comparison of multiple algorithms.
5. **Explainability**: SHAP integration for transparent predictions.

### Web Application

- **Backend**: Flask with RESTful API
- **Frontend**: Bootstrap 5 with responsive design
- **Visualization**: Plotly.js for interactive charts
- **Real-time**: AJAX-based predictions without page refresh

## Running the Project (Step‑by‑Step)

### Local setup

1. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Windows cmd
   .venv\Scripts\activate.bat
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Train the model** (first time or after changing the training code):
   ```bash
   python fake_news_detector.py
   ```
   This will create `models/fake_news_model.pkl`.

4. **Start the web app**:
   ```bash
   python app.py
   ```

5. **Open the UI**:
   - Go to `http://localhost:5000` in your browser.
   - Paste any news text or use the examples from `test_examples.txt`.

## Testing the Model

- **Built‑in examples**:
  - **File**: `test_examples.txt`
  - **Contains**:
    - Fake news examples (conspiracy, health scare, scams, hoaxes, clickbait)
    - Legitimate news examples (science, tech, business, local news)
    - Edge cases (satire, opinion, mixed content)
    - Short snippets for quick testing

- **How to use**:
  1. Open `test_examples.txt`.
  2. Copy any example text block.
  3. Paste it into the text area on `http://localhost:5000`.
  4. Click **Analyze News** and inspect:
     - **Prediction** (Fake / True)
     - **Confidence & probabilities**
     - **Top contributing features**
     - **SHAP feature importance chart**

## Environment & Compatibility Notes

- **Python version**:
  - Developed and tested with **Python 3.13** on Windows.
  - It should also work on recent 3.x versions (3.9+), but SHAP / NLTK behaviour can vary slightly.

- **NLTK data**:
  - The app automatically downloads required NLTK resources (`punkt`, `stopwords`) if missing.
  - If you see errors mentioning `punkt` or `punkt_tab`, run:
    ```bash
    python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
    ```

- **SHAP compatibility**:
  - The project uses SHAP with tree‑based models.
  - The code contains fallbacks in case the exact SHAP explainer cannot be loaded from disk.
  - Explanations may be simplified if your SHAP version behaves differently, but predictions will still work.

## Important Notes

- **Limitations**:
  - This tool is for educational and research purposes.
  - Results should not be the sole basis for fact-checking.
  - Always verify information through multiple reliable sources.
  - Model performance may vary with different types of content.

## Dependencies

- **pandas**: Data manipulation and analysis
- **scikit-learn**: Machine learning algorithms
- **nltk**: Natural language processing
- **xgboost**: Gradient boosting framework
- **lightgbm**: Fast gradient boosting
- **shap**: Model explainability
- **flask**: Web framework
- **plotly**: Interactive visualizations

## Contributing

This project demonstrates the application of machine learning for fake news detection with explainable AI. It combines multiple datasets and state-of-the-art techniques to provide both accurate predictions and transparent explanations.

## Git & GitHub (Publishing This Project)

You can publish this project to GitHub with the following steps (from the project root):

1. **Initialize git (once)**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Fake News Detector project"
   ```

2. **Create an empty repository on GitHub**:
   - Go to `github.com` → New repository.
   - **Repository name**: e.g. `fake-news-detector` or `project-alpha`.
   - Do **not** add a README / `.gitignore` / license from GitHub (you already have them locally).
   - Copy the **HTTPS** URL of the new repo (e.g. `https://github.com/your-user/fake-news-detector.git`).

3. **Connect local repo to GitHub**:
   ```bash
   git branch -M main
   git remote add origin https://github.com/YOUR-USER/YOUR-REPO.git
   ```

4. **Push the code**:
   ```bash
   git push -u origin main
   ```

5. **(Optional) Ignore large or private data**:
   - Consider adding a `.gitignore` entry for:
     - `data/` (large datasets)
     - `models/` (trained model files)
   - Example `.gitignore` snippet:
     ```gitignore
     __pycache__/
     .venv/
     data/
     models/
     *.log
     ```

After this, your project will be live on GitHub and can be cloned and run using the instructions above.

## License

This project is for educational purposes. The datasets used retain their original licenses and usage restrictions.


