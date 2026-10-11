"""
Step 3 of Pipeline: Retrieval of Authoritative Evidence
Includes:
- Google Fact Check Tools API query (with languageCode)
- Allowlist-restricted web search (Tavily primary via Authorization: Bearer, DuckDuckGo fallback)
- Page fetching in PARALLEL via asyncio.gather (was sequential)
- 24-hour persistent database caching

FIX: Tavily uses Authorization: Bearer header (not api_key in body — old method deprecated).
FIX: Pages fetched in parallel with asyncio.gather instead of sequential for loop.
FIX: bare `except: pass` replaced with logger.warning throughout.
FIX: Hint logged when no search provider configured so users know to add API keys.
FIX: Google Fact Check API receives languageCode derived from detected_language.
"""

import asyncio
import hashlib
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs, quote

import httpx
import trafilatura

from backend.config import (
    ALLOWLISTED_DOMAINS,
    is_domain_allowlisted,
    FACTCHECK_API_KEY,
    TAVILY_API_KEY,
)
from backend.models.db import get_cached_source, set_cached_sources

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Map detected language names/codes to BCP-47 codes for Google Fact Check API
_LANG_CODE_MAP = {
    "hindi": "hi", "hindi (हिन्दी)": "hi", "hi": "hi",
    "marathi": "mr", "mr": "mr",
    "tamil": "ta", "ta": "ta",
    "bengali": "bn", "bn": "bn",
    "telugu": "te", "te": "te",
    "gujarati": "gu", "gu": "gu",
    "english": "en", "en": "en",
    "auto": "en",
}


def _lang_to_bcp47(detected_language: str) -> str:
    return _LANG_CODE_MAP.get(detected_language.lower().strip(), "en")


def _clean_publisher_name(domain: str) -> str:
    if "pib.gov.in" in domain:
        return "PIB (Press Information Bureau)"
    if "rbi.org.in" in domain:
        return "Reserve Bank of India (RBI)"
    if "boomlive" in domain:
        return "BOOM Live"
    if "altnews" in domain:
        return "Alt News"
    if "factly" in domain:
        return "Factly"
    if "newschecker" in domain:
        return "Newschecker"
    if "who.int" in domain:
        return "World Health Organization (WHO)"
    if "mohfw.gov.in" in domain:
        return "Ministry of Health & Family Welfare"
    if "icmr.gov.in" in domain:
        return "ICMR"
    if "eci.gov.in" in domain:
        return "Election Commission of India"
    return domain.replace("www.", "").split(".")[0].upper()


async def query_google_fact_check(query: str, detected_language: str = "en") -> List[Dict[str, Any]]:
    """
    Queries Google Fact Check Tools API (claims:search).
    Returns list of verified reviews from certified fact checkers.
    """
    if not FACTCHECK_API_KEY:
        return []

    lang_code = _lang_to_bcp47(detected_language)
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": FACTCHECK_API_KEY,
        "pageSize": 5,
        "languageCode": lang_code,
    }

    results = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for claim in data.get("claims", []):
                    for review in claim.get("claimReview", []):
                        review_url = review.get("url", "")
                        publisher = review.get("publisher", {}).get("name", "Fact Checker")
                        rating = review.get("textualRating", "")
                        date = review.get("reviewDate", "Recent")
                        title = review.get("title", "")

                        if review_url and is_domain_allowlisted(review_url):
                            results.append({
                                "source_name": publisher,
                                "url": review_url,
                                "date": date,
                                "title": title,
                                "content": f"Fact Check Verdict: {rating}. Review: {title}",
                                "allowlist_passed": True,
                            })
            else:
                logger.warning("Google Fact Check API returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("Google Fact Check API error: %s", e)

    return results


async def search_tavily(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Queries Tavily Search API restricted to allowlisted domains.
    FIX: Uses Authorization: Bearer header (api_key in body is deprecated).
    """
    if not TAVILY_API_KEY:
        return []

    url = "https://api.tavily.com/search"
    # FIX: Send key as Authorization header, not in body
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_domains": ALLOWLISTED_DOMAINS,
        "max_results": max_results,
    }

    results = []
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for r in data.get("results", []):
                    r_url = r.get("url", "")
                    if is_domain_allowlisted(r_url):
                        results.append({
                            "source_name": _clean_publisher_name(urlparse(r_url).netloc),
                            "url": r_url,
                            "date": "Recent",
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "allowlist_passed": True,
                        })
            else:
                logger.warning("Tavily returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("Tavily search error: %s", e)

    return results


async def search_allowlist_web(query: str, max_results: int = 6) -> List[str]:
    """
    Fallback: scrapes DuckDuckGo HTML for allowlisted domain URLs.
    """
    domains_focus = (
        "site:pib.gov.in OR site:rbi.org.in OR site:boomlive.in "
        "OR site:altnews.in OR site:factly.in OR site:newschecker.in"
    )
    search_q = f"({domains_focus}) {query}"

    candidate_urls: List[str] = []

    for q in [search_q, f"{query} fact check"]:
        if len(candidate_urls) >= max_results:
            break
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={quote(q)}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(ddg_url, headers=_HEADERS)
                if resp.status_code == 200:
                    html = resp.text
                    for m in re.finditer(r'href="([^"]*uddg=[^"]*)"', html):
                        uddg = m.group(1)
                        parsed_qs = parse_qs(urlparse(uddg).query)
                        if "uddg" in parsed_qs:
                            raw_u = parsed_qs["uddg"][0]
                            if is_domain_allowlisted(raw_u) and raw_u not in candidate_urls:
                                candidate_urls.append(raw_u)
                                if len(candidate_urls) >= max_results:
                                    break
        except Exception as e:
            logger.warning("DuckDuckGo search error: %s", e)

    return candidate_urls


async def fetch_and_clean_page(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches an allowlisted URL and extracts readable body text via trafilatura.
    """
    if not is_domain_allowlisted(url):
        return None

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=_HEADERS)
            if resp.status_code != 200:
                logger.warning("fetch_and_clean_page: %s returned %d", url, resp.status_code)
                return None
            html = resp.text

        extracted = trafilatura.extract(html, include_comments=False, favor_precision=True)
        if not extracted or len(extracted) < 50:
            extracted = trafilatura.extract(html, favor_precision=False)

        if not extracted:
            logger.warning("fetch_and_clean_page: no text extracted from %s", url)
            return None

        domain = urlparse(url).netloc
        publisher_name = _clean_publisher_name(domain)

        return {
            "source_name": publisher_name,
            "url": url,
            "date": "Recent Official Record",
            "title": publisher_name,
            "content": extracted[:2500],
            "allowlist_passed": True,
        }
    except Exception as e:
        logger.warning("fetch_and_clean_page error for %s: %s", url, e)
        return None


async def retrieve_evidence(
    claim_text: str, detected_language: str = "en"
) -> List[Dict[str, Any]]:
    """
    Full Retrieval Pipeline for a Claim:
    1. Checks 24h cache.
    2. Queries Google Fact Check Tools API (primary).
    3. Runs Tavily (primary) or DuckDuckGo allowlist search (fallback).
    4. Fetches and cleans top pages via trafilatura — IN PARALLEL.
    5. Caches and returns allowlisted evidence passages.
    """
    cache_key = hashlib.sha256(claim_text.strip().lower().encode("utf-8")).hexdigest()
    cached = await get_cached_source(cache_key)
    if cached:
        valid = [c for c in cached if is_domain_allowlisted(c.get("url", ""))]
        if valid:
            return valid

    # Hint when no search provider is configured
    if not FACTCHECK_API_KEY and not TAVILY_API_KEY:
        logger.info(
            "No search provider configured (FACTCHECK_API_KEY and TAVILY_API_KEY both missing). "
            "Falling back to DuckDuckGo only. Add API keys to .env for better results."
        )

    evidence_list: List[Dict[str, Any]] = []

    # Step 3a: Google Fact Check Tools API
    factcheck_results = await query_google_fact_check(claim_text, detected_language)
    evidence_list.extend(factcheck_results)
    if factcheck_results:
        logger.info("Fact Check API returned %d results", len(factcheck_results))

    # Step 3b: Tavily (primary search)
    if TAVILY_API_KEY:
        tavily_results = await search_tavily(claim_text)
        evidence_list.extend(tavily_results)
        logger.info("Tavily returned %d results", len(tavily_results))

    # Step 3c: DuckDuckGo fallback if we still need more sources
    if len(evidence_list) < 3:
        search_urls = await search_allowlist_web(claim_text, max_results=6)
        # Deduplicate against already fetched URLs
        existing_urls = {e.get("url") for e in evidence_list}
        new_urls = [u for u in search_urls if u not in existing_urls]

        # FIX: Fetch pages in PARALLEL, not sequentially
        if new_urls:
            fetch_tasks = [fetch_and_clean_page(u) for u in new_urls]
            fetched_pages = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            for page in fetched_pages:
                if isinstance(page, Exception):
                    logger.warning("Page fetch error: %s", page)
                elif page is not None:
                    evidence_list.append(page)

    # Final allowlist filter
    valid_evidence = [e for e in evidence_list if is_domain_allowlisted(e.get("url", ""))]

    if not valid_evidence:
        logger.info(
            "retrieve_evidence: no allowlisted evidence found for claim: %s",
            claim_text[:80]
        )
    else:
        logger.info("retrieve_evidence: found %d valid sources", len(valid_evidence))

    # Cache for 24 hours
    if valid_evidence:
        try:
            await set_cached_sources(cache_key, valid_evidence)
        except Exception as cache_err:
            logger.warning("Cache write error: %s", cache_err)

    return valid_evidence
