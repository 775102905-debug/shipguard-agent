import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..core.config import settings
from ..history.store import list_reports, get_report
from ..services.redaction_service import redact
from .models import KnowledgeDocument
from .safety import assert_safe_for_index

logger = logging.getLogger(__name__)

_index: Dict[str, KnowledgeDocument] = {}
_index_built: bool = False


def is_index_built() -> bool:
    return _index_built


def get_index_size() -> int:
    return len(_index)


def get_index_path() -> Path:
    return settings.ROOT_DIR / settings.KNOWLEDGE_INDEX_PATH


def rebuild_index() -> int:
    global _index, _index_built

    if not settings.HISTORY_ENABLED:
        logger.warning("HISTORY_ENABLED=false, cannot rebuild knowledge index")
        _index = {}
        _index_built = False
        return 0

    all_reports = list_reports(limit=1000, offset=0)
    indexed = 0

    new_index: Dict[str, KnowledgeDocument] = {}
    for r in all_reports:
        rid = r.get("report_id", "")
        if not rid:
            continue

        detail = get_report(rid)
        if not detail:
            continue

        detail["report_id"] = rid

        if not assert_safe_for_index(detail, source=rid):
            logger.warning(f"Skipping {rid}: safety check failed")
            continue

        doc = _build_document(detail)
        new_index[rid] = doc
        indexed += 1

    _index = new_index
    _index_built = True
    logger.info(f"Knowledge index rebuilt: {indexed} documents")
    return indexed


def get_all_documents() -> List[KnowledgeDocument]:
    return list(_index.values())


def get_document(report_id: str) -> Optional[KnowledgeDocument]:
    return _index.get(report_id)


def _build_document(detail: Dict[str, Any]) -> KnowledgeDocument:
    findings_summary = detail.get("findings_summary", {})
    top_sec = detail.get("top_security_findings", [])
    top_struct = detail.get("top_structure_findings", [])
    top_dep = detail.get("top_dependency_findings", [])
    top_readme = detail.get("top_readme_findings", [])

    if isinstance(findings_summary, str):
        try:
            findings_summary = json.loads(findings_summary)
        except (json.JSONDecodeError, TypeError):
            findings_summary = {}

    for lst in [top_sec, top_struct, top_dep, top_readme]:
        if isinstance(lst, str):
            try:
                lst = json.loads(lst)
            except (json.JSONDecodeError, TypeError):
                lst = []

    content_parts = []
    if top_sec:
        content_parts.append("安全发现: " + "; ".join(top_sec))
    if top_struct:
        content_parts.append("结构: " + "; ".join(top_struct))
    if top_dep:
        content_parts.append("依赖: " + "; ".join(top_dep))
    if top_readme:
        content_parts.append("README: " + "; ".join(top_readme))

    fix = detail.get("commercial_fix_plan", "")
    if isinstance(fix, str) and fix:
        content_parts.append("修复建议: " + fix[:200])

    return KnowledgeDocument(
        report_id=detail.get("report_id", ""),
        project_alias=detail.get("project_alias", ""),
        project_fingerprint=detail.get("project_fingerprint", ""),
        review_mode=detail.get("review_mode", ""),
        verdict=detail.get("verdict", ""),
        score=detail.get("score", 0),
        project_type=detail.get("project_type", ""),
        detected_languages=detail.get("detected_languages", []),
        findings_summary=findings_summary,
        top_security_findings=top_sec,
        top_structure_findings=top_struct,
        top_dependency_findings=top_dep,
        top_readme_findings=top_readme,
        commercial_fix_plan=detail.get("commercial_fix_plan", ""),
        interview_notes=detail.get("interview_notes", ""),
        created_at=detail.get("created_at", ""),
        content_text=redact(" ".join(content_parts)),
    )
