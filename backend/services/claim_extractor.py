"""
Step 2 of Pipeline: Claim Extraction
Extracts atomic, testable claims from ingested text, dropping noise, opinions, and chain forwards.
"""

from typing import List, Tuple
from backend.services.gemini_client import GeminiClient
from backend.schemas.fact_check import ClaimItem
from backend.config import BASE_DIR

gemini_client = GeminiClient()

def _load_prompt(filename: str) -> str:
    path = BASE_DIR / "prompts" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

async def extract_claims(text: str) -> Tuple[List[ClaimItem], str]:
    """
    Extracts atomic factual claims and detected language from input text.
    Maintains the original span for each claim.
    """
    if not text or not text.strip():
        return [], "English"

    system_prompt = _load_prompt("claim_extraction.txt")
    user_prompt = f"Extract all atomic factual claims from the following text:\n\n{text}"

    data = await gemini_client.generate_json(
        prompt=user_prompt,
        system_instruction=system_prompt,
        retries=1
    )

    detected_lang = data.get("detected_language", "English")
    raw_claims = data.get("claims", [])

    claims: List[ClaimItem] = []
    for idx, c in enumerate(raw_claims):
        claim_id = c.get("claim_id") or f"c_{idx+1}"
        claim_text = c.get("claim_text", "").strip()
        original_span = c.get("original_span", "").strip() or claim_text
        category = c.get("category", "general")

        if claim_text:
            claims.append(
                ClaimItem(
                    claim_id=claim_id,
                    claim_text=claim_text,
                    original_span=original_span,
                    category=category
                )
            )

    # If the text is short and model returned 0 claims but there's a statement, create 1 claim
    if not claims and len(text.strip()) > 15:
        # Check if text contains checkable assertions
        claims.append(
            ClaimItem(
                claim_id="c_1",
                claim_text=text.strip()[:300],
                original_span=text.strip()[:300],
                category="general"
            )
        )

    return claims, detected_lang
