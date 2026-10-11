"""
Step 5 of Pipeline: Citation Verification

FIX: 60% word-match threshold removed — only verbatim substring match is accepted.
     (60% match was allowing fake/hallucinated quotes through.)
FIX: Very short quotes (<= 10 chars) that can't be meaningfully verified are marked
     is_verified_citation=False rather than blindly passing.
FIX: Citations whose URL was not in the retrieved set are kept but flagged as
     is_verified_citation=False (not silently dropped) so the UI can distinguish them.
"""

import logging
from typing import List, Dict, Any, Tuple

from backend.schemas.fact_check import EvidenceItem, ClaimJudgment
from backend.config import is_domain_allowlisted

logger = logging.getLogger(__name__)


def verify_citations(
    judgment: ClaimJudgment,
    retrieved_evidence: List[Dict[str, Any]],
) -> Tuple[List[EvidenceItem], List[str]]:
    """
    Verifies cited URLs and quotes against the retrieved set.
    Returns:
    - verified_evidence: list of EvidenceItem that passed domain allowlist
      (is_verified_citation=True only if quote found verbatim in page text)
    - warnings: list of diagnostic strings
    """
    retrieved_by_url = {
        item["url"].strip().rstrip("/"): item
        for item in retrieved_evidence
        if "url" in item
    }
    verified_evidence: List[EvidenceItem] = []
    warnings: List[str] = []

    for ev in judgment.evidence:
        ev_url = ev.url.strip().rstrip("/") if ev.url else ""

        # 1. Domain allowlist check — drop entirely if not allowlisted
        if not is_domain_allowlisted(ev_url):
            warnings.append(f"Dropped non-allowlisted citation: {ev_url}")
            logger.info("Dropped non-allowlisted citation: %s", ev_url)
            continue

        # 2. Check if URL was in the retrieved set (exact or trailing-slash match)
        matched_source = retrieved_by_url.get(ev_url)
        if not matched_source:
            # Try matching without http/https prefix differences
            clean_ev = ev_url.replace("https://", "").replace("http://", "")
            for r_url, r_data in retrieved_by_url.items():
                r_clean = r_url.replace("https://", "").replace("http://", "")
                if r_clean == clean_ev:
                    matched_source = r_data
                    break

        if not matched_source:
            # URL is allowlisted but was NOT in our retrieved set — flag as unverified
            # (LLM may have fabricated a plausible-looking URL on an allowlisted domain)
            warnings.append(f"URL not found in retrieved set (may be hallucinated): {ev_url}")
            logger.info("Citation URL not in retrieved set: %s", ev_url)
            ev_copy = ev.model_copy()
            ev_copy.is_verified_citation = False
            ev_copy.allowlist_passed = True
            verified_evidence.append(ev_copy)
            continue

        # 3. Verify quoted passage appears VERBATIM in the fetched page text
        page_text = matched_source.get("content", "").lower()
        quote = (ev.quote_or_passage or "").strip().lower()

        passage_verified = False
        if quote and len(quote) > 10:
            # STRICT: require the quoted text to appear verbatim as a substring
            passage_verified = quote in page_text
            if not passage_verified:
                warnings.append(
                    f"Quote not found verbatim in page {ev_url}: '{quote[:80]}...'"
                )
                logger.info("Quote not found verbatim in %s", ev_url)
        else:
            # Quote too short to verify — mark as unverified (not a pass)
            passage_verified = False
            if quote:
                warnings.append(f"Quote too short to verify (<= 10 chars): '{quote}'")

        ev_copy = ev.model_copy()
        ev_copy.is_verified_citation = passage_verified
        ev_copy.allowlist_passed = True
        verified_evidence.append(ev_copy)

    return verified_evidence, warnings
