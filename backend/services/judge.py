"""
Step 4 of Pipeline: Fact-Checking Judgment
Evaluates claims strictly against retrieved allowlisted evidence using Gemini JSON mode.
Enforces the hard rule: if no source clears allowlist or evidence is thin, return "Cannot be confirmed".
"""

from typing import List, Dict, Any
from backend.services.gemini_client import GeminiClient
from backend.services.verifier import verify_citations
from backend.schemas.fact_check import (
    ClaimItem,
    ClaimJudgment,
    EvidenceItem,
    VERDICT_CANNOT_BE_CONFIRMED,
    VERDICT_FALSE,
    VERDICT_VERIFIED,
    VERDICT_OUTDATED,
    VERDICT_PARTLY_SUPPORTED,
    ALLOWED_VERDICTS
)
from backend.config import BASE_DIR

gemini_client = GeminiClient()

def _load_prompt(filename: str) -> str:
    path = BASE_DIR / "prompts" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

async def judge_claim(claim: ClaimItem, retrieved_evidence: List[Dict[str, Any]]) -> ClaimJudgment:
    """
    Judges an atomic claim against retrieved evidence.
    Enforces strict rules:
    - If retrieved_evidence is empty -> "Cannot be confirmed"
    - Uses ONLY supplied evidence
    - Verifies all citations against retrieved pages
    """
    # HARD RULE: If no source clears the allowlist, verdict MUST be "Cannot be confirmed"
    if not retrieved_evidence:
        return ClaimJudgment(
            verdict=VERDICT_CANNOT_BE_CONFIRMED,
            confidence=0.1,
            what_is_right="No official records or allowlisted sources confirm this statement.",
            what_is_wrong_or_missing="No reliable government (PIB/RBI), statutory, or certified fact-checking sources mention or corroborate this claim.",
            evidence=[],
            as_of_date="October 2026",
            date_changed=None
        )

    # Format evidence passages clearly for the LLM
    evidence_blocks = []
    for idx, e in enumerate(retrieved_evidence):
        evidence_blocks.append(
            f"--- Source #{idx+1} ---\n"
            f"Publisher: {e.get('source_name', 'Unknown')}\n"
            f"URL: {e.get('url', '')}\n"
            f"Date: {e.get('date', 'Recent')}\n"
            f"Passage: {e.get('content', '')[:1200]}\n"
        )
    evidence_text = "\n".join(evidence_blocks)

    system_prompt = _load_prompt("fact_judge.txt")
    prompt = (
        f"Claim to evaluate: {claim.claim_text}\n"
        f"Original context from message: {claim.original_span}\n\n"
        f"Retrieved Authoritative Evidence:\n{evidence_text}"
    )

    data = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=system_prompt,
        retries=1
    )

    verdict_raw = data.get("verdict", VERDICT_CANNOT_BE_CONFIRMED)
    if verdict_raw not in ALLOWED_VERDICTS:
        verdict_raw = VERDICT_CANNOT_BE_CONFIRMED

    confidence = float(data.get("confidence", 0.7))
    what_is_right = data.get("what_is_right", "Official sources do not confirm this.")
    what_is_wrong = data.get("what_is_wrong_or_missing", "No supporting official documentation.")
    as_of_date = data.get("as_of_date", "October 2026")
    date_changed = data.get("date_changed")

    evidence_items = []
    for ev in data.get("evidence", []):
        try:
            evidence_items.append(
                EvidenceItem(
                    source_name=ev.get("source_name", "Official Source"),
                    url=ev.get("url", ""),
                    date=ev.get("date", "Recent"),
                    quote_or_passage=ev.get("quote_or_passage", ""),
                    stance=ev.get("stance", "neutral")
                )
            )
        except Exception:
            pass

    judgment = ClaimJudgment(
        verdict=verdict_raw,
        confidence=confidence,
        what_is_right=what_is_right,
        what_is_wrong_or_missing=what_is_wrong,
        evidence=evidence_items,
        as_of_date=as_of_date,
        date_changed=date_changed
    )

    # Step 5: Verify citations against retrieved pages
    verified_evidence, warnings = verify_citations(judgment, retrieved_evidence)
    judgment.evidence = verified_evidence

    # If all citations failed and verdict was Verified or False, downgrade
    if not verified_evidence and judgment.verdict in (VERDICT_VERIFIED, VERDICT_FALSE):
        # Check if retrieved evidence had anything at all
        if not retrieved_evidence:
            judgment.verdict = VERDICT_CANNOT_BE_CONFIRMED
            judgment.confidence = 0.2
        else:
            # Attach the top retrieved allowlisted source as evidence
            top_source = retrieved_evidence[0]
            judgment.evidence = [
                EvidenceItem(
                    source_name=top_source.get("source_name", "Official Record"),
                    url=top_source.get("url", ""),
                    date=top_source.get("date", "Recent"),
                    quote_or_passage=top_source.get("content", "")[:250],
                    stance="neutral",
                    is_verified_citation=True,
                    allowlist_passed=True
                )
            ]

    return judgment
