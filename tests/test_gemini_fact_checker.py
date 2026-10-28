"""
Generic Unseen Claim Fact Checker Test Suite
---------------------------------------------
Tests the agentic fact verification pipeline across 17 distinct unseen claim categories.
"""

import json
import time
import requests

SERVER_URL = "http://127.0.0.1:5001/predict"

TEST_CASES = [
    {
        "category": "COMPANY + ACQUISITION",
        "claim": "Elon Musk acquired Twitter for approximately $44 billion in 2022",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "PERSON + EVENT",
        "claim": "Serena Williams announced retirement from professional tennis",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "PERSON + CURRENT ROLE",
        "claim": "Satya Nadella is the current CEO of Microsoft",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "SPORTS + LATEST EVENT",
        "claim": "Lionel Messi scored a hat-trick in his latest match",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "CONTRADICTED", "UNVERIFIED"]
    },
    {
        "category": "COMPANY + PRODUCT",
        "claim": "Apple launched Apple Vision Pro headset",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "HISTORICAL EVENT",
        "claim": "Neil Armstrong walked on the Moon in July 1969",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "DATE CLAIM",
        "claim": "India gained independence on August 15, 1947",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "NUMERICAL CLAIM",
        "claim": "Mount Everest height is 8848 meters",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "LOCATION CLAIM",
        "claim": "The Eiffel Tower is located in Paris",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "SCIENTIFIC CLAIM / CLEARLY FALSE",
        "claim": "Scientists confirm Earth is flat",
        "expected_verdicts": ["CONTRADICTED", "CONTRADICTED / FAKE RUMOR"]
    },
    {
        "category": "POLITICAL CLAIM",
        "claim": "Emmanuel Macron is the current President of France",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "UNVERIFIED"]
    },
    {
        "category": "NEGATED CLAIM",
        "claim": "Tesla did not acquire Ford Motor Company",
        "expected_verdicts": ["UNVERIFIED", "CONTRADICTED", "VERIFIED"]
    },
    {
        "category": "COMPOUND CLAIM",
        "claim": "Google acquired YouTube in 2006 for $1.65 billion",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "PARTIALLY TRUE CLAIM",
        "claim": "Amazon acquired Whole Foods Market",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "PARTIALLY_SUPPORTED", "UNVERIFIED"]
    },
    {
        "category": "CLEARLY TRUE CLAIM",
        "claim": "Microsoft acquired LinkedIn for $26.2 billion in 2016",
        "expected_verdicts": ["VERIFIED", "SUPPORTED", "VERIFIED / STRONGLY SUPPORTED"]
    },
    {
        "category": "CONFLICTING EVIDENCE CLAIM",
        "claim": "AB de Villiers returns to international cricket",
        "expected_verdicts": ["CONFLICTING", "UNVERIFIED", "CONTRADICTED"]
    },
    {
        "category": "UNVERIFIABLE / INSUFFICIENT EVIDENCE",
        "claim": "Aliens landed in a backyard in Ohio yesterday",
        "expected_verdicts": ["UNVERIFIED", "UNVERIFIED / INSUFFICIENT EVIDENCE"]
    }
]

def run_tests():
    print("=========================================================")
    print("   VeriAI Gemini Fact Verification Suite                ")
    print("=========================================================\n")

    results = []
    passed_count = 0

    for idx, tc in enumerate(TEST_CASES, 1):
        claim = tc["claim"]
        category = tc["category"]
        expected = tc["expected_verdicts"]

        print(f"--- Test #{idx} [{category}]: '{claim}' ---")
        start_time = time.time()
        try:
            resp = requests.post(SERVER_URL, json={"text": claim}, timeout=60)
            elapsed = round(time.time() - start_time, 2)
            data = resp.json()

            fc = data.get("live_fact_check", {})
            verdict = fc.get("verdict", data.get("verdict", "UNVERIFIED"))
            verdict_state = fc.get("verdict_state", data.get("verdict_state", "UNVERIFIED"))
            confidence = data.get("confidence", fc.get("confidence", 0.0))
            queries = fc.get("search_queries", [fc.get("query_used", "")])
            sources = fc.get("sources", [])
            engine = fc.get("verification_engine", "Unknown Engine")
            reasoning = fc.get("reasoning_summary", fc.get("claim_assessment", data.get("verdict_reason", "")))

            # Evaluate Pass/Fail
            is_pass = any(exp.lower() in verdict.lower() or exp.lower() in verdict_state.lower() for exp in expected)
            if is_pass:
                passed_count += 1
                status_str = "PASSED"
            else:
                status_str = "FAILED"

            print(f"Engine          : {engine}")
            print(f"Queries Used    : {queries}")
            print(f"Sources Count   : {len(sources)}")
            print(f"Verdict         : {verdict}")
            print(f"Confidence      : {confidence}%")
            print(f"Reasoning       : {reasoning[:120]}...")
            print(f"Elapsed Time    : {elapsed}s")
            print(f"Status          : {status_str}\n")

            results.append({
                "test_id": idx,
                "category": category,
                "claim": claim,
                "verdict": verdict,
                "verdict_state": verdict_state,
                "confidence": confidence,
                "latency_sec": elapsed,
                "sources_retrieved": len(sources),
                "search_queries": queries,
                "passed": is_pass
            })
        except Exception as e:
            print(f"ERROR executing test #{idx}: {e}\n")
            results.append({
                "test_id": idx,
                "category": category,
                "claim": claim,
                "error": str(e),
                "passed": False
            })

    total = len(TEST_CASES)
    print("=========================================================")
    print(f"SUITE SUMMARY: {passed_count} / {total} PASSED ({round((passed_count/total)*100, 1)}%)")
    print("=========================================================")

if __name__ == "__main__":
    run_tests()
