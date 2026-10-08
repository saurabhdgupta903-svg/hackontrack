"""
History Router: Fetch previous checks and delete check data per user request
"""

from fastapi import APIRouter, HTTPException
from backend.models.db import get_check_history, get_check_by_id, delete_check

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("")
async def list_history():
    return await get_check_history(limit=50)

@router.get("/{check_id}")
async def get_single_check(check_id: str):
    record = await get_check_by_id(check_id)
    if not record:
        raise HTTPException(status_code=404, detail="Fact check not found.")
    return record

@router.delete("/{check_id}")
async def remove_check(check_id: str):
    deleted = await delete_check(check_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Fact check not found or already deleted.")
    return {"status": "success", "message": "Check permanently deleted."}
