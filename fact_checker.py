"""
Fact Checker Wrapper Module
Delegates live claim verification to the Multi-Stage Verification Agent in verification_agent.py
"""

from verification_agent import verify_claim_agent, analyze_claim, generate_queries

def verify_claim_live(text):
    """
    Wrapper for live claim verification using the Evidence Verification Agent.
    Returns structured result dictionary compatible with app.py and frontend.
    """
    agent_result = verify_claim_agent(text)
    
    # Map agent verdict to legacy fields if needed for UI compatibility
    return {
        'status': agent_result['verdict'],
        'verdict_state': agent_result['verdict_state'],
        'verdict_color': agent_result['verdict_color'],
        'summary': agent_result['summary'],
        'query_used': agent_result['query_used'],
        'is_verified': agent_result['is_verified'],
        'confidence': agent_result['confidence'],
        'claim_components': agent_result['claim_components'],
        'propositions': agent_result['propositions'],
        'supporting_evidence': agent_result['supporting_evidence'],
        'contradicting_evidence': agent_result['contradicting_evidence'],
        'source_corroboration': agent_result['source_corroboration'],
        'consistency_checks': agent_result['consistency_checks'],
        'sources': agent_result['sources']
    }
