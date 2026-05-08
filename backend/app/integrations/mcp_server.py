import io
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

from ..schemas.review import ReviewMode, ReviewRequest, ReviewVerdict
from ..graph.delivery_review_graph import review_graph
from ..graph.state import ReviewState
from ..services.redaction_service import redact
from ..services.report_service import MODE_LABELS
from ..core.config import settings

logger = logging.getLogger(__name__)

mcp = FastMCP("ShipGuard MCP Server")

_last_report: Dict[str, Any] = {}

_SAFE_DIRS: list[Path] = []
_SAFE_DIRS.append(settings.ROOT_DIR / "examples")
if settings.MCP_SAFE_UPLOAD_DIR:
    extra = Path(settings.MCP_SAFE_UPLOAD_DIR)
    if not extra.is_absolute():
        extra = settings.ROOT_DIR / extra
    _SAFE_DIRS.append(extra)

_MAX_ZIP_BYTES = settings.MCP_MAX_ZIP_MB * 1024 * 1024
if _MAX_ZIP_BYTES <= 0:
    _MAX_ZIP_BYTES = 50 * 1024 * 1024


def _validate_zip_path(zip_path: str) -> Path:
    resolved = Path(zip_path).resolve()
    if not resolved.exists():
        raise ValueError(f"文件不存在: {zip_path}")
    if not resolved.is_file():
        raise ValueError(f"路径不是文件: {zip_path}")
    if resolved.suffix.lower() != ".zip":
        raise ValueError(f"不支持的文件类型: {resolved.suffix}，仅支持 .zip")
    if resolved.stat().st_size > _MAX_ZIP_BYTES:
        raise ValueError(f"文件过大 (>{settings.MCP_MAX_ZIP_MB}MB)，请压缩后上传")
    safe = False
    for d in _SAFE_DIRS:
        try:
            resolved.relative_to(d.resolve())
            safe = True
            break
        except ValueError:
            continue
    if not safe:
        rel_allowed = []
        for d in _SAFE_DIRS:
            try:
                rel = d.relative_to(settings.ROOT_DIR)
                rel_allowed.append(str(rel))
            except ValueError:
                rel_allowed.append(d.name)
        allowed = ", ".join(rel_allowed)
        raise ValueError(f"路径不在安全白名单内。允许的目录: {allowed}（相对项目根目录）")
    return resolved


async def _run_review(zip_path: Path, mode: ReviewMode) -> Dict[str, Any]:
    from fastapi import UploadFile

    content = zip_path.read_bytes()
    f = UploadFile(filename=zip_path.name, file=io.BytesIO(content))

    request = ReviewRequest(review_mode=mode)
    request.zip_file = f

    initial: ReviewState = {
        "request": request,
        "zip_path": None,
        "extract_path": None,
        "project_root": None,
        "project_profile": {},
        "structure_findings": [],
        "security_findings": [],
        "dependency_findings": [],
        "readme_findings": [],
        "score": None,
        "verdict": None,
        "report": "",
        "llm_review": {},
        "llm_guard_findings": [],
        "errors": [],
    }

    result = await review_graph.ainvoke(initial)
    return result


def _build_summary(result: Dict[str, Any]) -> str:
    score = result.get("score")
    verdict = result.get("verdict")
    profile = result.get("project_profile", {})
    all_findings = (
        result.get("structure_findings", [])
        + result.get("security_findings", [])
        + result.get("dependency_findings", [])
        + result.get("readme_findings", [])
    )
    high = sum(1 for f in all_findings if f.severity == "HIGH")
    med = sum(1 for f in all_findings if f.severity == "MEDIUM")
    low = sum(1 for f in all_findings if f.severity == "LOW")
    total = score.total if score else 0
    v = verdict.value if verdict else "UNKNOWN"
    pt = profile.get("project_type", "unknown")
    lines = [
        f"审查模式: {MODE_LABELS.get(result['request'].review_mode, result['request'].review_mode.value)}",
        f"总分: {total}/100",
        f"结论: {v}",
        f"项目类型: {pt}",
        f"高危: {high}, 中危: {med}, 低危: {low}",
    ]
    return redact("\n".join(lines))


def _build_fix_plan(result: Dict[str, Any]) -> str:
    all_findings = (
        result.get("structure_findings", [])
        + result.get("security_findings", [])
        + result.get("dependency_findings", [])
        + result.get("readme_findings", [])
    )
    high = [f for f in all_findings if f.severity == "HIGH"]
    med = [f for f in all_findings if f.severity == "MEDIUM"]
    lines = []
    if high:
        lines.append(f"## 高危问题 ({len(high)}) — 优先修复")
        for f in high:
            rec = f.recommendation or "无建议"
            lines.append(f"- {f.message}")
            lines.append(f"  修复建议: {rec}")
    if med:
        lines.append(f"\n## 中危问题 ({len(med)})")
        for f in med[:5]:
            rec = f.recommendation or "无建议"
            lines.append(f"- {f.message}")
            lines.append(f"  修复建议: {rec}")
    if not lines:
        lines.append("未发现需要修复的问题")
    return redact("\n".join(lines))


@mcp.tool()
async def list_review_modes() -> str:
    """返回支持的四种审查模式名称和说明"""
    lines = []
    for mode in ReviewMode:
        label = MODE_LABELS.get(mode, mode.value)
        lines.append(f"- {mode.value}: {label}")
    return "\n".join(lines)


@mcp.tool()
async def review_zip(zip_path: str, review_mode: str = "student_assignment") -> str:
    """审查一个 ZIP 项目文件并返回评分摘要

    Args:
        zip_path: ZIP 文件路径（必须在安全白名单目录内）
        review_mode: 审查模式 (student_assignment | github_showcase | interview_project | commercial_delivery)
    """
    try:
        mode = ReviewMode(review_mode)
    except ValueError:
        allowed = [m.value for m in ReviewMode]
        return f"无效的审查模式: {review_mode}，可选: {allowed}"

    try:
        resolved = _validate_zip_path(zip_path)
    except ValueError as e:
        return str(e)

    try:
        result = await _run_review(resolved, mode)
    except Exception as e:
        logger.exception("MCP review failed")
        return f"审查失败: {type(e).__name__}: {e}"

    global _last_report
    _last_report = result

    summary = _build_summary(result)
    return summary


@mcp.tool()
async def get_last_report() -> str:
    """返回最近一次审查报告的脱敏摘要"""
    if not _last_report:
        return "尚未执行审查"
    return _build_summary(_last_report)


@mcp.tool()
async def explain_fix_plan() -> str:
    """基于最近一次审查结果生成整改建议"""
    if not _last_report:
        return "尚未执行审查，请先运行 review_zip"
    return _build_fix_plan(_last_report)


def run_mcp_server(host: str = "127.0.0.1", port: int = 8100):
    """启动 MCP Server（默认仅监听本地）"""
    if not settings.MCP_ENABLED:
        logger.warning("MCP_ENABLED=false，不启动 MCP Server")
        return
    logger.info(f"Starting MCP server on {host}:{port}")
    mcp.run(host=host, port=port)
