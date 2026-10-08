"""
Database models and connection handling
Supports SQLite (local) and PostgreSQL/Supabase (production)
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Integer, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.config import DATABASE_URL

Base = declarative_base()

class CheckRecord(Base):
    __tablename__ = "checks"

    id = Column(String(64), primary_key=True)
    input_type = Column(String(32), nullable=False)
    raw_input_anonymized = Column(Text, nullable=False)
    detected_language = Column(String(32), default="en")
    target_language = Column(String(32), default="auto")
    summary_text = Column(Text, nullable=False)
    dominant_verdict = Column(String(64), nullable=False)
    full_response_json = Column(Text, nullable=False)
    ip_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SourceCache(Base):
    __tablename__ = "source_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(128), index=True, nullable=False)
    url = Column(String(1024), nullable=False)
    title = Column(String(512), default="")
    content = Column(Text, nullable=False)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Ensure sqlite engine works with aiosqlite
db_url = DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(db_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

def anonymize_text(text: str) -> str:
    """
    Strips Indian/international phone numbers, emails, and sensitive identifiers.
    E.g. +91 9876543210 -> [REDACTED PHONE]
    """
    if not text:
        return ""
    # Phone numbers (Indian 10-digit, with optional +91 or 0 prefix, spaces, dashes)
    phone_pattern = r'(\+91[\-\s]?)?[6-9]\d{9}|\b\d{5}[\-\s]\d{5}\b|\b\d{3}[\-\s]\d{3}[\-\s]\d{4}\b'
    text = re.sub(phone_pattern, "[REDACTED PHONE]", text)
    # Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, "[REDACTED EMAIL]", text)
    return text

async def init_db():
    """Initializes tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_check(record_data: Dict[str, Any]) -> str:
    async with async_session() as session:
        record = CheckRecord(
            id=record_data["id"],
            input_type=record_data["input_type"],
            raw_input_anonymized=anonymize_text(record_data["raw_input"]),
            detected_language=record_data.get("detected_language", "en"),
            target_language=record_data.get("target_language", "auto"),
            summary_text=record_data["summary"]["summary_text"],
            dominant_verdict=record_data["summary"]["dominant_verdict"],
            full_response_json=json.dumps(record_data),
            ip_hash=record_data.get("ip_hash"),
            created_at=datetime.now(timezone.utc)
        )
        session.add(record)
        await session.commit()
        return record.id

async def get_check_history(limit: int = 50) -> List[Dict[str, Any]]:
    async with async_session() as session:
        stmt = select(CheckRecord).order_by(CheckRecord.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        records = result.scalars().all()
        history = []
        for r in records:
            history.append({
                "id": r.id,
                "input_type": r.input_type,
                "snippet": r.raw_input_anonymized[:120] + ("..." if len(r.raw_input_anonymized) > 120 else ""),
                "dominant_verdict": r.dominant_verdict,
                "summary_text": r.summary_text,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return history

async def get_check_by_id(check_id: str) -> Optional[Dict[str, Any]]:
    async with async_session() as session:
        stmt = select(CheckRecord).where(CheckRecord.id == check_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            return json.loads(record.full_response_json)
        return None

async def delete_check(check_id: str) -> bool:
    async with async_session() as session:
        stmt = delete(CheckRecord).where(CheckRecord.id == check_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

async def get_cached_source(query_hash: str) -> Optional[List[Dict[str, Any]]]:
    """Retrieve search results cached within last 24 hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    async with async_session() as session:
        stmt = select(SourceCache).where(
            SourceCache.query_hash == query_hash,
            SourceCache.cached_at >= cutoff
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        if rows:
            return [{"url": r.url, "title": r.title, "content": r.content} for r in rows]
        return None

async def set_cached_sources(query_hash: str, sources: List[Dict[str, Any]]):
    """Cache search and fetch results for 24h."""
    async with async_session() as session:
        for s in sources:
            cache_entry = SourceCache(
                query_hash=query_hash,
                url=s.get("url", ""),
                title=s.get("title", ""),
                content=s.get("content", ""),
                cached_at=datetime.now(timezone.utc)
            )
            session.add(cache_entry)
        await session.commit()
