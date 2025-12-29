import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
import joblib
import shap
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import warnings
warnings.filterwarnings('ignore')

class FakeNewsDetector:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.stemmer = PorterStemmer()
        self.stop_words = None
        self.explainer = None
        
    def download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        # Download punkt_tab for newer NLTK versions
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            try:
                nltk.download('punkt_tab', quiet=True)
            except Exception:
                # If punkt_tab doesn't exist, try alternative
                pass
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
            
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Ensure stopwords are loaded
        if self.stop_words is None:
            self.download_nltk_data()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize - handle both old and new NLTK versions
        tokens = []
        try:
            # Try using word_tokenize
            tokens = word_tokenize(text)
        except (LookupError, Exception) as e:
            # Fallback to regex-based tokenization if NLTK tokenizer fails
            tokens = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        
        # Remove stopwords and stem
        tokens = [self.stemmer.stem(token) for token in tokens 
                 if token not in self.stop_words and len(token) > 2]
        
        return ' '.join(tokens)
    
    def load_and_combine_data(self):
        """Load and combine all datasets"""
        print("Loading datasets...")
        
        # Load CSV datasets (archive and News-_dataset are identical)
        fake_df = pd.read_csv('data/archive/Fake.csv')
        true_df = pd.read_csv('data/archive/True.csv')
        
        # Add labels
        fake_df['label'] = 0  # Fake news
        true_df['label'] = 1  # True news
        
        # Combine CSV data
        csv_data = pd.concat([fake_df, true_df], ignore_index=True)
        csv_data['text_combined'] = csv_data['title'] + ' ' + csv_data['text']
        csv_data = csv_data[['text_combined', 'label']].rename(columns={'text_combined': 'text'})
        
        # Load LIAR dataset
        liar_train = pd.read_csv('data/liar_dataset/train.tsv', sep='\t', header=None)
        liar_test = pd.read_csv('data/liar_dataset/test.tsv', sep='\t', header=None)
        liar_valid = pd.read_csv('data/liar_dataset/valid.tsv', sep='\t', header=None)
        
        # Combine LIAR datasets
        liar_data = pd.concat([liar_train, liar_test, liar_valid], ignore_index=True)
        
        # Process LIAR dataset - convert multi-class to binary
        # Column 1 is label, Column 2 is statement
        liar_data.columns = ['id', 'label', 'statement', 'subject', 'speaker', 'job', 'state', 
                           'party', 'barely_true', 'false', 'half_true', 'mostly_true', 'pants_fire', 'context']
        
        # Convert to binary: false, barely-true, pants-on-fire -> 0 (fake)
        # half-true, mostly-true, true -> 1 (true)
        fake_labels = ['false', 'barely-true', 'pants-on-fire']
        liar_data['binary_label'] = liar_data['label'].apply(lambda x: 0 if x in fake_labels else 1)
        liar_data = liar_data[['statement', 'binary_label']].rename(columns={'statement': 'text', 'binary_label': 'label'})
        
        # Combine all datasets
        combined_data = pd.concat([csv_data, liar_data], ignore_index=True)
        combined_data = combined_data.dropna()
        
        print(f"Total samples: {len(combined_data)}")
        print(f"Fake news samples: {len(combined_data[combined_data['label'] == 0])}")
        print(f"True news samples: {len(combined_data[combined_data['label'] == 1])}")
        
        return combined_data
    
    def prepare_data(self, data, sample_size=10000):
        """Prepare and preprocess data for training"""
        print("Preprocessing text data...")
        
        # Sample data for faster processing (optional)
        if len(data) > sample_size:
            data = data.sample(n=sample_size, random_state=42)
        
        # Preprocess text
        data['processed_text'] = data['text'].apply(self.preprocess_text)
        
        # Remove empty texts
        data = data[data['processed_text'].str.len() > 0]
        
        return data
    
    def train_model(self, data):
        """Train the fake news detection model"""
        print("Training model...")
        
        X = data['processed_text']
        y = data['label']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Vectorize text
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train multiple models and select the best one
        models = {
            'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
            'LogisticRegression': LogisticRegression(random_state=42, max_iter=1000),
            'XGBoost': xgb.XGBClassifier(random_state=42),
            'LightGBM': lgb.LGBMClassifier(random_state=42, verbose=-1)
        }
        
        best_score = 0
        best_model_name = None
        
        for name, model in models.items():
            print(f"Training {name}...")
            model.fit(X_train_vec, y_train)
            y_pred = model.predict(X_test_vec)
            score = accuracy_score(y_test, y_pred)
            print(f"{name} Accuracy: {score:.4f}")
            
            if score > best_score:
                best_score = score
                best_model_name = name
                self.model = model
        
        print(f"\nBest model: {best_model_name} with accuracy: {best_score:.4f}")
        
        # Final evaluation
        y_pred_final = self.model.predict(X_test_vec)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred_final, target_names=['Fake', 'True']))
        
        # Setup SHAP explainer
        print("Setting up SHAP explainer...")
        try:
            if best_model_name in ['RandomForest', 'XGBoost', 'LightGBM']:
                self.explainer = shap.TreeExplainer(self.model, feature_perturbation='interventional')
            else:
                # For linear models, use a sample of training data
                self.explainer = shap.LinearExplainer(self.model, X_train_vec[:1000])
            print("SHAP explainer created successfully")
        except Exception as e:
            print(f"Warning: Could not create SHAP explainer ({e}). Explanations may be limited.")
            self.explainer = None
        
        return X_test_vec, y_test, y_pred_final
    
    def predict_with_explanation(self, text):
        """Predict if news is fake and provide SHAP explanation"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model not trained yet!")
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        text_vec = self.vectorizer.transform([processed_text])
        
        # Make prediction
        prediction = self.model.predict(text_vec)[0]
        probability = self.model.predict_proba(text_vec)[0]
        
        # Get SHAP values
        try:
            # Convert sparse vector to dense if needed (TreeExplainer often expects dense)
            input_for_shap = text_vec
            try:
                # If model is tree-based or explainer is TreeExplainer, prefer dense
                if hasattr(self.model, 'feature_importances_') and hasattr(text_vec, 'toarray'):
                    input_for_shap = text_vec.toarray()
            except Exception:
                pass

            shap_values = None
            if self.explainer is not None:
                shap_values = self.explainer.shap_values(input_for_shap)

            # For some versions, shap_values can be a list per class; pick positive/TRUE class (index 1)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]

            feature_names = self.vectorizer.get_feature_names_out()

            # If shap_values has shape (n_samples, n_features), take first sample
            if hasattr(shap_values, 'shape') and len(shap_values.shape) > 1:
                shap_values = shap_values[0]

            # If the predicted class is Fake (0), flip sign so that
            # contributions supporting Fake are negative (red) and True are positive (green)
            if prediction == 0:
                shap_values = -shap_values

            feature_importance = list(zip(feature_names, shap_values))
            # Select strongest contributors for the predicted class (now always positive after flip handling)
            feature_importance.sort(key=lambda x: x[1], reverse=True)
            top_features = feature_importance[:10]

        except Exception as e:
            print(f"SHAP explanation error: {e}")
            # Fallback 1: linear model coefficients contribution for present features
            try:
                feature_names = self.vectorizer.get_feature_names_out()
                dense_vec = text_vec.toarray().ravel() if hasattr(text_vec, 'toarray') else np.asarray(text_vec).ravel()

                if hasattr(self.model, 'coef_'):
                    coefs = self.model.coef_[0]
                    contributions = coefs * dense_vec
                    # Flip sign for Fake predictions to keep red/green semantics consistent
                    if prediction == 0:
                        contributions = -contributions
                    feature_importance = list(zip(feature_names, contributions))
                    feature_importance.sort(key=lambda x: x[1], reverse=True)
                    top_features = feature_importance[:10]
                elif hasattr(self.model, 'feature_importances_'):
                    importances = self.model.feature_importances_
                    contributions = importances * dense_vec
                    if prediction == 0:
                        contributions = -contributions
                    feature_importance = list(zip(feature_names, contributions))
                    feature_importance = [fi for fi in feature_importance if fi[1] != 0]
                    feature_importance.sort(key=lambda x: x[1], reverse=True)
                    top_features = feature_importance[:10]
                else:
                    top_features = []
            except Exception as e2:
                print(f"Fallback feature importance error: {e2}")
                top_features = []
        
        result = {
            'prediction': 'Fake' if prediction == 0 else 'True',
            'confidence': max(probability),
            'probabilities': {
                'fake': probability[0],
                'true': probability[1]
            },
            'explanation': top_features
        }
        
        return result
    
    def save_model(self, filepath='models/fake_news_model.pkl'):
        """Save the trained model and vectorizer"""
        import os
        os.makedirs('models', exist_ok=True)
        
        # Save model and vectorizer (explainer can be recreated if needed)
        model_data = {
            'model': self.model,
            'vectorizer': self.vectorizer
        }
        # Only save explainer if it exists and can be pickled
        try:
            if self.explainer is not None:
                # Test if explainer can be pickled
                import pickle
                pickle.dumps(self.explainer)
                model_data['explainer'] = self.explainer
        except Exception as e:
            print(f"Warning: Could not save SHAP explainer ({e}). Model will be saved without explainer.")
            print("Explainer will be recreated when needed.")
        
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='models/fake_news_model.pkl'):
        """Load a trained model and vectorizer"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.vectorizer = model_data['vectorizer']
            # Try to load explainer, but don't fail if it's incompatible
            self.explainer = None
            try:
                if 'explainer' in model_data and model_data['explainer'] is not None:
                    self.explainer = model_data['explainer']
                    print("SHAP explainer loaded successfully")
            except Exception as e:
                print(f"Warning: Could not load SHAP explainer ({e}). Will recreate if needed.")
                self.explainer = None
            
            # Recreate explainer if it wasn't loaded
            if self.explainer is None:
                print("Recreating SHAP explainer...")
                try:
                    # Get a sample from training data if available, otherwise create a dummy
                    # For tree-based models
                    if hasattr(self.model, 'feature_importances_'):
                        self.explainer = shap.TreeExplainer(self.model, feature_perturbation='interventional')
                    else:
                        # For linear models, we'll create explainer on demand
                        print("Linear model detected. SHAP explainer will be created when needed.")
                except Exception as e:
                    print(f"Warning: Could not create SHAP explainer ({e}). Explanations may be limited.")
                    self.explainer = None
            
            print(f"Model loaded from {filepath}")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("This may be due to version incompatibility. The model will be retrained.")
            raise

def main():
    # Initialize detector
    detector = FakeNewsDetector()
    detector.download_nltk_data()
    
    # Load and prepare data
    data = detector.load_and_combine_data()
    processed_data = detector.prepare_data(data, sample_size=15000)  # Adjust sample size as needed
    
    # Train model
    X_test, y_test, y_pred = detector.train_model(processed_data)
    
    # Save model
    detector.save_model()
    
    # Test with sample text
    sample_text = """
    Breaking: Scientists have discovered that drinking water can be harmful to your health. 
    A new study shows that 100% of people who drink water eventually die.
    """
    
    result = detector.predict_with_explanation(sample_text)
    print("\nSample Prediction:")
    print(f"Text: {sample_text}")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print("\nTop contributing features:")
    for feature, importance in result['explanation'][:5]:
        print(f"  {feature}: {importance:.4f}")

if __name__ == "__main__":
    main()
