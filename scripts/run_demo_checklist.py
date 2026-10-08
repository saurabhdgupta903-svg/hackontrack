"""
Live Demo Verification Script
Tests all 5 modalities mandated by Section 7 (Definition of Done):
1. A forwarded text claim (e.g. ₹500 note message)
2. A screenshot of a WhatsApp message in Hindi/English
3. A voice note
4. A multi-page PDF containing one false claim
5. A news URL

For each one, outputs:
- Extracted claims & original span
- Sources checked (allowlist domain verification)
- Verdict badge (one of the 5 exact labels)
- Plain-language explanation in user's language
- Outbound evidence links
"""

import asyncio
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from backend.models.db import init_db
from backend.services.ingest import (
    ingest_text,
    ingest_image,
    ingest_voice,
    ingest_pdf,
    ingest_url
)
from backend.services.pipeline import run_pipeline_sync

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo_samples"

async def test_case(title: str, ingest_func, target_lang: str = "en"):
    print("\n" + "=" * 80)
    print(f"DEMO CASE: {title}")
    print("=" * 80)
    try:
        ingest_res = await ingest_func()
        print(f"-> Ingest completed: Type={ingest_res.input_type}, Chars={len(ingest_res.raw_text)}")
        print(f"-> Raw snippet: {ingest_res.raw_text[:140]}...")

        print("-> Running fact-checking pipeline (Claim Extraction -> Retrieval -> Judging -> Explaining)...")
        result = await run_pipeline_sync(ingest_res, target_language=target_lang)

        print("\n--- RESULTS ---")
        print(f"Top Summary: {result.summary.summary_text}")
        print(f"Dominant Verdict: [{result.summary.dominant_verdict}]")
        print(f"Detected Language: {result.detected_language}")

        for i, c in enumerate(result.claims, 1):
            print(f"\n[Claim #{i}]")
            print(f"  • Original Quote : \"{c.original_span}\"")
            print(f"  • Extracted Claim: {c.claim_text}")
            print(f"  • Verdict Badge  : [{c.verdict}] (Confidence: {c.confidence:.2f})")
            print(f"  • What is Right  : {c.what_is_right}")
            print(f"  • What is False  : {c.what_is_wrong_or_missing}")
            print(f"  • Explanation    : {c.explanation}")
            print(f"  • Citations ({len(c.evidence)}):")
            for e in c.evidence:
                print(f"      - {e.source_name}: {e.url} (Passage: \"{e.quote_or_passage[:80]}...\")")

        return True
    except Exception as e:
        print(f"ERROR in {title}: {e}")
        return False

async def main():
    await init_db()

    # 1. Text Forward
    await test_case(
        "1. Forwarded Text Message (₹500 Currency Hoax)",
        lambda: ingest_text("From Monday, all ₹500 notes are invalid. Forward to everyone!"),
        target_lang="hi"
    )

    # 2. Screenshot
    screenshot_path = DEMO_DIR / "whatsapp_screenshot.png"
    if screenshot_path.exists():
        await test_case(
            "2. Screenshot of WhatsApp Message (OCR Extraction)",
            lambda: ingest_image(screenshot_path.read_bytes(), "image/png"),
            target_lang="en"
        )

    # 3. Voice Note
    voice_path = DEMO_DIR / "voicenote_hindi.wav"
    if voice_path.exists():
        await test_case(
            "3. Audio Voice Note (.wav / STT Transcription)",
            lambda: ingest_voice(voice_path.read_bytes(), "audio/wav"),
            target_lang="hi"
        )

    # 4. Multi-page PDF
    pdf_path = DEMO_DIR / "multipage_notice.pdf"
    if pdf_path.exists():
        await test_case(
            "4. Multi-Page PDF Document with False Claim",
            lambda: ingest_pdf(pdf_path.read_bytes()),
            target_lang="en"
        )

    # 5. News URL
    await test_case(
        "5. News / Article URL (Trafilatura Extraction)",
        lambda: ingest_url("https://pib.gov.in/PressReleasePage.aspx?PRID=1925348"),
        target_lang="en"
    )

if __name__ == "__main__":
    asyncio.run(main())
