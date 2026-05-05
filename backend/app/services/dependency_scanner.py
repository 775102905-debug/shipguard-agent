from pathlib import Path
from typing import List

from ..schemas.review import Finding


def scan_dependencies(root_dir: Path) -> List[Finding]:
    findings: List[Finding] = []
    has_requirements = (root_dir / "requirements.txt").exists()
    has_pyproject = (root_dir / "pyproject.toml").exists()
    has_package_json = (root_dir / "package.json").exists()

    if not has_requirements and not has_pyproject and not has_package_json:
        findings.append(
            Finding(
                severity="HIGH",
                category="依赖配置",
                message="未检测到任何依赖管理文件（requirements.txt、pyproject.toml、package.json）",
                file_path="",
                recommendation="请添加依赖管理文件以声明项目依赖",
            )
        )
        return findings

    if has_requirements:
        _check_requirements_txt(root_dir, findings)

    if has_pyproject:
        _check_pyproject_toml(root_dir, findings)

    if has_package_json:
        _check_package_json(root_dir, findings)

    return findings


def _check_requirements_txt(root_dir: Path, findings: List[Finding]) -> None:
    content = (root_dir / "requirements.txt").read_text(encoding="utf-8", errors="ignore")
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]

    if not lines:
        findings.append(
            Finding(
                severity="MEDIUM",
                category="依赖配置",
                message="requirements.txt 文件为空，未声明任何依赖",
                file_path="requirements.txt",
                recommendation="请添加实际的项目依赖包",
            )
        )
        return

    for line in lines:
        if "==" not in line and not line.startswith("-r") and not line.startswith("--"):
            findings.append(
                Finding(
                    severity="LOW",
                    category="依赖配置",
                    message=f"依赖未锁定版本号: {line}",
                    file_path="requirements.txt",
                    recommendation=f"建议锁定 {line} 的版本号，如 {line}==x.y.z",
                )
            )


def _check_pyproject_toml(root_dir: Path, findings: List[Finding]) -> None:
    content = (root_dir / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
    if "[project]" not in content and "[tool.poetry]" not in content:
        findings.append(
            Finding(
                severity="MEDIUM",
                category="依赖配置",
                message="pyproject.toml 缺少 [project] 或 [tool.poetry] 配置段",
                file_path="pyproject.toml",
                recommendation="请在 pyproject.toml 中正确配置项目元数据和依赖",
            )
        )

    if "dependencies" not in content.lower():
        findings.append(
            Finding(
                severity="LOW",
                category="依赖配置",
                message="pyproject.toml 中未声明 dependencies",
                file_path="pyproject.toml",
                recommendation="请在 pyproject.toml 中添加 dependencies 配置",
            )
        )


def _check_package_json(root_dir: Path, findings: List[Finding]) -> None:
    content = (root_dir / "package.json").read_text(encoding="utf-8", errors="ignore")

    if '"dependencies"' not in content and '"devDependencies"' not in content:
        findings.append(
            Finding(
                severity="MEDIUM",
                category="依赖配置",
                message="package.json 未声明任何 dependencies 或 devDependencies",
                file_path="package.json",
                recommendation="请添加项目所需的 Node 依赖包",
            )
        )
