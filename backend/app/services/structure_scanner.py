from pathlib import Path
from typing import List, Dict

from ..schemas.review import Finding
from ..core.config import settings


def scan_structure(root_dir: Path) -> List[Finding]:
    findings: List[Finding] = []
    files_present: Dict[str, bool] = {}

    checks = {
        "README.md": ("README.md", "项目文档"),
        "requirements.txt": ("requirements.txt", "Python 依赖文件"),
        "pyproject.toml": ("pyproject.toml", "Python 项目配置"),
        "package.json": ("package.json", "Node.js 项目配置"),
        ".env.example": (".env.example", "环境变量示例"),
        ".gitignore": (".gitignore", "Git 忽略配置"),
        "Dockerfile": ("Dockerfile", "Docker 构建文件"),
        "docker-compose.yml": ("docker-compose.yml", "Docker Compose 编排"),
        "LICENSE": ("LICENSE", "开源许可证"),
    }

    for key, (filename, label) in checks.items():
        exists = (root_dir / filename).exists()
        files_present[key] = exists
        if not exists:
            findings.append(
                Finding(
                    severity="MEDIUM",
                    category="交付完整性",
                    message=f"缺少 {label} ({filename})",
                    file_path=filename,
                    recommendation=f"建议添加 {filename} 文件以完善项目交付物",
                )
            )

    tests_dir = root_dir / "tests"
    test_alt = root_dir / "test"
    has_tests = tests_dir.exists() or test_alt.exists()
    files_present["tests/"] = has_tests
    if not has_tests:
        findings.append(
            Finding(
                severity="LOW",
                category="交付完整性",
                message="缺少 tests/ 测试目录",
                file_path="tests/",
                recommendation="建议添加测试目录和单元测试",
            )
        )

    return findings
