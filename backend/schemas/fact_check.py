"""
Pydantic Schemas for Sach? Fact-Checking Pipeline
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from backend.config import (
    VERDICT_VERIFIED,
    VERDICT_FALSE,
    VERDICT_OUTDATED,
    VERDICT_PARTLY_SUPPORTED,
    VERDICT_CANNOT_BE_CONFIRMED,
    ALLOWED_VERDICTS
)

VerdictType = Literal[
    "Verified",
    "False",
    "Outdated",
    "Partly supported",
    "Cannot be confirmed"
]

class EvidenceItem(BaseModel):
    source_name: str = Field(description="Name of publisher or authoritative authority")
    url: str = Field(description="Direct URL to official announcement or fact-check")
    date: Optional[str] = Field(default="Recent", description="Publication date or date of record")
    quote_or_passage: str = Field(description="Exact excerpt from the source text")
    stance: Literal["supports", "contradicts", "neutral"] = "neutral"
    is_verified_citation: bool = Field(default=False, description="Whether URL and quote were verified against fetched text")
    allowlist_passed: bool = Field(default=False, description="Whether domain is on the strict allowlist")

class ClaimItem(BaseModel):
    claim_id: str
    claim_text: str
    original_span: str
    category: Optional[str] = "general"

class ClaimJudgment(BaseModel):
    verdict: VerdictType
    confidence: float = Field(ge=0.0, le=1.0)
    what_is_right: str
    what_is_wrong_or_missing: str
    evidence: List[EvidenceItem] = []
    as_of_date: str = "October 2026"
    date_changed: Optional[str] = None

class ClaimResult(BaseModel):
    claim_id: str
    claim_text: str
    original_span: str
    verdict: VerdictType
    confidence: float
    what_is_right: str
    what_is_wrong_or_missing: str
    evidence: List[EvidenceItem]
    as_of_date: str
    date_changed: Optional[str] = None
    explanation: str
    explanation_en: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime: Optional[str] = None

class OverallSummary(BaseModel):
    total_claims: int
    verified_count: int
    false_count: int
    outdated_count: int
    partly_supported_count: int
    cannot_be_confirmed_count: int
    summary_text: str
    dominant_verdict: VerdictType

class FactCheckResponse(BaseModel):
    id: str
    raw_input: str
    input_type: Literal["text", "image", "voice", "pdf", "url"]
    detected_language: str
    target_language: str
    claims: List[ClaimResult]
    summary: OverallSummary
    created_at: str
    status: str = "completed"
    error: Optional[str] = None

class IngestResult(BaseModel):
    raw_text: str
    input_type: Literal["text", "image", "voice", "pdf", "url"]
    detected_language: str
    metadata: Dict[str, Any] = {}

class CheckRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    target_language: str = "auto"
