import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class KnowledgeDocument:
    report_id: str
    project_alias: str
    project_fingerprint: str
    review_mode: str
    verdict: str
    score: int
    project_type: str
    detected_languages: List[str]
    findings_summary: Dict[str, int]
    top_security_findings: List[str]
    top_structure_findings: List[str]
    top_dependency_findings: List[str]
    top_readme_findings: List[str]
    commercial_fix_plan: str
    interview_notes: str
    created_at: str
    content_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    report_id: str
    score: float
    verdict: str
    review_mode: str
    matched_summary: str
    reason: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdviseResult:
    next_fix_plan: str = ""
    common_risks: List[str] = field(default_factory=list)
    interview_talking_points: List[str] = field(default_factory=list)
    source_report_ids: List[str] = field(default_factory=list)
    total_reports_analyzed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
