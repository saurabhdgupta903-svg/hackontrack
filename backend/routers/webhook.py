"""
WhatsApp Cloud API Webhook Handler
Allows users to forward suspicious messages directly to a WhatsApp business number.
Exposes status endpoint indicating whether the WhatsApp channel is configured/live.
"""

import os
from fastapi import APIRouter, Request, Response, HTTPException, Query
from backend.services.ingest import ingest_text
from backend.services.pipeline import run_pipeline_sync

router = APIRouter(prefix="/api/webhook", tags=["WhatsApp Webhook"])

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sach_verify_token_dev")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

@router.get("/status")
async def get_channel_status():
    """Returns current status of the WhatsApp bot channel."""
    is_live = bool(WHATSAPP_API_TOKEN and PHONE_NUMBER_ID)
    return {
        "channel": "WhatsApp Cloud API",
        "is_live": is_live,
        "phone_number_id": PHONE_NUMBER_ID or "Not Configured",
        "webhook_endpoint": "/api/webhook/whatsapp",
        "status_message": (
            "WhatsApp Forwarding Bot is Active (Ready to receive forwards)"
            if is_live else
            "Webhook ready. Cloud API credentials pending in .env (WHATSAPP_API_TOKEN)."
        )
    }

@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Webhook verification for Meta / WhatsApp Cloud API."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch.")

@router.post("/whatsapp")
async def receive_whatsapp_message(request: Request):
    """
    Receives incoming forwarded messages from WhatsApp Cloud API,
    runs the fact-check pipeline, and prepares response text.
    """
    payload = await request.json()
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    sender = msg.get("from")
                    msg_type = msg.get("type")
                    if msg_type == "text":
                        text_body = msg.get("text", {}).get("body", "")
                        ingest_res = await ingest_text(text_body)
                        result = await run_pipeline_sync(ingest_res, target_language="auto")
                        # In production with WHATSAPP_API_TOKEN, we post reply to Graph API
                        # For now, return verified JSON payload
                        return {
                            "status": "processed",
                            "sender": sender,
                            "summary": result.summary.summary_text,
                            "dominant_verdict": result.summary.dominant_verdict
                        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {"status": "ok"}
