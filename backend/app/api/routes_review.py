import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any

from ..schemas.review import (
    ReviewRequest, ReviewResponse, ReviewMode, ReviewVerdict, Finding,
)
from ..services.zip_service import validate_upload
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

    llm_rev = result.get("llm_review", {})

    return ReviewResponse(
        report_markdown=result.get("report", ""),
        total_score=result.get("score").total if result.get("score") else 0,
        verdict=result.get("verdict", ReviewVerdict.REJECT),
        project_profile=result.get("project_profile", {}),
        findings_count=findings_count,
        llm_review_enabled=llm_rev.get("llm_reviewer_enabled", False),
        llm_model_used=llm_rev.get("llm_model_used", ""),
        llm_profile_used=llm_rev.get("llm_profile_used", ""),
        llm_review_summary=llm_rev.get("mode_specific_assessment", ""),
    )
