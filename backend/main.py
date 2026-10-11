"""
Sach? - Fact-Checking Backend Application
FastAPI asynchronous backend with real-time SSE, multimodal ingestion,
authoritative retrieval, structured judging, and citation verification.

FIX: Rate limiter dict cleaned up (memory leak prevention — old IPs purged every 5 min).
FIX: /api/health actually checks DB connection.
FIX: logging.basicConfig added so all service logs are visible.
FIX: CORS uses CORS_ORIGINS from config (not hardcoded "*").
"""

import asyncio
import logging
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import CORS_ORIGINS
from backend.models.db import init_db, engine
from backend.routers import check, history, feedback, webhook

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate Limiting ─────────────────────────────────────────────────────────────
# Simple in-memory IP rate limiting: max 30 requests per minute per IP.
ip_request_timestamps: dict = defaultdict(list)
RATE_LIMIT_WINDOW = 60   # seconds
RATE_LIMIT_MAX = 30      # requests per window
_last_cleanup = time.time()


async def _cleanup_rate_limiter():
    """Removes stale IP entries from the rate limiter dict (memory leak fix)."""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup > 300:  # clean up every 5 minutes
        stale = [ip for ip, ts in ip_request_timestamps.items()
                 if not any(now - t < RATE_LIMIT_WINDOW for t in ts)]
        for ip in stale:
            del ip_request_timestamps[ip]
        _last_cleanup = now


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Sach? starting up — initialising database...")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("Sach? shutting down.")


app = FastAPI(
    title="Sach? Fact-Checking API",
    description="Multimodal GenAI Fact-Checking Engine for WhatsApp & Social Media Forwards",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# FIX: use CORS_ORIGINS from config (includes localhost:3000 and 127.0.0.1:3000)
# allow_credentials requires specific origins, not "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/check"):
        await _cleanup_rate_limiter()  # periodic cleanup to prevent memory leak
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        # Purge old timestamps for this IP
        ip_request_timestamps[client_ip] = [
            ts for ts in ip_request_timestamps[client_ip]
            if now - ts < RATE_LIMIT_WINDOW
        ]
        if len(ip_request_timestamps[client_ip]) >= RATE_LIMIT_MAX:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit reached. Please wait a minute and try again."}
            )
        ip_request_timestamps[client_ip].append(now)

    response = await call_next(request)
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(check.router)
app.include_router(history.router)
app.include_router(feedback.router)
app.include_router(webhook.router)


@app.get("/api/health")
async def health_check():
    """Health check that also verifies DB connectivity."""
    db_status = "connected"
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {e}"
        logger.error("Health check DB error: %s", e)

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "Sach?",
        "timestamp": time.time(),
        "database": db_status,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
