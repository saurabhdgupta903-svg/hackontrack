"""
Feedback Router: Allows users to report inaccurate verdicts or provide corrections
"""

import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

class FeedbackSubmission(BaseModel):
    check_id: str
    claim_id: str
    reported_verdict: str
    expected_verdict: str
    correction_url: str = Field(default="", description="Link to authoritative source backing correction")
    notes: str = Field(default="", description="User notes or explanation")

FEEDBACK_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "feedback.jsonl"

@router.post("")
async def submit_feedback(payload: FeedbackSubmission):
    record = {
        **payload.model_dump(),
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "status": "received",
        "message": "Thank you for helping improve Sach?. Fact-checkers will review your correction."
    }
