from pathlib import Path
from typing import List, Dict

from ..schemas.review import Finding


REQUIRED_SECTIONS = {
    "项目简介": ["# ", "项目简介", "介绍", "概述", "背景", "overview", "introduction", "about"],
    "环境要求": ["环境", "requirements", "前置条件", "prerequisites", "系统要求"],
    "安装步骤": ["安装", "install", "setup", "getting started", "quick start"],
    "运行命令": ["运行", "run", "启动", "start", "usage", "使用"],
    "测试说明": ["测试", "test", "testing"],
    "配置说明": ["配置", "配置说明", "环境变量", "配置项", "configuration", "config", ".env"],
}


def review_readme(root_dir: Path) -> List[Finding]:
    findings: List[Finding] = []
    readme_path = root_dir / "README.md"

    if not readme_path.exists():
        alt_readme = root_dir / "README"
        if alt_readme.exists():
            readme_path = alt_readme
        else:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="README 文档",
                    message="项目缺少 README.md 文件",
                    file_path="README.md",
                    recommendation="请创建 README.md 文件，包含项目简介、安装步骤、运行说明等内容",
                )
            )
            return findings

    content = readme_path.read_text(encoding="utf-8", errors="ignore")
    content_lower = content.lower()
    missing_sections: List[str] = []
    section_status: Dict[str, bool] = {}

    for section_name, keywords in REQUIRED_SECTIONS.items():
        found = any(kw.lower() in content_lower for kw in keywords)
        section_status[section_name] = found
        if not found:
            missing_sections.append(section_name)

    content_length = len(content.strip())
    if content_length < 50:
        findings.append(
            Finding(
                severity="HIGH",
                category="README 文档",
                message="README.md 内容过短，缺少有效信息",
                file_path="README.md",
                recommendation="请补充项目说明，至少包含项目简介和使用方法",
            )
        )
        return findings

    for section in missing_sections:
        recommendations = {
            "项目简介": "请在 README 开头添加项目简介，说明项目的目的和功能",
            "环境要求": "请说明项目运行所需的 Python/Node 版本、操作系统等环境要求",
            "安装步骤": "请添加安装依赖的步骤说明",
            "运行命令": "请提供启动项目的命令示例",
            "测试说明": "请说明如何运行测试",
            "配置说明": "请说明项目的配置项和环境变量",
        }
        findings.append(
            Finding(
                severity="MEDIUM",
                category="README 文档",
                message=f"README.md 缺少「{section}」部分",
                file_path="README.md",
                recommendation=recommendations.get(section, f"建议在 README 中添加 {section} 说明"),
            )
        )

    return findings
