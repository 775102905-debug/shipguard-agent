from enum import Enum
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from pydantic import BaseModel, Field


class ReviewMode(str, Enum):
    student_assignment = "student_assignment"
    github_showcase = "github_showcase"
    interview_project = "interview_project"
    commercial_delivery = "commercial_delivery"


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    REJECT = "REJECT"


class Finding(BaseModel):
    severity: str
    category: str
    message: str
    file_path: Optional[str] = None
    recommendation: Optional[str] = None


class ReviewScore(BaseModel):
    delivery_completeness: int = 0
    security_risk: int = 0
    dependency_config: int = 0
    readme_quality: int = 0
    docker_deploy: int = 0
    structure_maintainability: int = 0
    total: int = 0


class ReviewRequest(BaseModel):
    review_mode: ReviewMode = ReviewMode.student_assignment
    zip_file: Any = None

    class Config:
        arbitrary_types_allowed = True


class ReviewResponse(BaseModel):
    report_markdown: str
    total_score: int
    verdict: ReviewVerdict
    project_profile: Dict[str, Any]
    findings_count: Dict[str, int]
    llm_review_enabled: bool = False
    llm_model_used: str = ""
    llm_profile_used: str = ""
    llm_review_summary: str = ""
