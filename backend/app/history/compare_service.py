import json
from typing import List, Dict, Any, Optional

from ..services.redaction_service import redact
from .models import CompareResult
from .store import get_report


def compare_reports(report_id_a: str, report_id_b: str) -> Optional[CompareResult]:
    a = get_report(report_id_a)
    b = get_report(report_id_b)

    if not a:
        raise ValueError(f"报告不存在: {report_id_a}")
    if not b:
        raise ValueError(f"报告不存在: {report_id_b}")

    a_findings = _collect_findings(a)
    b_findings = _collect_findings(b)

    a_set = set(a_findings)
    b_set = set(b_findings)

    fixed = list(a_set - b_set)
    new = list(b_set - a_set)
    persistent = list(a_set & b_set)

    a_score = a.get("score", 0)
    b_score = b.get("score", 0)
    delta = b_score - a_score

    a_dims = a.get("dimension_scores", {})
    b_dims = b.get("dimension_scores", {})

    improved = {}
    regressed = {}
    all_keys = set(list(a_dims.keys()) + list(b_dims.keys()))
    for key in all_keys:
        av = a_dims.get(key, 0)
        bv = b_dims.get(key, 0)
        diff = bv - av
        if diff > 0:
            improved[key] = diff
        elif diff < 0:
            regressed[key] = abs(diff)

    mode_a = a.get("review_mode", "")
    mode_b = b.get("review_mode", "")
    mode_changed = mode_a != mode_b

    next_fix_plan_lines = _build_next_fix_plan(b_findings, fixed, persistent)

    return CompareResult(
        previous_report_id=report_id_a,
        current_report_id=report_id_b,
        previous_score=a_score,
        current_score=b_score,
        score_delta=delta,
        previous_verdict=a.get("verdict", ""),
        current_verdict=b.get("verdict", ""),
        fixed_findings=[redact(f) for f in fixed],
        new_findings=[redact(f) for f in new],
        persistent_findings=[redact(f) for f in persistent],
        improved_dimensions=improved,
        regressed_dimensions=regressed,
        mode_changed=mode_changed,
        next_fix_plan=redact("\n".join(next_fix_plan_lines)),
    )


def _collect_findings(record: Dict[str, Any]) -> List[str]:
    items = []
    for field in ["top_security_findings", "top_structure_findings",
                   "top_dependency_findings", "top_readme_findings"]:
        val = record.get(field, [])
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                val = []
        if isinstance(val, list):
            items.extend(val)
    return items


def _build_next_fix_plan(
    current_findings: List[str],
    fixed: List[str],
    persistent: List[str],
) -> List[str]:
    lines = []
    if persistent:
        lines.append(f"## 仍未解决的问题 ({len(persistent)})")
        for f in persistent:
            lines.append(f"- {redact(f)}")
    if fixed:
        lines.append(f"\n## 已修复的问题 ({len(fixed)})")
        for f in fixed:
            lines.append(f"- {redact(f)}")
    if not lines:
        lines.append("未发现需要修复的问题")
    return lines
