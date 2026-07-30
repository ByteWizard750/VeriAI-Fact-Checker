from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
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
    return True

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
                title='Feature Impact on AI Model (Red = Promotional Risk | Green = Real News Style)',
                xaxis_title='◄ Pushes Toward Fake / Risk  |  Pushes Toward Real News ►',
                yaxis_title='Feature Terms',
                height=380,
                margin=dict(l=140, r=40, t=50, b=50)
            )
            
            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        else:
            chart_json = None
        
        # Run live web fact check
        try:
            from fact_checker import verify_claim_live
            live_check = verify_claim_live(text)
        except Exception as fc_err:
            print(f"Fact check error: {fc_err}")
            live_check = {
                'status': 'Check Failed',
                'verdict_color': 'secondary',
                'summary': 'Could not query live web search at this time.',
                'sources': []
            }
            
        # Compute Unified Final Verdict (combining AI Semantic Cross-Verification + Style Analysis)
        if live_check.get('is_verified', False):
            final_prediction = 'True'
            verdict_reason = f"Verified as Genuine Real News confirmed by live news reports with {live_check.get('alignment_score', 95.0)}% semantic alignment."
            display_confidence = 95.0
        elif live_check['status'] in ['Unverified Claim / False Rumor', 'Unverified Rumor / Misinformation', 'Fact-Check Article Found']:
            final_prediction = 'Fake'
            verdict_reason = live_check['summary']
            display_confidence = 90.0
        else:
            final_prediction = result['prediction']
            verdict_reason = f"Classified as {result['prediction']} based on AI linguistic style and vocabulary analysis."
            display_confidence = round(result['confidence'] * 100, 2)
        
        return jsonify({
            'prediction': final_prediction,
            'verdict_reason': verdict_reason,
            'style_prediction': result['prediction'],
            'confidence': display_confidence,
            'probabilities': {
                'fake': 90.0 if final_prediction == 'Fake' else 10.0,
                'true': 10.0 if final_prediction == 'Fake' else 90.0
            },
            'explanation': result['explanation'][:10],
            'chart': chart_json,
            'live_fact_check': live_check
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
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print("Failed to initialize detector. Please train the model first.")

