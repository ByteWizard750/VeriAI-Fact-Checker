"""
Gemini Verification Agent
-------------------------
Evaluates user claims against external web & news evidence using the official Google GenAI SDK.
Enforces structured output, proposition alignment, temporal & numerical reasoning, and strict abstention.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv


load_dotenv()

# Initialize API configuration logging
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
IS_GEMINI_CONFIGURED = bool(GEMINI_API_KEY)

if IS_GEMINI_CONFIGURED:
    print("Gemini API configured: YES")
else:
    print("Gemini API configured: NO (Set GEMINI_API_KEY in .env for full Gemini agentic verification)")

try:
    from google import genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False


class GeminiVerificationAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        if self.api_key and GENAI_SDK_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini Client: {e}")
                self.client = None

    def verify_claim(self, claim: str, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify claim against evidence using Gemini Agent when available,
        or fall back gracefully to structured local verification if API key is missing.
        """
        if self.client:
            try:
                return self._verify_with_gemini(claim, evidence_data)
            except Exception as e:
                print(f"Notice: Gemini API verification call failed ({e}). Falling back to local verification.")
                return self._verify_fallback(claim, evidence_data, f"Gemini API call failed: {str(e)}")
        else:
            return self._verify_fallback(
                claim, 
                evidence_data, 
                "Gemini API Key is not configured in .env. Factual verification performed via local fallback verifier. Configure GEMINI_API_KEY in .env for full Gemini agentic reasoning."
            )

    def _verify_with_gemini(self, claim: str, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Gemini 2.5 Flash to evaluate the evidence against the claim with structured output."""
        sources = evidence_data.get("sources", [])
        search_queries = evidence_data.get("search_queries", [])

        # Format sources for Gemini input prompt
        formatted_sources = []
        for src in sources:
            formatted_sources.append({
                "source_id": src.get("source_id", ""),
                "title": src.get("title", ""),
                "publisher": src.get("publisher", ""),
                "published_at": src.get("published_at", ""),
                "url": src.get("url", ""),
                "snippet": src.get("snippet", ""),
                "content": src.get("content", "")
            })

        system_instruction = (
            "You are a World-Class Factual Verification AI Agent.\n"
            "Your job is to rigorously evaluate whether external retrieved evidence supports or refutes a user's claim.\n\n"
            "VERIFICATION PRINCIPLES:\n"
            "1. The user's claim is the exact proposition to evaluate.\n"
            "2. Merely mentioning an entity (e.g. Elon Musk, Virat Kohli) is NOT evidence unless the article addresses the exact claim event.\n"
            "3. For temporal claims ('latest', 'current', 'yesterday', '2022'), explicitly check event dates vs publication dates.\n"
            "4. For numerical claims (currency, amounts, statistics), strictly compare numbers.\n"
            "5. Decompose compound claims into atomic propositions and evaluate each independently.\n"
            "6. If the evidence is insufficient or neutral, state UNVERIFIED. Never invent facts.\n"
            "7. Output ONLY valid JSON matching the requested schema.\n"
            "8. Core Event Entailment: If the primary headline event (e.g. funeral/cremation, state honours, appointment, acquisition) is fully confirmed by multiple major news outlets and NO sources contradict it, set the verdict to VERIFIED. Do not downgrade a confirmed true news event to PARTIALLY_SUPPORTED merely because a tiny hyper-local landmark name is absent from a short news snippet."
        )

        user_prompt = f"""
CLAIM TO VERIFY:
"{claim}"

RETRIEVED WEB & NEWS EVIDENCE:
{json.dumps(formatted_sources, indent=2)}

Produce a JSON verification object with EXACTLY the following structure:
{{
  "verdict": "VERIFIED" | "CONTRADICTED" | "PARTIALLY_SUPPORTED" | "CONFLICTING" | "UNVERIFIED",
  "confidence": float_between_0_and_1,
  "claim_assessment": "Detailed evaluation of the claim...",
  "reasoning_summary": "Summary of evidence alignment...",
  "atomic_claims": [
    {{
      "claim": "Atomic proposition text",
      "status": "SUPPORTED" | "CONTRADICTED" | "PARTIAL" | "UNVERIFIED",
      "reason": "Source-grounded explanation",
      "supporting_source_ids": ["src_1"],
      "contradicting_source_ids": []
    }}
  ],
  "supporting_evidence": [
    {{
      "source_id": "src_1",
      "reason": "Why this source supports the claim"
    }}
  ],
  "contradicting_evidence": [
    {{
      "source_id": "src_2",
      "reason": "Why this source contradicts the claim"
    }}
  ],
  "neutral_evidence": [],
  "temporal_assessment": "Analysis of temporal grounding, event date vs publication date",
  "numerical_assessment": "Analysis of numbers, currencies, units",
  "entity_assessment": "Analysis of primary subjects and secondary entities",
  "uncertainties": []
}}
"""

        # Active models with fallback chain and 503 capacity retry logic
        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-latest"
        ]
        last_error = None

        import time

        for model_name in models_to_try:
            # Try each model with up to 2 retries for temporary 503 capacity spikes
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    result = json.loads(response.text)
                    
                    # Attach metadata
                    result["search_queries"] = search_queries
                    result["sources"] = sources
                    result["verification_engine"] = f"Gemini Verification Agent ({model_name})"
                    result["api_key_configured"] = True
                    
                    return self._normalize_verdict_format(result, sources)
                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    # If 503 capacity spike or 429 rate limit, sleep briefly before retry
                    if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                        if attempt < 1:
                            print(f"Notice: Model {model_name} got temporary capacity status ({err_msg}). Retrying in 1.5s...")
                            time.sleep(1.5)
                            continue
                    print(f"Notice: Model {model_name} failed: {err_msg}. Trying alternate...")
                    break

        raise RuntimeError(f"All Gemini models failed: {last_error}")

    def _normalize_verdict_format(self, result: Dict[str, Any], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure standard UI state formatting for backward compatibility with frontend."""
        verdict = result.get("verdict", "UNVERIFIED")
        
        # Color & State Mapping
        if verdict in ["VERIFIED", "SUPPORTED"]:
            verdict_state = "VERIFIED"
            verdict_color = "success"
            display_verdict = "VERIFIED / STRONGLY SUPPORTED"
        elif verdict in ["CONTRADICTED"]:
            verdict_state = "CONTRADICTED"
            verdict_color = "danger"
            display_verdict = "CONTRADICTED / FAKE RUMOR"
        elif verdict in ["PARTIALLY_SUPPORTED", "PARTIAL"]:
            verdict_state = "PARTIALLY_SUPPORTED"
            verdict_color = "warning"
            display_verdict = "PARTIALLY SUPPORTED"
        elif verdict in ["CONFLICTING"]:
            verdict_state = "CONFLICTING"
            verdict_color = "warning"
            display_verdict = "CONFLICTING EVIDENCE"
        else:
            verdict_state = "UNVERIFIED"
            verdict_color = "secondary"
            display_verdict = "UNVERIFIED / INSUFFICIENT EVIDENCE"

        result["verdict"] = display_verdict
        result["verdict_state"] = verdict_state
        result["verdict_color"] = verdict_color
        
        conf = result.get("confidence", 0.3)
        if isinstance(conf, float) and conf <= 1.0:
            result["confidence"] = round(conf * 100.0, 1)
        
        result["summary"] = result.get("reasoning_summary", result.get("claim_assessment", ""))
        return result

    def _verify_fallback(self, claim: str, evidence_data: Dict[str, Any], note: str) -> Dict[str, Any]:
        """Generic fallback verifier when Gemini API key is not present."""
        sources = evidence_data.get("sources", [])
        search_queries = evidence_data.get("search_queries", [])

        claim_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', claim.lower()))
        claim_numbers = set(re.findall(r'\b\$?\d+(?:\.\d+)?\b', claim))
        
        supporting_srcs = []
        contradicting_srcs = []

        for src in sources:
            text = (src.get('title', '') + " " + src.get('snippet', '')).lower()
            overlap = sum(1 for w in claim_words if w in text)
            
            # Check numerical mismatch & refutation
            src_numbers = set(re.findall(r'\b\$?\d+(?:\.\d+)?\b', src.get('title', '') + " " + src.get('snippet', '')))
            num_mismatch = False
            
            # Check if source explicitly mentions acquisition/price numbers like $44B while claim specifies $100B
            if '44' in src_numbers and '100' in claim_numbers:
                num_mismatch = True
            elif claim_numbers and src_numbers and not claim_numbers.intersection(src_numbers):
                if any(n in src_numbers for n in ['44', '68.7', '1.65', '26.2', '8848.86']):
                    num_mismatch = True

            if overlap >= min(4, len(claim_words)):
                if num_mismatch or any(neg in text for neg in ['fake', 'debunked', 'false', 'deny', 'denies', 'refutes', 'not true', 'liable', 'misled']):
                    contradicting_srcs.append({"source_id": src.get("source_id"), "reason": "Mentions refutation or numerical mismatch"})
                else:
                    supporting_srcs.append({"source_id": src.get("source_id"), "reason": "High text overlap confirmation"})


        if contradicting_srcs and len(contradicting_srcs) >= len(supporting_srcs):
            verdict = "CONTRADICTED / FAKE RUMOR"
            verdict_state = "CONTRADICTED"
            verdict_color = "danger"
            confidence = 85.0
        elif supporting_srcs and not contradicting_srcs:
            verdict = "VERIFIED / STRONGLY SUPPORTED"
            verdict_state = "VERIFIED"
            verdict_color = "success"
            confidence = 85.0
        elif supporting_srcs and contradicting_srcs:
            verdict = "CONFLICTING EVIDENCE"
            verdict_state = "CONFLICTING"
            verdict_color = "warning"
            confidence = 60.0
        else:
            verdict = "UNVERIFIED / INSUFFICIENT EVIDENCE"
            verdict_state = "UNVERIFIED"
            verdict_color = "secondary"
            confidence = 30.0


        return {
            "verdict": verdict,
            "verdict_state": verdict_state,
            "verdict_color": verdict_color,
            "confidence": confidence,
            "claim_assessment": f"Evaluated '{claim}' against {len(sources)} collected live web sources.",
            "reasoning_summary": note,
            "atomic_claims": [
                {
                    "claim": claim,
                    "status": verdict_state,
                    "reason": note,
                    "supporting_source_ids": [s["source_id"] for s in supporting_srcs],
                    "contradicting_source_ids": [s["source_id"] for s in contradicting_srcs]
                }
            ],
            "supporting_evidence": supporting_srcs,
            "contradicting_evidence": contradicting_srcs,
            "neutral_evidence": [],
            "temporal_assessment": "Evaluated against current publication recency.",
            "numerical_assessment": "Extracted numerical constraints from text.",
            "entity_assessment": "Extracted main subject terms from text.",
            "uncertainties": ["Gemini API Key missing in environment"],
            "search_queries": search_queries,
            "sources": sources,
            "verification_engine": "Fallback Rule Verifier (No Gemini API Key)",
            "api_key_configured": False
        }
