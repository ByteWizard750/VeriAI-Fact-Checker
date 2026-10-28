"""
Live API Verification Test Script for VeriAI Fact Checker
----------------------------------------------------------
Sends POST requests to http://127.0.0.1:5001/predict to verify live claims
and validate structured verification responses.
"""

import json
import time
import requests

API_URL = "http://127.0.0.1:5001/predict"

TEST_CLAIMS = [
    {
        "claim": "Elon Musk acquired Twitter for approximately $44 billion in 2022",
        "description": "Company Acquisition (Historically True)"
    },
    {
        "claim": "Satya Nadella is the current CEO of Microsoft",
        "description": "Person Current Role (True)"
    },
    {
        "claim": "Serena Williams announced retirement from professional tennis",
        "description": "Person Event (True)"
    },
    {
        "claim": "Scientists confirm Earth is flat",
        "description": "Scientific Misinformation (False)"
    },
    {
        "claim": "Aliens landed in a backyard in Ohio yesterday",
        "description": "Unverifiable Claim (Insufficient Evidence)"
    }
]

def test_live_api():
    print("=========================================================")
    print("       VeriAI Live API Endpoint Verification            ")
    print("=========================================================\n")

    # 1. Test Health Endpoint
    try:
        health_resp = requests.get("http://127.0.0.1:5001/health", timeout=5)
        print(f"Health Check: {health_resp.json()}\n")
    except Exception as e:
        print(f"Warning: Health check failed: {e}\n")

    # 2. Test Live Claims
    for idx, item in enumerate(TEST_CLAIMS, 1):
        claim = item["claim"]
        desc = item["description"]

        print(f"--- Test #{idx} [{desc}] ---")
        print(f"Claim: '{claim}'")

        start = time.time()
        try:
            resp = requests.post(
                API_URL,
                json={"text": claim},
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            elapsed = round(time.time() - start, 2)
            
            if resp.status_code == 200:
                data = resp.json()
                fc = data.get("live_fact_check", {})

                print(f"HTTP Status     : {resp.status_code}")
                print(f"Prediction      : {data.get('prediction')}")
                print(f"Verdict         : {data.get('verdict')}")
                print(f"Verdict State   : {data.get('verdict_state')}")
                print(f"Confidence      : {data.get('confidence')}%")
                print(f"Engine Used     : {fc.get('verification_engine', 'N/A')}")
                print(f"Search Queries  : {fc.get('search_queries', [])}")
                print(f"Sources Count   : {len(fc.get('sources', []))}")
                print(f"Reasoning       : {data.get('verdict_reason', '')[:120]}...")
                print(f"Elapsed Time    : {elapsed}s")
                print("Status          : SUCCESS\n")
            else:
                print(f"HTTP Status     : {resp.status_code}")
                print(f"Error Response  : {resp.text}\n")

        except Exception as e:
            print(f"ERROR: {e}\n")

    print("=========================================================")
    print("Live API Testing Complete.")
    print("=========================================================")

if __name__ == "__main__":
    test_live_api()
