from typing import TypedDict, List, Optional, Annotated, Dict, Any
from pathlib import Path

from ..schemas.review import (
    ReviewRequest, ReviewMode, ReviewVerdict,
    Finding, ReviewScore,
)


class ReviewState(TypedDict):
    request: ReviewRequest
    zip_path: Optional[Path]
    extract_path: Optional[Path]
    project_root: Optional[Path]
    project_profile: Dict[str, Any]
    structure_findings: List[Finding]
    security_findings: List[Finding]
    dependency_findings: List[Finding]
    readme_findings: List[Finding]
    score: Optional[ReviewScore]
    verdict: Optional[ReviewVerdict]
    report: str
    llm_review: Dict[str, Any]
    llm_guard_findings: List[Dict[str, Any]]
    errors: List[str]
