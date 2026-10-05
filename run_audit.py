import json
from verification_agent import verify_claim_agent

claims = [
    "Apple launched iPhone 16 Pro in September 2024 with A18 Pro chip",
    "BCCI appointed Rohit Sharma as India test captain in 2022",
    "Tesla launched a flying electric car for $10,000 in Tokyo yesterday",
    "Mukesh Ambani bought Manchester United for $50 billion in August 2026",
    "NASA landed humans on Mars in March 2026",
    "Virat Kohli scored a century against Pakistan in Asia Cup",
    "Google acquired YouTube for $1.65 billion",
    "Perplexity AI released Perplexity Pro subscription service",
    "Adarsha Kutumbam movie released on October 2",
    "Scientists confirm the Earth is flat"
]

print("\n=======================================================")
print("         VERIAI VERIFICATION ENGINE RIGOROUS AUDIT     ")
print("=======================================================\n")

for i, claim in enumerate(claims, 1):
    res = verify_claim_agent(claim)
    
    nli_counts = {}
    for s in res['sources']:
        nv = s['nli']['nli_verdict']
        nli_counts[nv] = nli_counts.get(nv, 0) + 1
        
    print(f"--- TEST CLAIM #{i} ---")
    print(f"1. CLAIM                  : {res['claim']}")
    print(f"2. RETRIEVED EVIDENCE     : {res['summary']} (Evaluated {res['source_corroboration']['evaluated_sources_count']} sources)")
    print(f"3. NLI RESULT             : {nli_counts}")
    print(f"4. ENTITY RESULT          : {res['consistency_checks']['entity_consistency']} | Entities: {res['claim_components']['entities']}")
    print(f"5. EVENT RESULT           : Classification: '{res['claim_components']['event_type']}'")
    print(f"6. TEMPORAL RESULT        : {res['consistency_checks']['temporal_consistency']} | Dates: {res['claim_components']['dates']}")
    print(f"7. LOCATION RESULT        : Locations: {res['claim_components']['locations']}")
    print(f"8. NUMERICAL RESULT       : {res['consistency_checks']['numerical_consistency']} | Numbers: {res['claim_components']['numbers']}")
    print(f"9. SOURCE CORROBORATION   : {res['source_corroboration']}")
    print(f"10. FINAL VERDICT         : {res['verdict']} (State: {res['verdict_state']})")
    print(f"11. CONFIDENCE            : {res['confidence']}%\n")
