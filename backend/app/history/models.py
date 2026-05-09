import uuid
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class HistoryRecord:
    report_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_alias: str = ""
    project_fingerprint: str = ""
    review_mode: str = ""
    verdict: str = ""
    score: int = 0
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    findings_summary: Dict[str, int] = field(default_factory=lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0})
    top_security_findings: List[str] = field(default_factory=list)
    top_structure_findings: List[str] = field(default_factory=list)
    top_dependency_findings: List[str] = field(default_factory=list)
    top_readme_findings: List[str] = field(default_factory=list)
    commercial_fix_plan: str = ""
    interview_notes: str = ""
    project_type: str = ""
    detected_languages: List[str] = field(default_factory=list)
    redaction_version: str = "v1"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HistoryRecord":
        return cls(
            report_id=d.get("report_id", uuid.uuid4().hex[:12]),
            project_alias=d.get("project_alias", ""),
            project_fingerprint=d.get("project_fingerprint", ""),
            review_mode=d.get("review_mode", ""),
            verdict=d.get("verdict", ""),
            score=d.get("score", 0),
            dimension_scores=d.get("dimension_scores", {}),
            findings_summary=d.get("findings_summary", {"HIGH": 0, "MEDIUM": 0, "LOW": 0}),
            top_security_findings=d.get("top_security_findings", []),
            top_structure_findings=d.get("top_structure_findings", []),
            top_dependency_findings=d.get("top_dependency_findings", []),
            top_readme_findings=d.get("top_readme_findings", []),
            commercial_fix_plan=d.get("commercial_fix_plan", ""),
            interview_notes=d.get("interview_notes", ""),
            project_type=d.get("project_type", ""),
            detected_languages=d.get("detected_languages", []),
            redaction_version=d.get("redaction_version", "v1"),
            created_at=d.get("created_at", datetime.utcnow().isoformat()),
        )


@dataclass
class CompareResult:
    previous_report_id: str = ""
    current_report_id: str = ""
    previous_score: int = 0
    current_score: int = 0
    score_delta: int = 0
    previous_verdict: str = ""
    current_verdict: str = ""
    fixed_findings: List[str] = field(default_factory=list)
    new_findings: List[str] = field(default_factory=list)
    persistent_findings: List[str] = field(default_factory=list)
    improved_dimensions: Dict[str, int] = field(default_factory=dict)
    regressed_dimensions: Dict[str, int] = field(default_factory=dict)
    mode_changed: bool = False
    next_fix_plan: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
