import logging
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any

from ..schemas.review import (
    ReviewRequest, ReviewResponse, ReviewMode, ReviewVerdict, Finding,
)
from ..services.zip_service import validate_upload
from ..services.redaction_service import redact_report_markdown
from ..core.config import settings
from ..graph.state import ReviewState
from ..graph.delivery_review_graph import review_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/review", response_model=ReviewResponse)
async def create_review(
    file: UploadFile = File(...),
    review_mode: str = Form(default="student_assignment"),
) -> Dict[str, Any]:
    validate_upload(file)

    try:
        mode = ReviewMode(review_mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的审查模式: {review_mode}，可选: {[m.value for m in ReviewMode]}",
        )

    request = ReviewRequest(review_mode=mode)
    request.zip_file = file

    initial_state: ReviewState = {
        "request": request,
        "zip_path": None,
        "extract_path": None,
        "project_root": None,
        "project_profile": {},
        "structure_findings": [],
        "security_findings": [],
        "dependency_findings": [],
        "readme_findings": [],
        "score": None,
        "verdict": None,
        "report": "",
        "llm_review": {},
        "llm_guard_findings": [],
        "errors": [],
    }

    try:
        result = await review_graph.ainvoke(initial_state)
    except Exception as e:
        logger.exception("审查流程执行失败")
        raise HTTPException(status_code=500, detail=f"审查流程执行失败: {str(e)}")

    findings_count = {
        "HIGH": sum(
            1 for f in (
                result.get("structure_findings", [])
                + result.get("security_findings", [])
                + result.get("dependency_findings", [])
                + result.get("readme_findings", [])
            )
            if f.severity == "HIGH"
        ),
        "MEDIUM": sum(
            1 for f in (
                result.get("structure_findings", [])
                + result.get("security_findings", [])
                + result.get("dependency_findings", [])
                + result.get("readme_findings", [])
            )
            if f.severity == "MEDIUM"
        ),
        "LOW": sum(
            1 for f in (
                result.get("structure_findings", [])
                + result.get("security_findings", [])
                + result.get("dependency_findings", [])
                + result.get("readme_findings", [])
            )
            if f.severity == "LOW"
        ),
    }

    report_md = result.get("report", "")
    report_md = redact_report_markdown(report_md)

    if settings.HISTORY_ENABLED and settings.HISTORY_AUTO_SAVE:
        try:
            from ..history.summary_builder import build_summary
            from ..history.store import save_record
            record = build_summary(result)
            save_record(record)
        except Exception:
            pass

    if settings.KNOWLEDGE_ENABLED and settings.KNOWLEDGE_AUTO_INDEX:
        try:
            from ..knowledge.index_service import rebuild_index
            rebuild_index()
        except Exception:
            pass

    llm_rev = result.get("llm_review", {})
    llm_guard = result.get("llm_guard_findings", [])

    verdict_val = result.get("verdict", ReviewVerdict.REJECT)

    if settings.METRICS_ENABLED:
        try:
            from app.observability.metrics import observe_review, observe_llm_review

            mode_name = request.review_mode.value if hasattr(request.review_mode, "value") else str(request.review_mode)
            duration = time.time() - getattr(request, "_start_time", time.time())
            observe_review(
                mode=mode_name,
                verdict=verdict_val.value if hasattr(verdict_val, "value") else str(verdict_val),
                duration=duration,
                findings=findings_count,
            )
            llm_status = "enabled" if llm_rev.get("llm_reviewer_enabled") else "disabled"
            observe_llm_review(status=llm_status)
        except Exception:
            pass

    return ReviewResponse(
        report_markdown=report_md,
        total_score=result.get("score").total if result.get("score") else 0,
        verdict=verdict_val,
        project_profile=result.get("project_profile", {}),
        findings_count=findings_count,
        llm_review_enabled=llm_rev.get("llm_reviewer_enabled", False),
        llm_model_used=llm_rev.get("llm_model_used", ""),
        llm_profile_used=llm_rev.get("llm_profile_used", ""),
        llm_review_summary=llm_rev.get("mode_specific_assessment", ""),
        llm_guard_status=llm_rev.get("llm_guard_status", "not_scanned" if not settings.LLM_GUARD_ENABLED else "passed"),
        llm_guard_findings=llm_guard,
        llm_review_skipped_reason=llm_rev.get("llm_error", ""),
    )
