"""
Step 6 of Pipeline: Plain-Language Multilingual Explanation & Audio Generation
Generates simple 6th-grade level explanation in the user's language (Hindi, Marathi,
Tamil, Bengali, Telugu, Gujarati, English) and generates audio TTS via Sarvam Bulbul
or Gemini.
"""

from typing import Dict, Any, Optional, Tuple
import httpx
from backend.services.gemini_client import GeminiClient
from backend.schemas.fact_check import ClaimJudgment, ClaimItem
from backend.config import SARVAM_API_KEY, BASE_DIR

gemini_client = GeminiClient()

LANGUAGE_NAMES = {
    "auto": "the original message language",
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "bn": "Bengali (বাংলা)",
    "te": "Telugu (తెలుగు)",
    "gu": "Gujarati (ગુજરાતી)"
}

SARVAM_VOICE_MAP = {
    "hi": "hi-IN-arvind",
    "mr": "mr-IN-arvind",
    "ta": "ta-IN-valluvar",
    "bn": "bn-IN-tapan",
    "te": "te-IN-chaitanya",
    "gu": "gu-IN-nirav",
    "en": "en-IN-arvind"
}

def _load_prompt(filename: str) -> str:
    path = BASE_DIR / "prompts" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

async def generate_sarvam_tts(text: str, lang_code: str) -> Optional[Tuple[str, str]]:
    """Generates TTS audio via Sarvam AI Bulbul if configured."""
    if not SARVAM_API_KEY or not text:
        return None

    voice_id = SARVAM_VOICE_MAP.get(lang_code, "hi-IN-arvind")
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": [text[:500]],
        "target_language_code": f"{lang_code}-IN" if len(lang_code) == 2 else lang_code,
        "speaker": voice_id,
        "model": "bulbul:v1"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                audios = data.get("audios", [])
                if audios:
                    return audios[0], "audio/wav"
    except Exception:
        pass
    return None

async def explain_claim(
    claim: ClaimItem,
    judgment: ClaimJudgment,
    target_language: str = "auto",
    detected_language: str = "English"
) -> Dict[str, Any]:
    """
    Produces plain-language 6th-grade explanation and audio readout.
    """
    lang_label = LANGUAGE_NAMES.get(target_language, target_language)
    if target_language == "auto":
        lang_label = detected_language or "Hindi"

    system_prompt = _load_prompt("explanation.txt")
    prompt = (
        f"Claim: {claim.claim_text}\n"
        f"Verdict: {judgment.verdict}\n"
        f"What is right: {judgment.what_is_right}\n"
        f"What is wrong or missing: {judgment.what_is_wrong_or_missing}\n"
        f"Target Language: {lang_label}\n"
    )

    data = await gemini_client.generate_json(
        prompt=prompt,
        system_instruction=system_prompt,
        retries=1
    )

    explanation = data.get("explanation_target_lang", "").strip()
    explanation_en = data.get("explanation_en", "").strip()

    if not explanation:
        explanation = f"Verdict: {judgment.verdict}. {judgment.what_is_wrong_or_missing}"

    # Generate optional TTS audio via Sarvam if key exists
    audio_b64 = None
    audio_mime = None
    lang_code = target_language if target_language != "auto" else "hi"
    tts_res = await generate_sarvam_tts(explanation, lang_code)
    if tts_res:
        audio_b64, audio_mime = tts_res

    return {
        "explanation": explanation,
        "explanation_en": explanation_en,
        "audio_base64": audio_b64,
        "audio_mime": audio_mime
    }
