"""
Step 3 of Pipeline: Retrieval of Authoritative Evidence
Includes:
- Google Fact Check Tools API query
- Allowlist-restricted web search (Tavily or live DuckDuckGo)
- Page fetching and text cleaning via trafilatura
- 24-hour persistent database caching
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import httpx
import trafilatura

from backend.config import (
    ALLOWLISTED_DOMAINS,
    is_domain_allowlisted,
    FACTCHECK_API_KEY,
    TAVILY_API_KEY,
)
from backend.models.db import get_cached_source, set_cached_sources

async def query_google_fact_check(query: str) -> List[Dict[str, Any]]:
    """
    Queries Google Fact Check Tools API (claims:search).
    Returns list of verified reviews from certified fact checkers.
    """
    if not FACTCHECK_API_KEY:
        return []

    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {
        "query": query,
        "key": FACTCHECK_API_KEY,
        "pageSize": 5
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

                        # Check allowlist
                        if review_url and is_domain_allowlisted(review_url):
                            results.append({
                                "source_name": publisher,
                                "url": review_url,
                                "date": date,
                                "title": title,
                                "content": f"Fact Check Verdict: {rating}. Review: {title}",
                                "allowlist_passed": True
                            })
    except Exception:
        pass

    return results

async def search_tavily(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Queries Tavily Search API restricted strictly to allowlisted domains.
    """
    if not TAVILY_API_KEY:
        return []

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_domains": ALLOWLISTED_DOMAINS,
        "max_results": max_results
    }

    results = []
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                for r in data.get("results", []):
                    r_url = r.get("url", "")
                    if is_domain_allowlisted(r_url):
                        results.append({
                            "source_name": urlparse(r_url).netloc,
                            "url": r_url,
                            "date": "Recent",
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "allowlist_passed": True
                        })
    except Exception:
        pass
    return results

async def search_allowlist_web(query: str, max_results: int = 6) -> List[str]:
    """
    Direct live web search querying allowlisted domains.
    Extracts URLs and verifies that each belongs to the domain allowlist.
    """
    # Create targeted queries that emphasize our primary authorities
    domains_focus = "site:pib.gov.in OR site:rbi.org.in OR site:boomlive.in OR site:altnews.in OR site:factly.in OR site:newschecker.in"
    search_q = f"({domains_focus}) {query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    candidate_urls = []
    try:
        from urllib.parse import quote
        ddg_url = f"https://html.duckduckgo.com/html/?q={quote(search_q)}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(ddg_url, headers=headers)
            if resp.status_code == 200:
                html = resp.text
                for m in re.finditer(r'href="([^"]*uddg=[^"]*)"', html):
                    uddg = m.group(1)
                    parsed = parse_qs(urlparse(uddg).query)
                    if "uddg" in parsed:
                        raw_u = parsed["uddg"][0]
                        if is_domain_allowlisted(raw_u) and raw_u not in candidate_urls:
                            candidate_urls.append(raw_u)
                            if len(candidate_urls) >= max_results:
                                break
    except Exception:
        pass

    # If domain-specific query yielded few results, also run standard query and filter candidates
    if len(candidate_urls) < 3:
        try:
            from urllib.parse import quote
            ddg_url_broad = f"https://html.duckduckgo.com/html/?q={quote(query + ' fact check')}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(ddg_url_broad, headers=headers)
                if resp.status_code == 200:
                    html = resp.text
                    for m in re.finditer(r'href="([^"]*uddg=[^"]*)"', html):
                        uddg = m.group(1)
                        parsed = parse_qs(urlparse(uddg).query)
                        if "uddg" in parsed:
                            raw_u = parsed["uddg"][0]
                            if is_domain_allowlisted(raw_u) and raw_u not in candidate_urls:
                                candidate_urls.append(raw_u)
                                if len(candidate_urls) >= max_results:
                                    break
        except Exception:
            pass

    return candidate_urls

async def fetch_and_clean_page(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches an allowlisted URL and extracts readable body text using trafilatura.
    """
    if not is_domain_allowlisted(url):
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            html = resp.text

        extracted = trafilatura.extract(html, include_comments=False, favor_precision=True)
        if not extracted or len(extracted) < 50:
            extracted = trafilatura.extract(html, favor_precision=False)

        if not extracted:
            return None

        # Clean publisher name from netloc
        domain = urlparse(url).netloc.replace("www.", "")
        publisher_name = domain.split(".")[0].upper()
        if "pib.gov.in" in domain:
            publisher_name = "PIB (Press Information Bureau)"
        elif "rbi.org.in" in domain:
            publisher_name = "Reserve Bank of India (RBI)"
        elif "boomlive" in domain:
            publisher_name = "BOOM Live"
        elif "altnews" in domain:
            publisher_name = "Alt News"
        elif "factly" in domain:
            publisher_name = "Factly"
        elif "newschecker" in domain:
            publisher_name = "Newschecker"
        elif "who.int" in domain:
            publisher_name = "World Health Organization (WHO)"

        return {
            "source_name": publisher_name,
            "url": url,
            "date": "Recent Official Record",
            "title": publisher_name,
            "content": extracted[:2500], # Keep top 2500 chars of authoritative page
            "allowlist_passed": True
        }
    except Exception:
        return None

async def retrieve_evidence(claim_text: str, detected_language: str = "English") -> List[Dict[str, Any]]:
    """
    Full Retrieval Pipeline for a Claim:
    1. Checks 24h cache.
    2. Queries Google Fact Check Tools API.
    3. Runs Tavily or Allowlist web searches.
    4. Fetches and cleans top pages via trafilatura.
    5. Caches and returns list of allowlisted evidence passages.
    """
    cache_key = hashlib.sha256(claim_text.strip().lower().encode("utf-8")).hexdigest()
    cached = await get_cached_source(cache_key)
    if cached:
        return [c for c in cached if is_domain_allowlisted(c.get("url", ""))]

    evidence_list: List[Dict[str, Any]] = []

    # Step 3a: Google Fact Check Tools API
    factcheck_results = await query_google_fact_check(claim_text)
    evidence_list.extend(factcheck_results)

    # Step 3b: Tavily search if configured
    if TAVILY_API_KEY:
        tavily_results = await search_tavily(claim_text)
        evidence_list.extend(tavily_results)

    # Step 3c: Allowlist web search if we need more sources
    if len(evidence_list) < 3:
        search_urls = await search_allowlist_web(claim_text, max_results=5)
        for u in search_urls:
            # Avoid duplicate URLs
            if any(e.get("url") == u for e in evidence_list):
                continue
            cleaned_page = await fetch_and_clean_page(u)
            if cleaned_page:
                evidence_list.append(cleaned_page)

    # Filter out anything not clearing the allowlist
    valid_evidence = [e for e in evidence_list if is_domain_allowlisted(e.get("url", ""))]

    # Save to 24-hour cache if we found evidence
    if valid_evidence:
        await set_cached_sources(cache_key, valid_evidence)

    return valid_evidence
