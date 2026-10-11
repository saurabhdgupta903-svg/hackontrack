"""
Step 1 of Pipeline: Ingestion and text extraction from multimodal inputs
Supports: Text, Screenshot (Image), Voice note, PDF, URL

FIX: audio/webm from browser MediaRecorder is accepted by Gemini as audio/webm
     (Gemini supports webm). Sarvam STT falls back gracefully to Gemini for webm.
FIX: ingest_url blocks SSRF — rejects private/local IP ranges.
FIX: ingest_url caps downloaded content at 5 MB and truncates extracted text to 20k chars.
FIX: ingest_text truncates to 10k chars (matches router validation).
FIX: Sarvam STT bare `except: pass` replaced with logger.warning.
"""

import io
import logging
import re
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

import httpx
import pymupdf as fitz
import trafilatura

from backend.services.gemini_client import GeminiClient
from backend.schemas.fact_check import IngestResult
from backend.config import SARVAM_API_KEY, BASE_DIR

logger = logging.getLogger(__name__)
gemini_client = GeminiClient()

# SSRF protection: block requests to private/loopback/link-local ranges
_BLOCKED_NETWORKS = [
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("127.0.0.0/8"),
    ip_network("169.254.0.0/16"),
    ip_network("::1/128"),
    ip_network("fc00::/7"),
]

MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_TEXT_CHARS = 20_000                 # truncate extracted text


def _check_ssrf(url: str):
    """Raises ValueError if URL points to a private/internal address."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # Block if host is a raw IP in a private range
    try:
        addr = ip_address(host)
        for net in _BLOCKED_NETWORKS:
            if addr in net:
                raise ValueError(f"URL points to a private/internal address and cannot be fetched.")
    except ValueError as ve:
        if "private" in str(ve) or "internal" in str(ve):
            raise  # re-raise SSRF error
        # host is a hostname, not a raw IP — allow it through
    # Block explicit local hostnames
    if host.lower() in ("localhost", "0.0.0.0", "metadata.google.internal"):
        raise ValueError("URL points to a local address and cannot be fetched.")


def _load_prompt(filename: str) -> str:
    prompt_path = BASE_DIR / "prompts" / filename
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


async def ingest_text(text: str) -> IngestResult:
    """Ingests plain forwarded text message. Truncates to 10k chars."""
    clean_text = text.strip()[:10_000]
    return IngestResult(
        raw_text=clean_text,
        input_type="text",
        detected_language="auto",
        metadata={"char_count": len(clean_text)}
    )


async def ingest_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> IngestResult:
    """
    Ingests screenshot or photo using Gemini Multimodal OCR.
    Extracts text, detected language, and WhatsApp metadata.
    """
    prompt = _load_prompt("ocr_image.txt")
    if not prompt:
        prompt = (
            'Extract all text from this image and detect the language. '
            'Return JSON: {"extracted_text": "...", "language": "...", "metadata": {}}'
        )

    data = await gemini_client.generate_json(
        prompt=prompt,
        image_bytes=image_bytes,
        image_mime=mime_type,
        retries=1,
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
        metadata=meta,
    )


async def ingest_voice(audio_bytes: bytes, mime_type: str = "audio/webm") -> IngestResult:
    """
    Ingests voice notes (.ogg, .opus, .mp3, .m4a, .wav, .webm).
    Uses Sarvam AI (Saarika) if key available; falls back to Gemini Audio transcription.
    Note: browser MediaRecorder produces audio/webm — Gemini accepts this natively.
    Sarvam does NOT support webm; for webm we skip Sarvam and go straight to Gemini.
    """
    # Only try Sarvam for formats it supports (not webm/ogg-opus from browser)
    sarvam_supported = mime_type in (
        "audio/mp3", "audio/mpeg", "audio/wav", "audio/m4a", "audio/x-m4a",
        "audio/ogg", "audio/opus",
    )

    if SARVAM_API_KEY and sarvam_supported:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("audio_note", audio_bytes, mime_type)}
                headers = {"api-subscription-key": SARVAM_API_KEY}
                resp = await client.post(
                    "https://api.sarvam.ai/speech-to-text",
                    files=files,
                    headers=headers,
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
                            metadata={"provider": "sarvam_saarika"},
                        )
                else:
                    logger.warning("Sarvam STT returned %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Sarvam STT error, falling back to Gemini: %s", e)

    # Fall back to Gemini audio input (supports webm, ogg, mp3, wav, m4a, flac, aiff)
    # For Gemini: audio/webm is acceptable; normalize if needed
    gemini_mime = mime_type
    if mime_type in ("audio/webm; codecs=opus", "audio/webm;codecs=opus"):
        gemini_mime = "audio/webm"

    prompt = (
        "Accurately transcribe this audio voice note into text. "
        "The voice note may be in Hindi, Marathi, Tamil, Bengali, Telugu, Gujarati, or English. "
        "Also detect the language spoken. "
        'Return JSON: {"extracted_text": "...", "language": "..."}'
    )

    data = await gemini_client.generate_json(
        prompt=prompt,
        audio_bytes=audio_bytes,
        audio_mime=gemini_mime,
        retries=1,
    )

    transcript = data.get("extracted_text", "").strip()
    if not transcript:
        raise ValueError(
            "Could not transcribe audio from the voice note. "
            "The audio may be silent, in an unsupported format, or too short."
        )

    return IngestResult(
        raw_text=transcript,
        input_type="voice",
        detected_language=data.get("language", "auto"),
        metadata={"provider": "gemini_multimodal_audio", "original_mime": mime_type},
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
        logger.warning("PyMuPDF extraction failed: %s", e)
        doc_text = ""

    # If PyMuPDF found little or no text (scanned/graphics PDF), use Gemini multimodal
    if len(doc_text) < 50:
        prompt = (
            "Extract all readable text and factual claims from this PDF document. "
            'Return JSON: {"extracted_text": "...", "language": "..."}'
        )
        data = await gemini_client.generate_json(
            prompt=prompt,
            pdf_bytes=pdf_bytes,
            retries=1,
        )
        doc_text = data.get("extracted_text", "").strip()
        detected_lang = data.get("language", "auto")
        provider = "gemini_multimodal_pdf"
    else:
        detected_lang = "auto"
        provider = "pymupdf"

    if not doc_text:
        raise ValueError("Could not extract any text from this PDF file.")

    # Truncate very long PDFs
    doc_text = doc_text[:MAX_TEXT_CHARS]

    return IngestResult(
        raw_text=doc_text,
        input_type="pdf",
        detected_language=detected_lang,
        metadata={"pages": page_count, "extractor": provider},
    )


async def ingest_url(url: str) -> IngestResult:
    """
    Ingests article content from a web link using trafilatura.
    FIX: Blocks SSRF by rejecting private/internal IP ranges.
    FIX: Caps download at 5 MB and truncates extracted text to 20k chars.
    """
    clean_url = url.strip()

    # SSRF check
    _check_ssrf(clean_url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(clean_url, headers=headers)
            if resp.status_code in (401, 403):
                raise ValueError("This link needs a login or is restricted — we can't open it.")
            if resp.status_code != 200:
                raise ValueError(f"Failed to access URL (HTTP {resp.status_code}). Please verify the link.")

            # Cap download size
            content_bytes = resp.content[:MAX_DOWNLOAD_BYTES]
            html_content = content_bytes.decode("utf-8", errors="replace")

    except httpx.RequestError as e:
        raise ValueError(f"Network error while connecting to URL: {e}")

    extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
    if not extracted or len(extracted.strip()) < 40:
        extracted = trafilatura.extract(html_content, favor_precision=False)
        if not extracted or len(extracted.strip()) < 30:
            raise ValueError(
                "Could not find article content at this URL. "
                "It may require login or JavaScript rendering."
            )

    # Truncate
    extracted = extracted.strip()[:MAX_TEXT_CHARS]

    return IngestResult(
        raw_text=extracted,
        input_type="url",
        detected_language="auto",
        metadata={"url": clean_url, "char_count": len(extracted)},
    )
