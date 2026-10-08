"""
Gemini Client with Multimodal & Structured JSON Output Support
"""

import os
import json
import base64
import httpx
from typing import Dict, Any, Optional, List
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_PRO_MODEL, GEMINI_FALLBACK_MODELS

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.fallback_models = GEMINI_FALLBACK_MODELS
        self.pro_model = GEMINI_PRO_MODEL

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
        retries: int = 1
    ) -> Dict[str, Any]:
        """
        Sends request to Gemini with JSON output mode and returns parsed dictionary.
        Tries fallback models on 503/429/timeout errors.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        models_to_try = [self.pro_model] + self.fallback_models if use_pro else list(self.fallback_models)

        parts = []

        # Multimodal attachments
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

        # Text prompt
        parts.append({"text": prompt})

        payload: Dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        last_err = None
        for model_name in models_to_try:
            url = f"{GEMINI_BASE_URL}/{model_name}:generateContent?key={self.api_key}"
            for attempt in range(retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code in (404, 429, 503):
                            # Try next model
                            last_err = RuntimeError(f"Model {model_name} returned {resp.status_code}: {resp.text[:150]}")
                            break
                        if resp.status_code != 200:
                            raise RuntimeError(f"Gemini API returned {resp.status_code}: {resp.text}")

                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise RuntimeError(f"Gemini returned no candidates: {data}")

                        candidate = candidates[0]
                        content_parts = candidate.get("content", {}).get("parts", [])
                        if not content_parts:
                            raise RuntimeError("Gemini returned empty parts")

                        text_resp = content_parts[0].get("text", "").strip()

                        # Clean markdown codeblocks if model wrapped in ```json
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
                    if attempt < retries:
                        parts[-1]["text"] = prompt + "\n\nCRITICAL: Return ONLY valid, parseable JSON with no explanation text."
                except Exception as e:
                    last_err = e
                    break # try next model

        raise RuntimeError(f"Failed to obtain valid JSON from Gemini: {last_err}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        use_pro: bool = False
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        model_name = self.pro_model if use_pro else self.flash_model
        url = f"{GEMINI_BASE_URL}/{model_name}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
