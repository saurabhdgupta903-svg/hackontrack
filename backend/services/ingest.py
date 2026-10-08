"""
Step 1 of Pipeline: Ingestion and text extraction from multimodal inputs
Supports: Text, Screenshot (Image), Voice note, PDF, URL
"""

import io
import pymupdf as fitz
import httpx
import trafilatura
from typing import Dict, Any, Optional
from backend.services.gemini_client import GeminiClient
from backend.schemas.fact_check import IngestResult
from backend.config import SARVAM_API_KEY, BASE_DIR

gemini_client = GeminiClient()

def _load_prompt(filename: str) -> str:
    prompt_path = BASE_DIR / "prompts" / filename
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""

async def ingest_text(text: str) -> IngestResult:
    """Ingests plain forwarded text message."""
    clean_text = text.strip()
    return IngestResult(
        raw_text=clean_text,
        input_type="text",
        detected_language="auto",
        metadata={"char_count": len(clean_text)}
    )

async def ingest_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> IngestResult:
    """
    Ingests screenshot or photo using Gemini Multimodal OCR.
    Extracts text, detected language, and WhatsApp metadata (forward tags, timestamps).
    """
    prompt = _load_prompt("ocr_image.txt")
    if not prompt:
        prompt = "Extract all text from this image and detect language. Return JSON: {\"extracted_text\": \"...\", \"language\": \"...\", \"metadata\": {}}"

    data = await gemini_client.generate_json(
        prompt=prompt,
        image_bytes=image_bytes,
        image_mime=mime_type,
        retries=1
    )

    extracted_text = data.get("extracted_text", "").strip()
    language = data.get("language", "en")
    meta = data.get("metadata", {})

    if not extracted_text:
        raise ValueError("Couldn't read any text from this image. Try a clearer screenshot.")

    return IngestResult(
        raw_text=extracted_text,
        input_type="image",
        detected_language=language,
        metadata=meta
    )

async def ingest_voice(audio_bytes: bytes, mime_type: str = "audio/mp3") -> IngestResult:
    """
    Ingests voice notes (.ogg, .opus, .mp3, .m4a, .wav).
    Uses Sarvam AI (Saarika) if key available; falls back to Gemini Audio transcription.
    """
    # 1. Try Sarvam AI Saarika if key present
    if SARVAM_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("audio_note", audio_bytes, mime_type)}
                headers = {"api-subscription-key": SARVAM_API_KEY}
                resp = await client.post(
                    "https://api.sarvam.ai/speech-to-text",
                    files=files,
                    headers=headers
                )
                if resp.status_code == 200:
                    res_json = resp.json()
                    transcript = res_json.get("transcript", "").strip()
                    lang = res_json.get("language_code", "hi")
                    if transcript:
                        return IngestResult(
                            raw_text=transcript,
                            input_type="voice",
                            detected_language=lang,
                            metadata={"provider": "sarvam_saarika"}
                        )
        except Exception:
            pass # Fall back to Gemini

    # 2. Fall back to Gemini audio input
    prompt = (
        "Accurately transcribe this audio voice note into text. "
        "The voice note may be in Hindi, Marathi, Tamil, Bengali, Telugu, Gujarati, or English. "
        "Also detect the language spoken. "
        "Return JSON: {\"extracted_text\": \"...\", \"language\": \"...\"}"
    )

    data = await gemini_client.generate_json(
        prompt=prompt,
        audio_bytes=audio_bytes,
        audio_mime=mime_type,
        retries=1
    )

    transcript = data.get("extracted_text", "").strip()
    if not transcript:
        raise ValueError("Could not transcribe audio from the voice note. The audio may be silent or corrupted.")

    return IngestResult(
        raw_text=transcript,
        input_type="voice",
        detected_language=data.get("language", "auto"),
        metadata={"provider": "gemini_multimodal_audio"}
    )

async def ingest_pdf(pdf_bytes: bytes) -> IngestResult:
    """
    Ingests PDF documents using PyMuPDF; sends scanned/empty PDFs to Gemini multimodal.
    """
    doc_text = ""
    page_count = 0
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        for page in doc:
            doc_text += page.get_text() + "\n"
        doc_text = doc_text.strip()
    except Exception as e:
        doc_text = ""

    # If PyMuPDF found little or no text (e.g. scanned document or graphics-heavy PDF), send to Gemini
    if len(doc_text) < 50:
        prompt = (
            "Extract all readable text and factual claims from this PDF document. "
            "Return JSON: {\"extracted_text\": \"...\", \"language\": \"...\"}"
        )
        data = await gemini_client.generate_json(
            prompt=prompt,
            pdf_bytes=pdf_bytes,
            retries=1
        )
        doc_text = data.get("extracted_text", "").strip()
        detected_lang = data.get("language", "auto")
        provider = "gemini_multimodal_pdf"
    else:
        detected_lang = "auto"
        provider = "pymupdf"

    if not doc_text:
        raise ValueError("Could not extract any text from this PDF file.")

    return IngestResult(
        raw_text=doc_text,
        input_type="pdf",
        detected_language=detected_lang,
        metadata={"pages": page_count, "extractor": provider}
    )

async def ingest_url(url: str) -> IngestResult:
    """
    Ingests article content from a web link using trafilatura with readability fallback.
    """
    clean_url = url.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(clean_url, headers=headers)
            if resp.status_code in (401, 403):
                raise ValueError("This link needs a login, so we can't open it.")
            if resp.status_code != 200:
                raise ValueError(f"Failed to access URL (HTTP {resp.status_code}). Please verify the link.")

            html_content = resp.text
    except httpx.RequestError as e:
        raise ValueError(f"Network error while connecting to URL: {e}")

    # Use trafilatura to extract clean main text
    extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
    if not extracted or len(extracted.strip()) < 40:
        # Fallback to trafilatura bare or raise clear error
        extracted = trafilatura.extract(html_content, favor_precision=False)
        if not extracted or len(extracted.strip()) < 30:
            raise ValueError("Could not find article content at this URL. It may require login or JavaScript rendering.")

    return IngestResult(
        raw_text=extracted.strip(),
        input_type="url",
        detected_language="auto",
        metadata={"url": clean_url, "char_count": len(extracted)}
    )
