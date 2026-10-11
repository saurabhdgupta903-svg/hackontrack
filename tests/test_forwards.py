"""
Accuracy and Benchmark Test Suite for Sach?
Tests 10 real forwards across:
- False
- Verified
- Outdated
- Partly supported
- Cannot be confirmed
Prints a formatted accuracy and evaluation table.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

from backend.models.db import init_db
from backend.services.ingest import ingest_text
from backend.services.pipeline import run_pipeline_sync
from backend.schemas.fact_check import (
    VERDICT_VERIFIED,
    VERDICT_FALSE,
    VERDICT_OUTDATED,
    VERDICT_PARTLY_SUPPORTED,
    VERDICT_CANNOT_BE_CONFIRMED,
)

# 10 Real-world viral forwards circulated on WhatsApp in India
TEST_FORWARDS = [
    {
        "id": 1,
        "input": "From Monday, all ₹500 currency notes are invalid and banned by RBI. Forward to all groups immediately!",
        "expected_verdicts": [VERDICT_CANNOT_BE_CONFIRMED, VERDICT_FALSE],
        "category": "Currency / Banking Hoax",
        "notes": "PIB/RBI have repeatedly refuted claims that ₹500 notes are discontinued."
    },
    {
        "id": 2,
        "input": "Breaking: UNESCO has just declared the Indian National Anthem 'Jana Gana Mana' as the best national anthem in the world! Proud moment for all Indians.",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_CANNOT_BE_CONFIRMED],
        "category": "UNESCO Hoax",
        "notes": "Classic long-running WhatsApp myth repeatedly debunked by PIB and fact-checkers."
    },
    {
        "id": 3,
        "input": "Prime Minister Free Laptop Scheme 2026: Government of India is giving free laptops to all Class 10 and 12 students. Register at http://pm-laptop-free-yojana-apply.in before Sunday!",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_CANNOT_BE_CONFIRMED],
        "category": "Phishing / Government Scheme",
        "notes": "Scam website pretending to be PIB/Education Ministry scheme."
    },
    {
        "id": 4,
        "input": "India's Chandrayaan-3 successfully landed on the south polar region of the Moon on 23 August 2023, making India the fourth country to achieve a soft lunar landing.",
        "expected_verdicts": [VERDICT_VERIFIED],
        "category": "ISRO / Science Achievement",
        "notes": "Historically confirmed fact verified by ISRO and PIB."
    },
    {
        "id": 5,
        "input": "New WhatsApp guidelines: If your message gets three blue ticks, it means the government has seen it. If two blue ticks and one red tick, government is taking legal action against you.",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_CANNOT_BE_CONFIRMED],
        "category": "Privacy / WhatsApp Hoax",
        "notes": "Fake WhatsApp tick color rumor debunked officially by PIB Fact Check."
    },
    {
        "id": 6,
        "input": "The Reserve Bank of India has withdrawn ₹2,000 denomination banknotes from circulation, but they remain legal tender.",
        "expected_verdicts": [VERDICT_VERIFIED, VERDICT_PARTLY_SUPPORTED],
        "category": "RBI Currency Notice",
        "notes": "RBI circular dated May 19, 2023 withdrew ₹2000 notes while noting legal tender status."
    },
    {
        "id": 7,
        "input": "COVID-19 vaccination was mandated by the Supreme Court of India and no one can enter public places without showing a vaccine certificate.",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_OUTDATED, VERDICT_PARTLY_SUPPORTED],
        "category": "Health / Legal",
        "notes": "Supreme Court ruled in May 2022 that no individual can be forced to be vaccinated."
    },
    {
        "id": 8,
        "input": "WHO issued an alert that paracetamol P-500 contains the Machupo virus, causing fatal infection within hours. Do not consume!",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_CANNOT_BE_CONFIRMED],
        "category": "Medical / Health Panic",
        "notes": "Long-running health hoax debunked by WHO, Health Ministry, and fact checkers."
    },
    {
        "id": 9,
        "input": "A secret tunnel was discovered under our colony park yesterday night and aliens were spotted by the watchman.",
        "expected_verdicts": [VERDICT_CANNOT_BE_CONFIRMED],
        "category": "Unverifiable Local Rumor",
        "notes": "Zero authoritative records exist; must return 'Cannot be confirmed' without guessing."
    },
    {
        "id": 10,
        "input": "Old ₹1000 notes can still be exchanged at any post office counter under current RBI guidelines.",
        "expected_verdicts": [VERDICT_FALSE, VERDICT_OUTDATED],
        "category": "Banking / Demonetisation",
        "notes": "Demonetised in 2016; exchange windows closed years ago."
    }
]

async def run_benchmark():
    await init_db()
    print("=" * 80)
    print("SACH? FACT-CHECKING ENGINE ACCURACY BENCHMARK (10 REAL FORWARDS)")
    print("=" * 80)

    results = []
    correct_matches = 0

    for item in TEST_FORWARDS:
        f_id = item["id"]
        inp = item["input"]
        expected = item["expected_verdicts"]
        category = item["category"]

        print(f"\n[{f_id}/10] Testing: {inp[:60]}...")
        try:
            ingested = await ingest_text(inp)
            res = await run_pipeline_sync(ingested, target_language="en")
            actual_dominant = res.summary.dominant_verdict
            claim_verdicts = [c.verdict for c in res.claims]
            first_verdict = claim_verdicts[0] if claim_verdicts else actual_dominant

            # Check if actual verdict aligns with expected labels
            is_match = (first_verdict in expected) or (actual_dominant in expected)
            if is_match:
                correct_matches += 1
                status = "PASS"
            else:
                status = "REVIEW"

            results.append({
                "id": f_id,
                "category": category,
                "expected": "/".join(expected),
                "actual": actual_dominant,
                "status": status,
                "claims_count": len(res.claims),
                "summary": res.summary.summary_text
            })
            print(f"       -> Actual Verdict: {actual_dominant} | Status: {status}")
        except Exception as e:
            results.append({
                "id": f_id,
                "category": category,
                "expected": "/".join(expected),
                "actual": f"ERROR: {str(e)[:30]}",
                "status": "FAIL",
                "claims_count": 0,
                "summary": str(e)
            })
            print(f"       -> ERROR: {e}")

    # Print Formatted Evaluation Table
    print("\n" + "=" * 80)
    print(f"{'ID':<4} | {'Category':<24} | {'Expected Verdict':<20} | {'Actual Verdict':<18} | {'Status':<6}")
    print("-" * 80)
    for r in results:
        print(f"{r['id']:<4} | {r['category']:<24} | {r['expected']:<20} | {r['actual']:<18} | {r['status']:<6}")
    print("-" * 80)
    accuracy_pct = (correct_matches / len(TEST_FORWARDS)) * 100
    print(f"SUMMARY: {correct_matches}/{len(TEST_FORWARDS)} Passed ({accuracy_pct:.1f}% Benchmark Alignment)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
