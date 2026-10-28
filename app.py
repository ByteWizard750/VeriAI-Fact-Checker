import os
from dotenv import load_dotenv
load_dotenv()

os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
os.environ["JOBLIB_MULTIPROCESSING"] = "0"

gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
if gemini_key:
    print("Gemini API configured: YES")
else:
    print("Gemini API configured: NO (Set GEMINI_API_KEY in .env for full Gemini agentic verification)")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from fake_news_detector import FakeNewsDetector

import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)
CORS(app)

# Global detector instance
detector = None

def initialize_detector():
    """Initialize the fake news detector"""
    global detector
    detector = FakeNewsDetector()
    # Ensure NLTK resources (punkt, stopwords) are available
    try:
        detector.download_nltk_data()
    except Exception as e:
        print(f"Warning: Failed to download NLTK data: {e}")
    
    # Check if model exists, if not train it
    model_path = 'models/fake_news_model.pkl'
    if os.path.exists(model_path):
        print("Loading existing model...")
        try:
            detector.load_model(model_path)
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("Retraining model with current dependencies...")
            try:
                # Load and prepare data
                data = detector.load_and_combine_data()
                processed_data = detector.prepare_data(data, sample_size=15000)
                # Train model
                detector.train_model(processed_data)
                # Save model
                detector.save_model(model_path)
                print("Model retrained and saved successfully!")
            except Exception as train_error:
                print(f"Failed to retrain model: {train_error}")
                return False
    else:
        print("No existing model found. Training new model...")
        try:
            # Load and prepare data
            data = detector.load_and_combine_data()
            processed_data = detector.prepare_data(data, sample_size=15000)
            # Train model
            detector.train_model(processed_data)
            # Save model
            detector.save_model(model_path)
            print("Model trained and saved successfully!")
        except Exception as train_error:
            print(f"Failed to train model: {train_error}")
            return False
    # Pre-warm Neural Transformer NLI model
    try:
        from nli_verifier import SemanticNLIVerifier
        SemanticNLIVerifier.get_instance().load_model()
    except Exception as e:
        print(f"Warning: Failed to pre-warm Neural NLI model: {e}")
        
    return True

# Initialize detector on module import for WSGI servers
initialize_detector()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Predict if news is fake or true"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Please provide some text to analyze'}), 400
        
        if detector is None:
            return jsonify({'error': 'Model not loaded. Please train the model first.'}), 500
        
        # Get prediction with explanation
        result = detector.predict_with_explanation(text)
        
        # Create visualization data for SHAP values
        if result['explanation']:
            features = [item[0] for item in result['explanation'][:10]]
            values = [item[1] for item in result['explanation'][:10]]
            
            # Create bar chart for feature importance
            fig = go.Figure(data=[
                go.Bar(
                    x=values,
                    y=features,
                    orientation='h',
                    marker=dict(
                        color=['red' if v < 0 else 'green' for v in values],
                        opacity=0.7
                    )
                )
            ])
            
            fig.update_layout(
                title='Feature Contributions to Model Prediction',
                xaxis_title='◄ Pushes Toward Unverified Style  |  Pushes Toward Verified News Style ►',
                yaxis_title='Feature Terms',
                height=360,
                margin=dict(l=140, r=40, t=50, b=50)
            )
            
            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        else:
            chart_json = None
        
        # Run live web evidence verification agent
        try:
            from verification_agent import verify_claim_agent
            agent_result = verify_claim_agent(text)
        except Exception as fc_err:
            print(f"Verification Agent error: {fc_err}")
            agent_result = {
                'verdict': 'UNVERIFIED / INSUFFICIENT EVIDENCE',
                'verdict_state': 'UNVERIFIED',
                'verdict_color': 'secondary',
                'confidence': 25.0,
                'summary': 'Could not complete web evidence verification at this time.',
                'query_used': text[:50],
                'is_verified': False,
                'claim_components': {'entities': [], 'dates': [], 'numbers': [], 'locations': [], 'event_type': 'general_claim'},
                'propositions': [],
                'supporting_evidence': [],
                'contradicting_evidence': [],
                'source_corroboration': {'evaluated_sources_count': 0, 'independent_sources_count': 0, 'syndicated_copies_detected': 0},
                'consistency_checks': {'entity_consistency': 'MISMATCH', 'temporal_consistency': 'DATE_MISMATCH', 'numerical_consistency': 'NUMBER_MISMATCH'},
                'sources': []
            }
            
        # Map agent state to prediction string for legacy UI widgets
        v_state = agent_result.get('verdict_state', 'UNVERIFIED')
        if v_state in ['VERIFIED', 'SUPPORTED']:
            final_prediction = 'True'
        elif v_state in ['CONTRADICTED']:
            final_prediction = 'Fake'
        elif v_state in ['PARTIALLY_SUPPORTED']:
            final_prediction = 'Partially Supported'
        else:
            final_prediction = 'Unverified'

        display_confidence = agent_result.get('confidence', 30.0)
        verdict_reason = agent_result.get('summary', '')

        # Fake vs True probabilities strictly reflecting derived evidence confidence
        if final_prediction in ['True', 'Partially Supported']:
            true_prob = display_confidence
            fake_prob = round(100.0 - display_confidence, 1)
        elif final_prediction == 'Fake':
            fake_prob = display_confidence
            true_prob = round(100.0 - display_confidence, 1)
        else:
            fake_prob = 50.0
            true_prob = 50.0

        # Process SHAP explanations for rich interactive UI
        raw_explanation = result.get('explanation', [])
        shap_word_map = {}
        pos_terms = []
        neg_terms = []
        
        for item in raw_explanation:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                word = str(item[0]).strip().lower()
                val = float(item[1])
                shap_word_map[word] = round(val, 4)
                if val > 0:
                    pos_terms.append({'word': word, 'impact': round(val, 3)})
                elif val < 0:
                    neg_terms.append({'word': word, 'impact': round(val, 3)})

        pos_terms.sort(key=lambda x: x['impact'], reverse=True)
        neg_terms.sort(key=lambda x: x['impact'])

        # Calculate Linguistic Style Quality Index (0-100%)
        net_shap = sum(item[1] for item in raw_explanation if isinstance(item, (list, tuple)))
        linguistic_score = round(max(10.0, min(98.0, 60.0 + (net_shap * 25.0))), 1)

        return jsonify({
            'prediction': final_prediction,
            'verdict': agent_result.get('verdict'),
            'verdict_state': v_state,
            'verdict_color': agent_result.get('verdict_color', 'secondary'),
            'verdict_reason': verdict_reason,
            'style_prediction': result['prediction'],
            'confidence': display_confidence,
            'probabilities': {
                'fake': fake_prob,
                'true': true_prob
            },
            'explanation': raw_explanation[:10],
            'shap_analysis': {
                'word_scores': shap_word_map,
                'positive_terms': pos_terms[:6],
                'negative_terms': neg_terms[:6],
                'linguistic_score': linguistic_score
            },
            'chart': chart_json,
            'live_fact_check': agent_result
        })



        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': detector is not None
    })

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

if __name__ == '__main__':
    print("Initializing Fake News Detector...")
    if initialize_detector():
        port = int(os.environ.get('PORT', 5001))
        print(f"Starting Flask application on port {port}...")
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False, threaded=True)
    else:
        print("Failed to initialize detector. Please train the model first.")

