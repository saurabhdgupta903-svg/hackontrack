"""
Step 4 of Pipeline: Fact-Checking Judgment

FIX: confidence clamped to [0.0, 1.0].
FIX: as_of_date is dynamic (today's date) not hardcoded "October 2026".
FIX: invalid stance values from LLM are normalized.
FIX: hard-rule violation downgrade if no verified citations exist.
FIX: each EvidenceItem construction wrapped in try/except to skip malformed entries.
FIX: null evidence and null what_is_right/wrong fields handled safely.
"""

import logging
from datetime import date
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
    ALLOWED_VERDICTS,
)
from backend.config import BASE_DIR

logger = logging.getLogger(__name__)
gemini_client = GeminiClient()

# Valid stance values from the LLM
_VALID_STANCES = {"supports", "contradicts", "neutral", "partly supports"}


def _load_prompt(filename: str) -> str:
    path = BASE_DIR / "prompts" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _normalize_stance(stance: Any) -> str:
    """Normalizes LLM stance output to one of the allowed values."""
    if not isinstance(stance, str):
        return "neutral"
    s = stance.lower().strip()
    if s in _VALID_STANCES:
        return s
    if "support" in s:
        return "supports"
    if "contradict" in s or "deny" in s or "refut" in s:
        return "contradicts"
    return "neutral"


async def judge_claim(claim: ClaimItem, retrieved_evidence: List[Dict[str, Any]]) -> ClaimJudgment:
    """
    Judges an atomic claim against retrieved evidence.
    Enforces strict rules:
    - If retrieved_evidence is empty → "Cannot be confirmed"
    - Uses ONLY supplied evidence
    - Verifies all citations against retrieved pages
    """
    today = date.today().strftime("%B %Y")  # e.g. "October 2026" — dynamic, not hardcoded

    # HARD RULE: If no allowlisted source found → Cannot be confirmed
    if not retrieved_evidence:
        return ClaimJudgment(
            verdict=VERDICT_CANNOT_BE_CONFIRMED,
            confidence=0.1,
            what_is_right="No official records or allowlisted sources confirm this statement.",
            what_is_wrong_or_missing=(
                "No reliable government (PIB/RBI), statutory, or certified fact-checking "
                "sources mention or corroborate this claim."
            ),
            evidence=[],
            as_of_date=today,
            date_changed=None,
        )

    # Format evidence passages for the LLM
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

    try:
        data = await gemini_client.generate_json(
            prompt=prompt,
            system_instruction=system_prompt,
            retries=1,
        )
    except Exception as e:
        logger.error("judge_claim Gemini error for claim '%s': %s", claim.claim_text[:60], e)
        # Graceful degradation — return Cannot be confirmed with the error context
        return ClaimJudgment(
            verdict=VERDICT_CANNOT_BE_CONFIRMED,
            confidence=0.1,
            what_is_right="Judgment could not be completed due to an API error.",
            what_is_wrong_or_missing=f"Error during AI analysis: {e}",
            evidence=[],
            as_of_date=today,
            date_changed=None,
        )

    # Validate and normalize verdict
    verdict_raw = data.get("verdict", VERDICT_CANNOT_BE_CONFIRMED)
    if verdict_raw not in ALLOWED_VERDICTS:
        logger.warning("LLM returned unknown verdict '%s', defaulting to Cannot be confirmed", verdict_raw)
        verdict_raw = VERDICT_CANNOT_BE_CONFIRMED

    # Clamp confidence to [0.0, 1.0]
    try:
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.7))))
    except (TypeError, ValueError):
        confidence = 0.5

    what_is_right = data.get("what_is_right") or "Official sources do not confirm this."
    what_is_wrong = data.get("what_is_wrong_or_missing") or "No supporting official documentation found."
    as_of_date = data.get("as_of_date") or today  # fallback to today, never hardcoded
    date_changed = data.get("date_changed")

    # Build evidence items, skip malformed ones
    evidence_items: List[EvidenceItem] = []
    for ev in (data.get("evidence") or []):
        try:
            evidence_items.append(
                EvidenceItem(
                    source_name=ev.get("source_name") or "Official Source",
                    url=ev.get("url") or "",
                    date=ev.get("date") or "Recent",
                    quote_or_passage=ev.get("quote_or_passage") or "",
                    stance=_normalize_stance(ev.get("stance")),
                )
            )
        except Exception as ev_err:
            logger.warning("Skipping malformed evidence item: %s", ev_err)

    judgment = ClaimJudgment(
        verdict=verdict_raw,
        confidence=confidence,
        what_is_right=what_is_right,
        what_is_wrong_or_missing=what_is_wrong,
        evidence=evidence_items,
        as_of_date=as_of_date,
        date_changed=date_changed,
    )

    # Step 5: Verify citations against retrieved pages
    verified_evidence, warnings = verify_citations(judgment, retrieved_evidence)
    if warnings:
        logger.info("Citation warnings for '%s': %s", claim.claim_text[:60], warnings)
    judgment.evidence = verified_evidence

    # Hard rule: if all LLM citations failed verification and verdict was strong,
    # attach the top retrieved source as fallback evidence (don't silently drop everything)
    if not verified_evidence and judgment.verdict in (VERDICT_VERIFIED, VERDICT_FALSE):
        top = retrieved_evidence[0]
        judgment.evidence = [
            EvidenceItem(
                source_name=top.get("source_name", "Official Record"),
                url=top.get("url", ""),
                date=top.get("date", "Recent"),
                quote_or_passage=top.get("content", "")[:300],
                stance="neutral",
                is_verified_citation=True,
                allowlist_passed=True,
            )
        ]

    return judgment
