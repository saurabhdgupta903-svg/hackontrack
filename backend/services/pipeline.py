"""
Pipeline Coordinator for Sach?
Coordinates: ingest → extract_claims → retrieve → judge → verify_citations → explain → summary.
Emits real-time SSE progress events during processing.

FIX: Claims processed concurrently (asyncio.gather + semaphore of 3) — no more serial slow path.
FIX: Claims capped at 5 to prevent runaway API costs.
FIX: Progress emitted after each claim completes.
FIX: compute_overall_summary: Verified + Cannot_be_confirmed mix → Partly supported (correct).
FIX: explain_claim failures caught per-claim and logged (not crash the whole pipeline).
FIX: Pipeline-level exceptions caught and emitted as SSE error events.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, List, Optional

from backend.schemas.fact_check import (
    IngestResult,
    ClaimResult,
    OverallSummary,
    FactCheckResponse,
    VERDICT_VERIFIED,
    VERDICT_FALSE,
    VERDICT_OUTDATED,
    VERDICT_PARTLY_SUPPORTED,
    VERDICT_CANNOT_BE_CONFIRMED,
)
from backend.services.claim_extractor import extract_claims
from backend.services.retriever import retrieve_evidence
from backend.services.judge import judge_claim
from backend.services.explainer import explain_claim
from backend.models.db import save_check

logger = logging.getLogger(__name__)

MAX_CLAIMS = 5          # cap to avoid runaway API usage
CONCURRENCY = 3         # max parallel claim-checks


def compute_overall_summary(claims: List[ClaimResult]) -> OverallSummary:
    total = len(claims)
    v_count = sum(1 for c in claims if c.verdict == VERDICT_VERIFIED)
    f_count = sum(1 for c in claims if c.verdict == VERDICT_FALSE)
    o_count = sum(1 for c in claims if c.verdict == VERDICT_OUTDATED)
    p_count = sum(1 for c in claims if c.verdict == VERDICT_PARTLY_SUPPORTED)
    u_count = sum(1 for c in claims if c.verdict == VERDICT_CANNOT_BE_CONFIRMED)

    # Dominant verdict logic
    # FIX: mix of Verified + Cannot_be_confirmed → Partly supported (not Partly supported only if p_count)
    if f_count > 0:
        dominant = VERDICT_FALSE
    elif o_count > 0:
        dominant = VERDICT_OUTDATED
    elif p_count > 0:
        dominant = VERDICT_PARTLY_SUPPORTED
    elif v_count > 0 and u_count == 0:
        dominant = VERDICT_VERIFIED
    elif u_count > 0 and v_count == 0:
        dominant = VERDICT_CANNOT_BE_CONFIRMED
    elif v_count > 0 and u_count > 0:
        # Mixed confirmed and unconfirmed → Partly supported
        dominant = VERDICT_PARTLY_SUPPORTED
    else:
        dominant = VERDICT_CANNOT_BE_CONFIRMED

    # Natural language breakdown
    parts = []
    if f_count:
        parts.append(f"{f_count} false")
    if p_count:
        parts.append(f"{p_count} partly supported")
    if o_count:
        parts.append(f"{o_count} outdated")
    if v_count:
        parts.append(f"{v_count} verified")
    if u_count:
        parts.append(f"{u_count} cannot be confirmed")

    breakdown = ", ".join(parts) if parts else "no checkable claims"
    summary_text = f"{total} claim{'s' if total != 1 else ''}: {breakdown}."

    return OverallSummary(
        total_claims=total,
        verified_count=v_count,
        false_count=f_count,
        outdated_count=o_count,
        partly_supported_count=p_count,
        cannot_be_confirmed_count=u_count,
        summary_text=summary_text,
        dominant_verdict=dominant,
    )


async def _process_claim(
    claim,
    detected_lang: str,
    target_language: str,
    semaphore: asyncio.Semaphore,
) -> ClaimResult:
    """Process a single claim: retrieve evidence → judge → explain. Thread-safe via semaphore."""
    async with semaphore:
        evidence = await retrieve_evidence(claim.claim_text, detected_lang)
        judgment = await judge_claim(claim, evidence)

        try:
            explanation_data = await explain_claim(
                claim=claim,
                judgment=judgment,
                target_language=target_language,
                detected_language=detected_lang,
            )
        except Exception as exp_err:
            logger.warning("explain_claim failed for '%s': %s", claim.claim_text[:60], exp_err)
            explanation_data = {
                "explanation": f"Verdict: {judgment.verdict}. {judgment.what_is_wrong_or_missing}",
                "explanation_en": f"Verdict: {judgment.verdict}. {judgment.what_is_wrong_or_missing}",
                "audio_base64": None,
                "audio_mime": None,
            }

        return ClaimResult(
            claim_id=claim.claim_id,
            claim_text=claim.claim_text,
            original_span=claim.original_span,
            verdict=judgment.verdict,
            confidence=judgment.confidence,
            what_is_right=judgment.what_is_right,
            what_is_wrong_or_missing=judgment.what_is_wrong_or_missing,
            evidence=judgment.evidence,
            as_of_date=judgment.as_of_date,
            date_changed=judgment.date_changed,
            explanation=explanation_data["explanation"],
            explanation_en=explanation_data.get("explanation_en"),
            audio_base64=explanation_data.get("audio_base64"),
            audio_mime=explanation_data.get("audio_mime"),
        )


async def run_pipeline_stream(
    ingest_result: IngestResult,
    target_language: str = "auto",
    ip_hash: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the pipeline and yields real-time SSE progress events.
    All exceptions are caught and converted to error events.
    """
    check_id = f"chk_{uuid.uuid4().hex[:12]}"

    try:
        # Event 1: Ingest
        yield {
            "stage": "ingest",
            "message": f"Processed {ingest_result.input_type} input ({len(ingest_result.raw_text)} chars)...",
            "progress": 15,
        }

        # Event 2: Extract claims
        yield {
            "stage": "extract_claims",
            "message": "Extracting atomic factual claims and dropping forward noise...",
            "progress": 30,
        }

        claims, detected_lang = await extract_claims(ingest_result.raw_text)

        if not claims:
            summary = OverallSummary(
                total_claims=0,
                verified_count=0,
                false_count=0,
                outdated_count=0,
                partly_supported_count=0,
                cannot_be_confirmed_count=0,
                summary_text="No testable factual claims detected in this message.",
                dominant_verdict=VERDICT_CANNOT_BE_CONFIRMED,
            )
            final_resp = FactCheckResponse(
                id=check_id,
                raw_input=ingest_result.raw_text,
                input_type=ingest_result.input_type,
                detected_language=detected_lang,
                target_language=target_language,
                claims=[],
                summary=summary,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            yield {
                "stage": "complete",
                "message": "Analysis finished: No checkable claims.",
                "progress": 100,
                "data": final_resp.model_dump(),
            }
            return

        # Cap claims to MAX_CLAIMS
        if len(claims) > MAX_CLAIMS:
            logger.info("Capping %d claims to %d", len(claims), MAX_CLAIMS)
            claims = claims[:MAX_CLAIMS]

        yield {
            "stage": "claims_extracted",
            "message": f"Found {len(claims)} checkable claim(s). Searching official sources...",
            "progress": 45,
            "claims_count": len(claims),
        }

        # Event 3+: Process claims concurrently
        semaphore = asyncio.Semaphore(CONCURRENCY)
        tasks = [
            asyncio.create_task(_process_claim(claim, detected_lang, target_language, semaphore))
            for claim in claims
        ]

        claim_results: List[ClaimResult] = []
        completed = 0
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                claim_results.append(result)
            except Exception as claim_err:
                logger.error("Claim processing error: %s", claim_err, exc_info=True)
                # Don't fail the whole check — add a Cannot_be_confirmed result
                from backend.schemas.fact_check import ClaimItem
                claim_results.append(
                    ClaimResult(
                        claim_id=f"err_{uuid.uuid4().hex[:8]}",
                        claim_text="[Claim processing failed]",
                        original_span="",
                        verdict=VERDICT_CANNOT_BE_CONFIRMED,
                        confidence=0.0,
                        what_is_right="",
                        what_is_wrong_or_missing=f"Processing error: {claim_err}",
                        evidence=[],
                        as_of_date="",
                        date_changed=None,
                        explanation=f"Could not check this claim: {claim_err}",
                        explanation_en=None,
                        audio_base64=None,
                        audio_mime=None,
                    )
                )

            completed += 1
            progress = 45 + int(45 * completed / len(claims))
            yield {
                "stage": "retrieval",
                "message": f"Checked {completed}/{len(claims)} claim(s)...",
                "progress": progress,
            }

        # Event: Summarize
        yield {
            "stage": "summarize",
            "message": "Synthesizing per-claim verdicts and final report...",
            "progress": 95,
        }

        overall_summary = compute_overall_summary(claim_results)

        final_response = FactCheckResponse(
            id=check_id,
            raw_input=ingest_result.raw_text,
            input_type=ingest_result.input_type,
            detected_language=detected_lang,
            target_language=target_language,
            claims=claim_results,
            summary=overall_summary,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save to history DB
        try:
            await save_check({**final_response.model_dump(), "ip_hash": ip_hash})
        except Exception as db_err:
            logger.error("Failed to save check to DB: %s", db_err)

        yield {
            "stage": "complete",
            "message": "Fact-check complete.",
            "progress": 100,
            "data": final_response.model_dump(),
        }

    except Exception as pipeline_err:
        logger.error("Pipeline fatal error: %s", pipeline_err, exc_info=True)
        yield {
            "stage": "error",
            "error": str(pipeline_err),
            "progress": 0,
        }


async def run_pipeline_sync(
    ingest_result: IngestResult,
    target_language: str = "auto",
    ip_hash: Optional[str] = None,
) -> FactCheckResponse:
    """Synchronous pipeline helper for testing and direct REST calls."""
    last_data = None
    async for event in run_pipeline_stream(ingest_result, target_language, ip_hash):
        if event.get("stage") == "complete" and "data" in event:
            last_data = event["data"]
        elif event.get("stage") == "error":
            raise RuntimeError(event.get("error", "Pipeline error"))
    if not last_data:
        raise RuntimeError("Pipeline failed to generate final response")
    return FactCheckResponse(**last_data)
