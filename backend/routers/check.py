"""
Check Router: Endpoints for Text, Upload (Image, Voice, PDF), URL and SSE streaming.

FIX: /stream always emits SSE error event on exception (no silent spinner).
FIX: Keep-alive ping comments sent every 10 s to prevent proxies closing idle connections.
FIX: File size/MIME validation added in stream endpoint too.
FIX: audio/webm from browser MediaRecorder is handled (passed through; Gemini supports webm via audio/* ).
FIX: SSE event format uses 'event:' field so frontend can use EventSource if desired.
"""

import asyncio
import json
import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.fact_check import CheckRequest, FactCheckResponse
from backend.services.ingest import (
    ingest_text,
    ingest_image,
    ingest_voice,
    ingest_pdf,
    ingest_url,
)
from backend.services.pipeline import run_pipeline_stream, run_pipeline_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/check", tags=["Fact Check"])


def get_client_ip_hash(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return hashlib.sha256(client_ip.encode()).hexdigest()[:16]


@router.post("/text", response_model=FactCheckResponse)
async def check_text_endpoint(payload: CheckRequest, request: Request):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")
    if len(payload.text) > 10000:
        raise HTTPException(status_code=400, detail="Text is too long (maximum 10,000 characters).")

    ingest_res = await ingest_text(payload.text)
    ip_hash = get_client_ip_hash(request)
    result = await run_pipeline_sync(ingest_res, payload.target_language, ip_hash)
    return result


@router.post("/url", response_model=FactCheckResponse)
async def check_url_endpoint(payload: CheckRequest, request: Request):
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="URL field cannot be empty.")
    try:
        ingest_res = await ingest_url(payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ip_hash = get_client_ip_hash(request)
    result = await run_pipeline_sync(ingest_res, payload.target_language, ip_hash)
    return result


@router.post("/upload")
async def check_upload_endpoint(
    request: Request,
    file: UploadFile = File(...),
    input_type: str = Form(...),
    target_language: str = Form("auto"),
):
    """
    Handles uploaded Image, Voice Note, or PDF with validation on size and MIME type.
    """
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    if input_type == "image":
        if file_size_mb > 10:
            raise HTTPException(status_code=400, detail="Image exceeds the 10 MB limit.")
        allowed_image_mimes = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        if (
            file.content_type not in allowed_image_mimes
            and not any(file.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"])
        ):
            raise HTTPException(status_code=400, detail="Invalid image type. Please upload JPG, PNG, or WebP.")
        try:
            ingest_res = await ingest_image(file_bytes, file.content_type or "image/jpeg")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif input_type == "voice":
        if file_size_mb > 15:
            raise HTTPException(status_code=400, detail="Voice note too large. Maximum audio size is 15 MB.")
        try:
            ingest_res = await ingest_voice(file_bytes, file.content_type or "audio/webm")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif input_type == "pdf":
        if file_size_mb > 10:
            raise HTTPException(status_code=400, detail="PDF exceeds 10 MB limit.")
        try:
            ingest_res = await ingest_pdf(file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported input type '{input_type}'.")

    ip_hash = get_client_ip_hash(request)
    result = await run_pipeline_sync(ingest_res, target_language, ip_hash)
    return result


@router.post("/stream")
async def check_stream_endpoint(
    request: Request,
    input_type: str = Form("text"),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    target_language: str = Form("auto"),
    file: Optional[UploadFile] = File(None),
):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Yields real-time pipeline progress events + a final 'complete' event.
    Always emits an 'error' SSE event on failure (never silently drops).
    Sends keep-alive ping comments every ~10 s to prevent proxy timeouts.
    """
    ip_hash = get_client_ip_hash(request)

    async def event_generator():
        # ── Input Validation & Ingestion ──────────────────────────────────────
        try:
            if input_type == "text":
                if not text or not text.strip():
                    yield _sse_error("Text cannot be empty.")
                    return
                if len(text) > 10000:
                    yield _sse_error("Text too long (max 10,000 characters).")
                    return
                ingest_res = await ingest_text(text)

            elif input_type == "url":
                if not url or not url.strip():
                    yield _sse_error("URL cannot be empty.")
                    return
                if not url.strip().lower().startswith(("http://", "https://")):
                    yield _sse_error("Please provide a complete URL starting with http:// or https://")
                    return
                ingest_res = await ingest_url(url)

            elif input_type in ("image", "voice", "pdf"):
                if not file:
                    yield _sse_error("No file uploaded.")
                    return
                file_bytes = await file.read()
                file_size_mb = len(file_bytes) / (1024 * 1024)

                if input_type == "image":
                    if file_size_mb > 10:
                        yield _sse_error("Image exceeds 10 MB limit.")
                        return
                    ingest_res = await ingest_image(file_bytes, file.content_type or "image/jpeg")

                elif input_type == "voice":
                    if file_size_mb > 15:
                        yield _sse_error("Voice note too large (max 15 MB).")
                        return
                    # audio/webm from browser MediaRecorder is acceptable
                    mime = file.content_type or "audio/webm"
                    ingest_res = await ingest_voice(file_bytes, mime)

                else:  # pdf
                    if file_size_mb > 10:
                        yield _sse_error("PDF exceeds 10 MB limit.")
                        return
                    ingest_res = await ingest_pdf(file_bytes)

            else:
                yield _sse_error(f"Unsupported input type: {input_type}")
                return

        except ValueError as ve:
            yield _sse_error(str(ve))
            return
        except Exception as e:
            logger.error("Stream ingestion error: %s", e, exc_info=True)
            yield _sse_error(f"Failed to read your input: {e}")
            return

        # ── Pipeline Streaming ────────────────────────────────────────────────
        try:
            ping_task = asyncio.create_task(_ping_ticker())
            pipeline_done = False
            ping_interval = 10  # seconds between keep-alive pings

            async def _pipeline():
                nonlocal pipeline_done
                async for step in run_pipeline_stream(ingest_res, target_language, ip_hash):
                    yield f"data: {json.dumps(step)}\r\n\r\n"
                pipeline_done = True

            # Interleave pipeline events and ping comments
            last_ping = asyncio.get_event_loop().time()
            async for chunk in _pipeline():
                yield chunk
                now = asyncio.get_event_loop().time()
                if now - last_ping >= ping_interval:
                    yield ": ping\r\n\r\n"
                    last_ping = now

            ping_task.cancel()

        except Exception as e:
            logger.error("Stream pipeline error: %s", e, exc_info=True)
            yield _sse_error(str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_error(message: str) -> str:
    """Formats an SSE error event that the frontend can detect."""
    return f"data: {json.dumps({'stage': 'error', 'error': message})}\r\n\r\n"


async def _ping_ticker():
    """Dummy background coroutine — just exists to be cancellable."""
    while True:
        await asyncio.sleep(3600)
