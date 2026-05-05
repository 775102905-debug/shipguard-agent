from pathlib import Path
from typing import List, Set

from ..schemas.review import Finding
from ..core.security_patterns import SECURITY_PATTERNS
from ..core.config import settings


def _skip_dir(name: str) -> bool:
    return name in settings.IGNORED_DIRS or name.startswith(".")


def scan_security(root_dir: Path) -> List[Finding]:
    findings: List[Finding] = []
    matched_files: Set[Path] = set()

    env_file = root_dir / ".env"
    if env_file.exists():
        findings.append(
            Finding(
                severity="MEDIUM",
                category="安全风险",
                message="发现 .env 文件 — 包含敏感环境变量，不应提交到版本控制",
                file_path=".env",
                recommendation="将 .env 添加到 .gitignore，使用 .env.example 作为模板提交",
            )
        )
        matched_files.add(env_file)

    text_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yml", ".yaml",
        ".toml", ".cfg", ".ini", ".conf", ".env", ".txt", ".md",
        ".html", ".css", ".scss", ".vue", ".sh", ".bat", ".ps1",
        ".dockerfile", ".yaml", ".yml", ".xml", ".sql",
    }

    for file_path in root_dir.rglob("*"):
        if file_path in matched_files:
            continue
        if file_path.is_dir():
            if _skip_dir(file_path.name):
                continue
            continue

        if file_path.suffix.lower() not in text_extensions:
            continue

        if any(_skip_dir(p.name) for p in file_path.relative_to(root_dir).parents):
            continue

        if file_path.name == ".env" or file_path.name.startswith(".env."):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""

        for sp in SECURITY_PATTERNS:
            matches = sp.pattern.findall(content)
            if matches:
                rel_path = str(file_path.relative_to(root_dir))
                if file_path not in matched_files:
                    finding = Finding(
                        severity=sp.severity,
                        category="安全风险",
                        message=f"{sp.description} — 文件: {rel_path}",
                        file_path=rel_path,
                        recommendation=_get_recommendation(sp.name),
                    )
                    findings.append(finding)
                    matched_files.add(file_path)

    return findings


def _get_recommendation(pattern_name: str) -> str:
    recommendations = {
        "OpenAI API Key (sk-)": "使用环境变量替代硬编码密钥，将 API Key 移至 .env 文件并添加到 .gitignore",
        "GitHub Personal Access Token (ghp_)": "使用环境变量或 GitHub Secrets 管理 Token",
        "AWS Access Key (AKIA)": "使用 AWS IAM Role 或环境变量管理密钥",
        "Generic SECRET": "使用环境变量替代硬编码密钥",
        "Generic PASSWORD": "使用环境变量或密钥管理服务管理密码",
        "Bearer Token": "使用环境变量管理 Token，避免硬编码",
        "Authorization Header": "避免在代码中硬编码 Authorization 信息",
        "Windows Local Path (C:\\Users\\)": "使用相对路径或 pathlib 动态构建路径",
        "macOS/Linux Local Path (/Users/)": "使用相对路径或 pathlib 动态构建路径",
        "Debug Mode Enabled (debug=True)": "生产环境应设置 debug=False",
        "DEBUG Mode Enabled (DEBUG=True)": "生产环境应设置 DEBUG=False",
        "CORS Wildcard (*)": "生产环境应限制 CORS 为具体域名",
    }
    return recommendations.get(pattern_name, "建议移除或使用安全的方式管理敏感信息")
