import difflib
import logging
from typing import List, Dict, Any, Optional

from ..core.config import settings
from ..services.redaction_service import redact
from .models import KnowledgeDocument, SearchResult, AdviseResult
from .index_service import get_all_documents, is_index_built, get_document

logger = logging.getLogger(__name__)


def search_similar_reports(
    query_text: str,
    max_results: int = 5,
    review_mode: Optional[str] = None,
    min_score: int = 0,
) -> List[SearchResult]:
    if not is_index_built():
        return []

    docs = get_all_documents()
    if max_results <= 0:
        max_results = settings.KNOWLEDGE_MAX_RESULTS

    scored: List[tuple] = []
    query_lower = query_text.lower()
    query_words = set(query_lower.split())

    for doc in docs:
        if review_mode and doc.review_mode != review_mode:
            continue
        if min_score > 0 and doc.score < min_score:
            continue

        text = (doc.content_text + " " + doc.project_alias + " " +
                doc.project_type + " " + str(doc.findings_summary)).lower()

        word_match = sum(1 for w in query_words if w in text)
        seq_match = difflib.SequenceMatcher(None, query_lower[:100], text[:200]).ratio()
        combined = word_match * 0.5 + seq_match * 0.5

        if combined > 0.1:
            matched = _extract_matched_snippet(text, query_lower)
            scored.append((combined, doc, matched))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, doc, matched in scored[:max_results]:
        high = doc.findings_summary.get("HIGH", 0)
        results.append(SearchResult(
            report_id=doc.report_id,
            score=round(score, 3),
            verdict=doc.verdict,
            review_mode=doc.review_mode,
            matched_summary=redact(matched),
            reason=redact(f"相似度 {score:.1%}, 类型={doc.project_type}, "
                          f"高危={high}, 得分={doc.score}"),
            created_at=doc.created_at,
        ))

    return results


def get_common_risks() -> List[str]:
    docs = get_all_documents()
    risk_counter: Dict[str, int] = {}

    for doc in docs:
        for finding in doc.top_security_findings:
            key = _normalize_risk(finding)
            if key:
                risk_counter[key] = risk_counter.get(key, 0) + 1

    sorted_risks = sorted(risk_counter.items(), key=lambda x: -x[1])
    lines = []
    for risk, count in sorted_risks[:10]:
        lines.append(f"{risk} (出现在 {count} 次审查中)")
    return [redact(l) for l in lines]


def generate_advise(
    query_text: str = "",
    max_results: int = 5,
    review_mode: Optional[str] = None,
) -> AdviseResult:
    if not is_index_built():
        return AdviseResult(
            next_fix_plan="知识索引未构建，请先调用 rebuild_index",
            total_reports_analyzed=0,
        )

    all_docs = get_all_documents()
    if not all_docs:
        return AdviseResult(total_reports_analyzed=0)

    similar = search_similar_reports(query_text, max_results=max_results,
                                      review_mode=review_mode) if query_text else []
    source_ids = [s.report_id for s in similar]

    target_docs = []
    if source_ids:
        for rid in source_ids:
            d = get_document(rid)
            if d:
                target_docs.append(d)
    else:
        target_docs = all_docs[:max_results]
        source_ids = [d.report_id for d in target_docs]

    fix_lines = _build_aggregated_fix_plan(target_docs)
    common_risks = get_common_risks()
    talking_points = _build_interview_talking_points(target_docs)

    return AdviseResult(
        next_fix_plan=redact("\n".join(fix_lines)),
        common_risks=common_risks,
        interview_talking_points=talking_points,
        source_report_ids=source_ids,
        total_reports_analyzed=len(all_docs),
    )


def _normalize_risk(finding: str) -> str:
    finding_lower = finding.lower()
    patterns = [
        (".env", ".env 文件风险"),
        ("secret", "密钥/凭据泄露"),
        ("api_key", "API Key 泄露"),
        ("password", "密码泄露"),
        ("authorization", "Authorization 泄露"),
        ("bearer", "Bearer Token 泄露"),
        ("token", "Token 泄露"),
        ("private key", "私钥泄露"),
        ("ssh", "SSH Key 泄露"),
        ("jwt", "JWT Secret 泄露"),
        ("accesskey", "AccessKey 泄露"),
        ("aws_secret", "AWS Secret 泄露"),
        ("openai", "OpenAI Key 泄露"),
        ("debug", "调试模式未关闭"),
        ("hardcoded", "硬编码配置"),
        ("node_modules", "node_modules 泄露"),
        ("__pycache__", "缓存文件泄露"),
        ("cors", "CORS 配置风险"),
        ("sql injection", "SQL 注入风险"),
        ("xss", "XSS 风险"),
        ("path traversal", "路径穿越风险"),
    ]
    for pat, label in patterns:
        if pat in finding_lower:
            return label
    return finding[:60] + "..."


def _extract_matched_snippet(text: str, query: str) -> str:
    idx = text.find(query[:20])
    if idx >= 0:
        start = max(0, idx - 40)
        end = min(len(text), idx + 80)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet
    return text[:100]


def _build_aggregated_fix_plan(docs: List[KnowledgeDocument]) -> List[str]:
    lines = []
    all_high = []
    all_med = []
    for d in docs:
        for finding in d.top_security_findings:
            all_high.append(finding)
        for finding in d.top_structure_findings:
            all_med.append(finding)

    seen = set()
    unique_high = []
    for f in all_high:
        if f not in seen:
            seen.add(f)
            unique_high.append(f)

    seen_med = set()
    unique_med = []
    for f in all_med:
        if f not in seen_med:
            seen_med.add(f)
            unique_med.append(f)

    if unique_high:
        lines.append(f"## 历史报告中发现的高危问题 ({len(unique_high)} 项)")
        for f in unique_high[:8]:
            lines.append(f"- {redact(f)}")
    if unique_med:
        lines.append(f"\n## 中危问题 ({len(unique_med)} 项)")
        for f in unique_med[:5]:
            lines.append(f"- {redact(f)}")
    if not lines:
        lines.append("历史报告中未发现需要修复的问题")
    return lines


def _build_interview_talking_points(docs: List[KnowledgeDocument]) -> List[str]:
    points = []
    for d in docs[:3]:
        if d.verdict == "PASS" and d.score >= 80:
            pts = f"项目 [{d.project_alias}] 质量优秀（{d.score}分），"
            if d.top_security_findings:
                pts += f"但需注意 {d.top_security_findings[0]}"
            else:
                pts += "无明显风险"
            points.append(pts)
        elif d.verdict == "REJECT":
            pts = f"项目 [{d.project_alias}] 存在严重风险（{d.score}分），"
            if d.top_security_findings:
                pts += f"需重点关注 {d.top_security_findings[0]}"
            else:
                pts += "需全面整改"
            points.append(pts)
        else:
            pts = f"项目 [{d.project_alias}] 得分为 {d.score}，"
            pts += f"结论 {d.verdict}"
            if d.top_security_findings:
                pts += f"，主要问题: {d.top_security_findings[0]}"
            points.append(pts)
    return [redact(p) for p in points]
