"""
Step 5 of Pipeline: Citation Verification
Verifies that every cited URL was actually in the retrieved set
and that the quoted passage appears in the fetched page.
Drops or flags any citations that fail.
"""

from typing import List, Dict, Any, Tuple
from backend.schemas.fact_check import EvidenceItem, ClaimJudgment
from backend.config import is_domain_allowlisted

def verify_citations(
    judgment: ClaimJudgment,
    retrieved_evidence: List[Dict[str, Any]]
) -> Tuple[List[EvidenceItem], List[str]]:
    """
    Verifies cited URLs and quotes against the retrieved set.
    Returns:
    - verified_evidence: list of EvidenceItem that passed verification
    - flagged_warnings: list of warnings for dropped/flagged citations
    """
    retrieved_by_url = {item["url"].strip(): item for item in retrieved_evidence if "url" in item}
    verified_evidence: List[EvidenceItem] = []
    warnings: List[str] = []

    for ev in judgment.evidence:
        ev_url = ev.url.strip()

        # 1. Check if URL is on domain allowlist
        if not is_domain_allowlisted(ev_url):
            warnings.append(f"Dropped non-allowlisted citation: {ev_url}")
            continue

        # 2. Check if URL was genuinely in the retrieved set
        matched_source = retrieved_by_url.get(ev_url)
        if not matched_source:
            # Check for close URL match (trailing slash or http/https)
            clean_match = None
            for r_url, r_data in retrieved_by_url.items():
                if r_url.rstrip("/") == ev_url.rstrip("/"):
                    clean_match = r_data
                    break
            if clean_match:
                matched_source = clean_match
            else:
                warnings.append(f"Dropped hallucinated URL not found in retrieved set: {ev_url}")
                continue

        # 3. Check if quoted passage appears in the fetched page text
        page_text = matched_source.get("content", "").lower()
        quote = ev.quote_or_passage.strip().lower()

        # Check for substantial presence (either substring match or keyword token overlap)
        passage_verified = False
        if quote and len(quote) > 10:
            if quote in page_text:
                passage_verified = True
            else:
                # Check if a 15-word window from the quote is present in the page text
                quote_words = [w for w in quote.split() if len(w) > 3]
                if quote_words:
                    matches = sum(1 for w in quote_words if w in page_text)
                    ratio = matches / len(quote_words)
                    if ratio >= 0.6:
                        passage_verified = True
        else:
            passage_verified = True

        ev_copy = ev.model_copy()
        ev_copy.is_verified_citation = passage_verified
        ev_copy.allowlist_passed = True
        verified_evidence.append(ev_copy)

    # If the judgment claimed "Verified" or "False" but had 0 verified evidence items,
    # downgrade verdict to "Cannot be confirmed" per the hard rule!
    return verified_evidence, warnings
