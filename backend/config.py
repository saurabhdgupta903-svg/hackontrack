"""
Sach? - Configuration and Domain Allowlist
"""

import os
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── API Keys & Endpoints ──────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Real Gemini model IDs (env-configured model goes FIRST in fallback list)
_env_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_MODEL = _env_model

# Fallback list: env model first, then known-good models that are live in API
GEMINI_FALLBACK_MODELS: List[str] = [
    _env_model,
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]
# Deduplicate while preserving order
seen: set = set()
_deduped: List[str] = []
for _m in GEMINI_FALLBACK_MODELS:
    if _m not in seen:
        seen.add(_m)
        _deduped.append(_m)
GEMINI_FALLBACK_MODELS = _deduped

GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-3.5-pro")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
FACTCHECK_API_KEY = os.getenv("FACTCHECK_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ── Database ──────────────────────────────────────────────────────────────────
# Always resolve sqlite path relative to BASE_DIR so it doesn't depend on cwd
_raw_db_url = os.getenv("DATABASE_URL", "")
if not _raw_db_url:
    # Build absolute path: <project_root>/data/sach.db
    _db_path = BASE_DIR / "data" / "sach.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{_db_path.as_posix()}"
else:
    DATABASE_URL = _raw_db_url

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ORIGINS: List[str] = [
    orig.strip()
    for orig in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if orig.strip()
]

# ── Strict Domain Allowlist ───────────────────────────────────────────────────
# Only pages from these domains are accepted as valid evidence sources.
ALLOWLISTED_DOMAINS: List[str] = [
    # Official Indian Government & Statutory Bodies
    "pib.gov.in",
    "rbi.org.in",
    "mohfw.gov.in",
    "who.int",
    "icmr.gov.in",
    "india.gov.in",
    "eci.gov.in",
    "imd.gov.in",
    "upsc.gov.in",
    "ssc.gov.in",
    "incometax.gov.in",
    "uidai.gov.in",
    "mha.gov.in",
    "mea.gov.in",
    "cbse.gov.in",
    "epfindia.gov.in",

    # Reputable Certified Fact-Checkers (IFCN signatories / India)
    "altnews.in",
    "boomlive.in",
    "factly.in",
    "vishvasnews.com",
    "newschecker.in",
    "thequint.com",         # Quint WebQoof
    "indiatoday.in",        # India Today Anti Fake News War Room (AFWA)
    "logicallyfacts.com",
    "thip.media",           # The Healthy Indian Project (Health fact-checker)

    # Major Wire Services & Public Broadcasters
    "ptinews.com",
    "aninews.in",
    "reuters.com",
    "apnews.com",
    "newsonair.gov.in",     # All India Radio News
    "sansad.in",            # Parliament of India
]


def is_domain_allowlisted(url_or_domain: str) -> bool:
    """
    Checks if a given URL or hostname belongs to an allowlisted domain.
    Matches subdomains too (e.g. factcheck.pib.gov.in matches pib.gov.in).
    """
    if not url_or_domain:
        return False
    from urllib.parse import urlparse
    parsed = urlparse(url_or_domain)
    hostname = (parsed.hostname or url_or_domain).lower()
    if ":" in hostname:
        hostname = hostname.split(":")[0]
    for domain in ALLOWLISTED_DOMAINS:
        domain_clean = domain.lower()
        if hostname == domain_clean or hostname.endswith("." + domain_clean):
            return True
    return False


# ── Verdict Labels ────────────────────────────────────────────────────────────
VERDICT_VERIFIED = "Verified"
VERDICT_FALSE = "False"
VERDICT_OUTDATED = "Outdated"
VERDICT_PARTLY_SUPPORTED = "Partly supported"
VERDICT_CANNOT_BE_CONFIRMED = "Cannot be confirmed"

ALLOWED_VERDICTS = [
    VERDICT_VERIFIED,
    VERDICT_FALSE,
    VERDICT_OUTDATED,
    VERDICT_PARTLY_SUPPORTED,
    VERDICT_CANNOT_BE_CONFIRMED,
]

# ── Supported Languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "auto": "Auto Detect",
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "mr": "मराठी (Marathi)",
    "ta": "தமிழ் (Tamil)",
    "bn": "বাংলা (Bengali)",
    "te": "తెలుగు (Telugu)",
    "gu": "ગુજરાતી (Gujarati)",
}
