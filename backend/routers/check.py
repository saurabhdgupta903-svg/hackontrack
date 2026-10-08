"""
Check Router: Endpoints for Text, Upload (Image, Voice, PDF), URL and SSE streaming
"""

import json
import hashlib
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.fact_check import CheckRequest, FactCheckResponse
from backend.services.ingest import (
    ingest_text,
    ingest_image,
    ingest_voice,
    ingest_pdf,
    ingest_url
)
from backend.services.pipeline import run_pipeline_stream, run_pipeline_sync

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
    target_language: str = Form("auto")
):
    """
    Handles uploaded Image, Voice Note, or PDF with validation on size and MIME type.
    """
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    # 1. Image validation
    if input_type == "image":
        if file_size_mb > 10:
            raise HTTPException(status_code=400, detail="Image exceeds the 10 MB limit.")
        allowed_image_mimes = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        if file.content_type not in allowed_image_mimes and not any(file.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            raise HTTPException(status_code=400, detail="Invalid image type. Please upload JPG, PNG, or WebP.")

        try:
            ingest_res = await ingest_image(file_bytes, file.content_type or "image/jpeg")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 2. Voice note validation
    elif input_type == "voice":
        if file_size_mb > 15:
            raise HTTPException(status_code=400, detail="Voice note too long. Maximum audio size is 15 MB (~2 minutes).")
        try:
            ingest_res = await ingest_voice(file_bytes, file.content_type or "audio/mp3")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 3. PDF validation
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
    file: Optional[UploadFile] = File(None)
):
    """
    Server-Sent Events (SSE) streaming endpoint providing real-time pipeline status updates:
    'Reading image... Finding claims... Checking sources...'
    """
    ip_hash = get_client_ip_hash(request)

    async def event_generator():
        try:
            # 1. Ingest based on type
            if input_type == "text":
                if not text or not text.strip():
                    yield f"data: {json.dumps({'error': 'Text cannot be empty'})}\n\n"
                    return
                ingest_res = await ingest_text(text)
            elif input_type == "url":
                if not url or not url.strip():
                    yield f"data: {json.dumps({'error': 'URL cannot be empty'})}\n\n"
                    return
                ingest_res = await ingest_url(url)
            elif input_type in ("image", "voice", "pdf"):
                if not file:
                    yield f"data: {json.dumps({'error': 'No file uploaded'})}\n\n"
                    return
                file_bytes = await file.read()
                if input_type == "image":
                    ingest_res = await ingest_image(file_bytes, file.content_type or "image/jpeg")
                elif input_type == "voice":
                    ingest_res = await ingest_voice(file_bytes, file.content_type or "audio/mp3")
                else:
                    ingest_res = await ingest_pdf(file_bytes)
            else:
                yield f"data: {json.dumps({'error': 'Invalid input type'})}\n\n"
                return

            # 2. Run pipeline generator
            async for step in run_pipeline_stream(ingest_res, target_language, ip_hash):
                yield f"data: {json.dumps(step)}\n\n"

        except Exception as e:
            err_msg = str(e)
            yield f"data: {json.dumps({'stage': 'error', 'error': err_msg})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
