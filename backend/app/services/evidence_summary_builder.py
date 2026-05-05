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
        "top_security_findings": [
            {
                "severity": f.severity,
                "message": f.message,
                "file": f.file_path or "",
            }
            for f in _cap_findings(security_findings, 5)
        ],
        "security_severity_summary": {
            "HIGH": sum(1 for f in security_findings if f.severity == "HIGH"),
            "MEDIUM": sum(1 for f in security_findings if f.severity == "MEDIUM"),
            "LOW": sum(1 for f in security_findings if f.severity == "LOW"),
        },
        "dependency_findings_summary": [
            {
                "severity": f.severity,
                "message": f.message,
            }
            for f in _cap_findings(dependency_findings, 3)
        ],
        "readme_findings_summary": [
            {
                "severity": f.severity,
                "message": f.message,
            }
            for f in _cap_findings(readme_findings, 3)
        ],
        "structure_findings_summary": [
            {
                "severity": f.severity,
                "message": f.message,
            }
            for f in _cap_findings(structure_findings, 3)
        ],
    }
    return summary


def _cap_findings(findings: List[Finding], max_count: int) -> List[Finding]:
    if len(findings) <= max_count:
        return findings
    high = [f for f in findings if f.severity == "HIGH"]
    med = [f for f in findings if f.severity == "MEDIUM"]
    low = [f for f in findings if f.severity == "LOW"]
    capped = (high + med + low)[:max_count]
    return capped
