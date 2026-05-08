from typing import List, Dict, Any

from ..schemas.review import Finding


def build_evidence_summary(
    profile: Dict[str, Any],
    structure_findings: List[Finding],
    security_findings: List[Finding],
    dependency_findings: List[Finding],
    readme_findings: List[Finding],
    total_score: int,
    verdict: str,
) -> Dict[str, Any]:
    key_files = profile.get("key_files", {})

    security_high, security_med, security_low = _sort_findings(security_findings)
    dep_high, dep_med, dep_low = _sort_findings(dependency_findings)
    readme_high, readme_med, readme_low = _sort_findings(readme_findings)
    struct_high, struct_med, struct_low = _sort_findings(structure_findings)

    top_security = _capped_with_flag(security_high, security_med, security_low, 5)
    dep_summary = _capped_with_flag(dep_high, dep_med, dep_low, 3)
    readme_summary = _capped_with_flag(readme_high, readme_med, readme_low, 3)
    struct_summary = _capped_with_flag(struct_high, struct_med, struct_low, 3)

    truncated_flags = {}
    if top_security["truncated"]:
        truncated_flags["security"] = True
    if dep_summary["truncated"]:
        truncated_flags["dependency"] = True
    if readme_summary["truncated"]:
        truncated_flags["readme"] = True
    if struct_summary["truncated"]:
        truncated_flags["structure"] = True

    summary = {
        "project_type": profile.get("project_type", "unknown"),
        "detected_languages": profile.get("detected_languages", []),
        "detected_frameworks": profile.get("detected_frameworks", []),
        "has_backend": profile.get("has_backend", False),
        "has_frontend": profile.get("has_frontend", False),
        "total_score": total_score,
        "verdict": verdict,
        "missing_critical_files": [
            name for name, present in key_files.items()
            if not present
        ],
        "top_security_findings": top_security["items"],
        "security_severity_summary": {
            "HIGH": len(security_high),
            "MEDIUM": len(security_med),
            "LOW": len(security_low),
        },
        "dependency_findings_summary": dep_summary["items"],
        "readme_findings_summary": readme_summary["items"],
        "structure_findings_summary": struct_summary["items"],
        "truncated": truncated_flags if truncated_flags else None,
    }
    return summary


def _sort_findings(findings: List[Finding]) -> tuple:
    high = sorted(
        [f for f in findings if f.severity == "HIGH"],
        key=lambda x: x.message or "",
    )
    med = sorted(
        [f for f in findings if f.severity == "MEDIUM"],
        key=lambda x: x.message or "",
    )
    low = sorted(
        [f for f in findings if f.severity == "LOW"],
        key=lambda x: x.message or "",
    )
    return high, med, low


def _capped_with_flag(
    high: List[Finding],
    med: List[Finding],
    low: List[Finding],
    max_count: int,
) -> Dict[str, Any]:
    total = len(high) + len(med) + len(low)
    capped = (high + med + low)[:max_count]
    items = [
        {"severity": f.severity, "message": f.message, "file": getattr(f, "file_path", "") or ""}
        for f in capped
    ]
    return {"items": items, "truncated": total > max_count}
