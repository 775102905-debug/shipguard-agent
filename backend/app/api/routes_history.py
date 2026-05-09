import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List

from ..core.config import settings
from ..history.store import save_record, list_reports, get_report, get_total_count
from ..history.summary_builder import build_summary
from ..history.compare_service import compare_reports
from ..history.models import HistoryRecord
from ..services.redaction_service import redact

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/save")
async def api_save(review_result: Dict[str, Any], project_alias: str = "") -> Dict[str, Any]:
    if not settings.HISTORY_ENABLED:
        return {"saved": False, "reason": "HISTORY_ENABLED=false"}
    if not settings.HISTORY_AUTO_SAVE:
        return {"saved": False, "reason": "HISTORY_AUTO_SAVE=false, use POST /api/history/save explicitly"}
    record = build_summary(review_result, project_alias=project_alias)
    rid = save_record(record)
    if not rid:
        return {"saved": False, "reason": "save failed (non-blocking)"}
    return {"saved": True, "report_id": rid}


@router.post("/save-explicit")
async def api_save_explicit(review_result: Dict[str, Any], project_alias: str = "") -> Dict[str, Any]:
    if not settings.HISTORY_ENABLED:
        return {"saved": False, "reason": "HISTORY_ENABLED=false"}
    record = build_summary(review_result, project_alias=project_alias)
    rid = save_record(record)
    if not rid:
        return {"saved": False, "reason": "save failed (non-blocking)"}
    return {"saved": True, "report_id": rid}


@router.get("/reports")
async def api_list_reports(limit: int = Query(default=20, le=100), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    if not settings.HISTORY_ENABLED:
        return {"enabled": False, "reports": [], "total": 0}
    reports = list_reports(limit=limit, offset=offset)
    total = get_total_count()
    return {"enabled": True, "total": total, "reports": reports}


@router.get("/reports/{report_id}")
async def api_get_report(report_id: str) -> Dict[str, Any]:
    if not settings.HISTORY_ENABLED:
        raise HTTPException(status_code=403, detail="History store is disabled")
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
    report["report_id"] = report_id
    return report


@router.post("/compare")
async def api_compare(payload: Dict[str, str]) -> Dict[str, Any]:
    if not settings.HISTORY_ENABLED:
        raise HTTPException(status_code=403, detail="History store is disabled")
    report_id_a = payload.get("report_id_a", "")
    report_id_b = payload.get("report_id_b", "")
    if not report_id_a or not report_id_b:
        raise HTTPException(status_code=400, detail="需要提供 report_id_a 和 report_id_b")
    try:
        result = compare_reports(report_id_a, report_id_b)
        return result.to_dict() if result else {"error": "compare failed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
