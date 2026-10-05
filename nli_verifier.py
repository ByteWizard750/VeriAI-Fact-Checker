"""
Neural Transformer NLI Verifier Module
======================================
Loads a pretrained NLI Cross-Encoder / Sequence Classification model
(e.g., cross-encoder/nli-deberta-v3-small)
and predicts semantic entailment, contradiction, and neutral probabilities.
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class SemanticNLIVerifier:
    _instance = None
    
    def __init__(self, model_name="cross-encoder/nli-deberta-v3-small"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
        try:
            torch.set_num_threads(1)
        except Exception:
            pass
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SemanticNLIVerifier()
        return cls._instance

    def load_model(self):
        if self.is_loaded:
            return True
        try:
            print(f"Loading pretrained Neural NLI model '{self.model_name}' on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            print("Neural NLI model loaded successfully!")
            return True
        except Exception as e:
            print(f"Warning: Failed to load Neural NLI model '{self.model_name}': {e}")
            self.is_loaded = False
            return False

    def predict_pair(self, premise, hypothesis):
        """
        Evaluate (premise, hypothesis) pair.
        Returns dict: {'entailment': float, 'contradiction': float, 'neutral': float}
        """
        if not self.is_loaded:
            success = self.load_model()
            if not success:
                return None
                
        try:
            inputs = self.tokenizer(
                premise[:1000], hypothesis[:300],
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs = torch.softmax(logits, dim=1)[0].cpu().tolist()
                
            id2label = getattr(self.model.config, 'id2label', {0: 'contradiction', 1: 'entailment', 2: 'neutral'})
            
            result = {}
            for idx, prob in enumerate(probs):
                lbl_raw = str(id2label.get(idx, idx)).lower()
                if 'entail' in lbl_raw:
                    result['entailment'] = float(prob)
                elif 'contra' in lbl_raw:
                    result['contradiction'] = float(prob)
                else:
                    result['neutral'] = float(prob)
                    
            for k in ['entailment', 'contradiction', 'neutral']:
                if k not in result:
                    result[k] = 0.0
                    
            return result
        except Exception as ex:
            print(f"NLI prediction error: {ex}")
            return None

    def batch_predict(self, pairs):
        """
        Batch evaluation of multiple (premise, hypothesis) pairs.
        """
        if not pairs:
            return []
        if not self.is_loaded:
            success = self.load_model()
            if not success:
                return [None] * len(pairs)
                
        results = []
        for i in range(0, len(pairs), 8):
            batch_pairs = pairs[i:i+8]
            premises = [p[0][:1000] for p in batch_pairs]
            hypotheses = [p[1][:300] for p in batch_pairs]
            
            try:
                inputs = self.tokenizer(
                    premises, hypotheses,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    logits = self.model(**inputs).logits
                    probs = torch.softmax(logits, dim=1).cpu().tolist()
                    
                id2label = getattr(self.model.config, 'id2label', {0: 'contradiction', 1: 'entailment', 2: 'neutral'})
                
                for prob_set in probs:
                    res = {}
                    for idx, prob in enumerate(prob_set):
                        lbl_raw = str(id2label.get(idx, idx)).lower()
                        if 'entail' in lbl_raw:
                            res['entailment'] = float(prob)
                        elif 'contra' in lbl_raw:
                            res['contradiction'] = float(prob)
                        else:
                            res['neutral'] = float(prob)
                    for k in ['entailment', 'contradiction', 'neutral']:
                        if k not in res:
                            res[k] = 0.0
                    results.append(res)
            except Exception as ex:
                print(f"Batch NLI error: {ex}")
                for _ in batch_pairs:
                    results.append(None)
                    
        return results
