import logging
from pathlib import Path
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from .state import ReviewState
from ..schemas.review import ReviewRequest, ReviewVerdict
from ..services import (
    zip_service,
    project_parser,
    structure_scanner,
    security_scanner,
    dependency_scanner,
    readme_reviewer,
    report_service,
)

logger = logging.getLogger(__name__)


def node_extract_zip(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 解压 ZIP ===")
    req = state["request"]
    extract_path = zip_service.extract_zip_safe(req.zip_file)
    return {"extract_path": extract_path}


def node_find_project_root(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 查找项目根目录 ===")
    extract_path = state["extract_path"]
    project_root = project_parser.find_project_root(extract_path)
    return {"project_root": project_root}


def node_analyze_project(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 项目画像分析 ===")
    project_root = state["project_root"]
    profile = project_parser.detect_project_type(project_root)
    return {"project_profile": profile}


def node_scan_structure(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 结构审查 ===")
    project_root = state["project_root"]
    findings = structure_scanner.scan_structure(project_root)
    return {"structure_findings": findings}


def node_scan_security(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 安全审查 ===")
    project_root = state["project_root"]
    findings = security_scanner.scan_security(project_root)
    return {"security_findings": findings}


def node_scan_dependencies(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 依赖审查 ===")
    project_root = state["project_root"]
    findings = dependency_scanner.scan_dependencies(project_root)
    return {"dependency_findings": findings}


def node_review_readme(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: README 审查 ===")
    project_root = state["project_root"]
    findings = readme_reviewer.review_readme(project_root)
    return {"readme_findings": findings}


def node_generate_report(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 生成报告 ===")
    report = report_service.generate_report(
        request=state["request"],
        profile=state["project_profile"],
        structure_findings=state["structure_findings"],
        security_findings=state["security_findings"],
        dependency_findings=state["dependency_findings"],
        readme_findings=state["readme_findings"],
    )

    req = state["request"]
    score = report_service.calculate_score(
        req.review_mode,
        state["structure_findings"],
        state["security_findings"],
        state["dependency_findings"],
        state["readme_findings"],
        state["project_profile"],
    )
    verdict = report_service.determine_verdict(req.review_mode, score.total, state["security_findings"])

    return {
        "report": report,
        "score": score,
        "verdict": verdict,
    }


def node_cleanup(state: ReviewState) -> Dict[str, Any]:
    logger.info("=== 节点: 清理临时文件 ===")
    extract_path = state.get("extract_path")
    if extract_path:
        zip_service.cleanup_dir(extract_path)


def build_review_graph() -> StateGraph:
    graph = StateGraph(ReviewState)

    graph.add_node("extract_zip", node_extract_zip)
    graph.add_node("find_project_root", node_find_project_root)
    graph.add_node("analyze_project", node_analyze_project)
    graph.add_node("scan_structure", node_scan_structure)
    graph.add_node("scan_security", node_scan_security)
    graph.add_node("scan_dependencies", node_scan_dependencies)
    graph.add_node("review_readme", node_review_readme)
    graph.add_node("generate_report", node_generate_report)
    graph.add_node("cleanup", node_cleanup)

    graph.add_edge(START, "extract_zip")
    graph.add_edge("extract_zip", "find_project_root")
    graph.add_edge("find_project_root", "analyze_project")
    graph.add_edge("analyze_project", "scan_structure")
    graph.add_edge("analyze_project", "scan_security")
    graph.add_edge("analyze_project", "scan_dependencies")
    graph.add_edge("analyze_project", "review_readme")
    graph.add_edge("scan_structure", "generate_report")
    graph.add_edge("scan_security", "generate_report")
    graph.add_edge("scan_dependencies", "generate_report")
    graph.add_edge("review_readme", "generate_report")
    graph.add_edge("generate_report", "cleanup")
    graph.add_edge("cleanup", END)

    return graph.compile()


review_graph = build_review_graph()
