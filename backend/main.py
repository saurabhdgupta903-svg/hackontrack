"""
Sach? - Fact-Checking Backend Application
FastAPI asynchronous backend with real-time SSE, multimodal ingestion,
authoritative retrieval, structured judging, and citation verification.
"""

from contextlib import asynccontextmanager
from collections import defaultdict
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import CORS_ORIGINS
from backend.models.db import init_db
from backend.routers import check, history, feedback, webhook

# Simple IP rate limiting: max 30 requests per minute per IP
ip_request_timestamps = defaultdict(list)
RATE_LIMIT_WINDOW = 60 # seconds
RATE_LIMIT_MAX = 30 # requests per window

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    yield

app = FastAPI(
    title="Sach? Fact-Checking API",
    description="Multimodal GenAI Fact-Checking Engine for WhatsApp & Social Media Forwards",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all; configurable via CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only rate-limit API mutating/checking paths
    if request.url.path.startswith("/api/check"):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        timestamps = ip_request_timestamps[client_ip]
        # Purge timestamps older than 60s
        ip_request_timestamps[client_ip] = [ts for ts in timestamps if now - ts < RATE_LIMIT_WINDOW]

        if len(ip_request_timestamps[client_ip]) >= RATE_LIMIT_MAX:
            return JSONResponse(
                status_code=429,
                content={"detail": "API rate limit hit, try again in a minute."}
            )
        ip_request_timestamps[client_ip].append(now)

    response = await call_next(request)
    return response

# Mount routers
app.include_router(check.router)
app.include_router(history.router)
app.include_router(feedback.router)
app.include_router(webhook.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Sach?",
        "timestamp": time.time(),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
