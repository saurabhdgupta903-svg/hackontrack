"""
Gemini Client with Multimodal & Structured JSON Output Support.

FIX: generate_text() used self.flash_model (AttributeError) — replaced with fallback list.
FIX: Invalid model names replaced with real IDs (gemini-2.5-flash, gemini-2.5-flash-lite, gemini-2.5-pro).
FIX: API key sent in x-goog-api-key header instead of URL query string (prevents key leakage in logs).
FIX: All text parts joined (not just [0]).
FIX: Safety/blocked responses handled gracefully.
FIX: Real error causes surfaced to caller instead of swallowed.
FIX: Missing key raises user-friendly ValueError immediately.
"""

import json
import base64
import logging
from typing import Dict, Any, Optional, List

import httpx

from backend.config import GEMINI_API_KEY, GEMINI_FALLBACK_MODELS, GEMINI_PRO_MODEL

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.fallback_models = GEMINI_FALLBACK_MODELS
        self.pro_model = GEMINI_PRO_MODEL

    def _headers(self) -> Dict[str, str]:
        """Return auth headers. Key goes in header, NOT in URL query string."""
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _check_api_key(self):
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Add it to your .env file as GEMINI_API_KEY=<your-key>."
            )

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        """
        Extracts and joins ALL text parts from a Gemini response.
        Handles safety blocks and empty candidates gracefully.
        """
        # Check for prompt-level safety block
        if data.get("promptFeedback", {}).get("blockReason"):
            reason = data["promptFeedback"]["blockReason"]
            raise RuntimeError(f"Gemini blocked prompt due to safety policy: {reason}")

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates. Response: {json.dumps(data)[:300]}")

        candidate = candidates[0]
        finish_reason = candidate.get("finishReason", "")
        if finish_reason in ("SAFETY", "RECITATION", "BLOCKLIST"):
            raise RuntimeError(f"Gemini response blocked: finishReason={finish_reason}")

        parts = candidate.get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError(f"Gemini returned empty parts. finishReason={finish_reason}")

        # Join ALL text parts (not just [0])
        text = " ".join(p.get("text", "") for p in parts if "text" in p).strip()
        return text

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = "image/jpeg",
        audio_bytes: Optional[bytes] = None,
        audio_mime: Optional[str] = "audio/mp3",
        pdf_bytes: Optional[bytes] = None,
        use_pro: bool = False,
        retries: int = 1,
    ) -> Dict[str, Any]:
        """
        Sends a request to Gemini with JSON output mode and returns parsed dict.
        Tries fallback models on 404/429/503/timeout errors.
        Raises RuntimeError with clear reason on permanent failures (400, 403 etc).
        """
        self._check_api_key()

        models_to_try: List[str] = (
            [self.pro_model] + list(self.fallback_models) if use_pro
            else list(self.fallback_models)
        )

        # Build multimodal parts list
        parts: List[Dict[str, Any]] = []
        if image_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": image_mime or "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode("utf-8")
                }
            })
        if audio_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": audio_mime or "audio/mp3",
                    "data": base64.b64encode(audio_bytes).decode("utf-8")
                }
            })
        if pdf_bytes:
            parts.append({
                "inline_data": {
                    "mime_type": "application/pdf",
                    "data": base64.b64encode(pdf_bytes).decode("utf-8")
                }
            })
        parts.append({"text": prompt})

        payload: Dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        last_err: Exception = RuntimeError("No models tried")
        tried: List[str] = []

        for model_name in models_to_try:
            url = f"{GEMINI_BASE_URL}/{model_name}:generateContent"
            for attempt in range(retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(url, json=payload, headers=self._headers())

                    if resp.status_code in (404, 429, 503):
                        # Transient / model-not-found → try next model
                        last_err = RuntimeError(
                            f"Model {model_name} → HTTP {resp.status_code}: {resp.text[:200]}"
                        )
                        logger.warning("Gemini: %s", last_err)
                        break  # break inner retry loop, try next model

                    if resp.status_code == 400:
                        # Permanent client error (bad request, invalid key format, etc)
                        detail = resp.text[:300]
                        raise RuntimeError(
                            f"Gemini API rejected request (HTTP 400). "
                            f"Check your API key and prompt. Detail: {detail}"
                        )

                    if resp.status_code == 403:
                        raise RuntimeError(
                            "Gemini API access denied (HTTP 403). "
                            "Your API key may be invalid or quota exceeded. "
                            "Check https://aistudio.google.com/app/apikey"
                        )

                    if resp.status_code != 200:
                        raise RuntimeError(
                            f"Gemini API error HTTP {resp.status_code}: {resp.text[:300]}"
                        )

                    data = resp.json()
                    text_resp = self._extract_text(data)

                    # Strip markdown code fences if model wrapped output in ```json
                    if text_resp.startswith("```"):
                        lines = text_resp.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        text_resp = "\n".join(lines).strip()

                    return json.loads(text_resp)

                except json.JSONDecodeError as jde:
                    last_err = jde
                    logger.warning("Gemini JSON parse error on %s attempt %d: %s", model_name, attempt, jde)
                    if attempt < retries:
                        # Ask model to be strict JSON on retry
                        parts[-1]["text"] = (
                            prompt + "\n\nCRITICAL: Return ONLY valid parseable JSON. No markdown, no explanation."
                        )
                        continue
                    break  # try next model

                except (httpx.TimeoutException, httpx.ConnectError) as net_err:
                    last_err = net_err
                    logger.warning("Gemini network error on %s: %s", model_name, net_err)
                    break  # try next model

                except RuntimeError:
                    raise  # permanent errors (400/403/safety) — don't try more models

                except Exception as e:
                    last_err = e
                    logger.error("Gemini unexpected error on %s: %s", model_name, e, exc_info=True)
                    break

            tried.append(model_name)

        # Surface a meaningful error
        raise RuntimeError(
            f"Gemini failed after trying models {tried}. "
            f"Last error: {last_err}. "
            f"Check GEMINI_API_KEY in .env and that you have quota."
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        use_pro: bool = False,
    ) -> str:
        """
        Generates free-form text (not JSON). Uses the same model fallback list.
        FIX: Removed self.flash_model (AttributeError) — uses fallback list instead.
        """
        self._check_api_key()

        models_to_try: List[str] = (
            [self.pro_model] + list(self.fallback_models) if use_pro
            else list(self.fallback_models)
        )

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        last_err: Exception = RuntimeError("No models tried")
        for model_name in models_to_try:
            url = f"{GEMINI_BASE_URL}/{model_name}:generateContent"
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(url, json=payload, headers=self._headers())

                if resp.status_code in (404, 429, 503):
                    last_err = RuntimeError(f"Model {model_name} → HTTP {resp.status_code}")
                    logger.warning("generate_text: %s", last_err)
                    continue

                if resp.status_code != 200:
                    raise RuntimeError(f"Gemini API error HTTP {resp.status_code}: {resp.text[:300]}")

                data = resp.json()
                return self._extract_text(data)

            except RuntimeError:
                raise
            except Exception as e:
                last_err = e
                logger.warning("generate_text error on %s: %s", model_name, e)
                continue

        raise RuntimeError(
            f"generate_text failed on all models. Last error: {last_err}"
        )
