import os
import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

import json
import time
from verification_agent import verify_claim_agent

def run_tests():
    test_claims = [
        "Ajinkya Rahane has taken retirement from all forms of cricket today",
        "Airtel to give free gemini pro for 1 year",
        "Adarsha kutumbam to be released on oct 2",
        "Nushrratt Bharuccha suffered spinal fracture following accident during work trip in Bali",
        "Amazon acquired Flipkart for $200 billion in 2026",
        "Scientists confirm moon is made of green cheese"
    ]

    print("\n=======================================================")
    print("      VeriAI Verification Agent Generic Test Suite     ")
    print("=======================================================\n")

    for i, claim in enumerate(test_claims, 1):
        print(f"--- Test #{i}: '{claim}' ---")
        start = time.time()
        result = verify_claim_agent(claim)
        elapsed = time.time() - start

        print(f"Verdict         : {result['verdict']}")
        print(f"State           : {result['verdict_state']}")
        print(f"Confidence      : {result['confidence']}%")
        print(f"Entities Found  : {result['claim_components']['entities']}")
        print(f"Dates Found     : {result['claim_components']['dates']}")
        print(f"Numbers Found   : {result['claim_components']['numbers']}")
        print(f"Consistency     : {result['consistency_checks']}")
        print(f"Corroboration   : {result['source_corroboration']}")
        print(f"Summary         : {result['summary']}")
        print(f"Execution Time  : {elapsed:.2f}s\n")

if __name__ == '__main__':
    run_tests()
