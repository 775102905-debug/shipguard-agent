import hashlib
from typing import List, Dict, Any, Optional

from ..services.redaction_service import redact
from ..schemas.review import ReviewVerdict
from .models import HistoryRecord


def build_summary(
    review_result: Dict[str, Any],
    project_alias: str = "",
) -> HistoryRecord:
    score = review_result.get("score")
    verdict = review_result.get("verdict")
    profile = review_result.get("project_profile", {})
    req = review_result.get("request")

    all_findings = (
        review_result.get("structure_findings", [])
        + review_result.get("security_findings", [])
        + review_result.get("dependency_findings", [])
        + review_result.get("readme_findings", [])
    )

    findings_count = {
        "HIGH": sum(1 for f in all_findings if f.severity == "HIGH"),
        "MEDIUM": sum(1 for f in all_findings if f.severity == "MEDIUM"),
        "LOW": sum(1 for f in all_findings if f.severity == "LOW"),
    }

    top_security = [
        redact(f.message)
        for f in review_result.get("security_findings", [])
        if f.severity in ("HIGH", "MEDIUM")
    ][:5]

    top_structure = [
        redact(f.message)
        for f in review_result.get("structure_findings", [])
        if f.severity in ("HIGH", "MEDIUM")
    ][:3]

    top_dep = [
        redact(f.message)
        for f in review_result.get("dependency_findings", [])
        if f.severity in ("HIGH", "MEDIUM")
    ][:3]

    top_readme = [
        redact(f.message)
        for f in review_result.get("readme_findings", [])
        if f.severity in ("HIGH", "MEDIUM")
    ][:3]

    dim_scores = {}
    if score:
        dim_scores = {
            "delivery_completeness": score.delivery_completeness,
            "security_risk": score.security_risk,
            "dependency_config": score.dependency_config,
            "readme_quality": score.readme_quality,
            "docker_deploy": score.docker_deploy,
            "structure_maintainability": score.structure_maintainability,
        }

    fp_parts = [
        profile.get("project_type", ""),
        str(profile.get("detected_languages", [])),
        str(score.total if score else 0),
        str(verdict.value if verdict else ""),
    ]
    fp_raw = "|".join(fp_parts)
    fingerprint = hashlib.md5(fp_raw.encode()).hexdigest()[:16]

    review_mode_str = req.review_mode.value if req and hasattr(req, "review_mode") else ""

    fix_plan_lines = _generate_fix_plan(all_findings)

    record = HistoryRecord(
        project_alias=redact(project_alias or profile.get("project_type", "unknown")),
        project_fingerprint=fingerprint,
        review_mode=review_mode_str,
        verdict=verdict.value if verdict else "UNKNOWN",
        score=score.total if score else 0,
        dimension_scores=dim_scores,
        findings_summary=findings_count,
        top_security_findings=top_security,
        top_structure_findings=top_structure,
        top_dependency_findings=top_dep,
        top_readme_findings=top_readme,
        commercial_fix_plan=redact("\n".join(fix_plan_lines)),
        project_type=profile.get("project_type", ""),
        detected_languages=profile.get("detected_languages", []),
        redaction_version="v1",
    )
    return record


def _generate_fix_plan(findings: List[Any]) -> List[str]:
    high = [f for f in findings if f.severity == "HIGH"]
    med = [f for f in findings if f.severity == "MEDIUM"]
    lines = []
    if high:
        lines.append(f"## 高危问题 ({len(high)}) — 优先修复")
        for f in high:
            rec = f.recommendation or "无建议"
            lines.append(f"- {redact(f.message)}")
            lines.append(f"  修复: {rec}")
    if med:
        lines.append(f"\n## 中危问题 ({len(med)})")
        for f in med[:5]:
            rec = f.recommendation or "无建议"
            lines.append(f"- {redact(f.message)}")
            lines.append(f"  修复: {rec}")
    if not lines:
        lines.append("未发现需要修复的问题")
    return lines



