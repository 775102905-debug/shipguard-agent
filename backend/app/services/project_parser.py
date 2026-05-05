from pathlib import Path
from typing import Dict, Any

from ..core.config import settings


def find_project_root(extract_path: Path) -> Path:
    markers = [
        "README.md", "requirements.txt", "pyproject.toml",
        "package.json", "Dockerfile", "docker-compose.yml",
        "setup.py", "setup.cfg", "Makefile",
    ]
    candidates = sorted(extract_path.rglob("*"), key=lambda p: len(p.parts))

    dir_scores: Dict[Path, int] = {}
    for candidate in candidates:
        if candidate.is_file() and candidate.name in markers:
            parent = candidate.parent
            dir_scores[parent] = dir_scores.get(parent, 0) + 1

    if dir_scores:
        best = max(dir_scores, key=dir_scores.get)
        return best

    return extract_path


def detect_project_type(root_dir: Path) -> Dict[str, Any]:
    files = {p.name for p in root_dir.iterdir() if p.is_file()}
    dirs = {p.name for p in root_dir.iterdir() if p.is_dir()}

    has_requirements = "requirements.txt" in files
    has_pyproject = "pyproject.toml" in files
    has_package_json = "package.json" in files
    has_dockerfile = "Dockerfile" in files
    has_docker_compose = "docker-compose.yml" in files

    has_backend = has_requirements or has_pyproject or "setup.py" in files
    has_frontend = has_package_json

    languages = []
    frameworks = []

    if has_requirements:
        languages.append("Python")
        req_text = (root_dir / "requirements.txt").read_text(encoding="utf-8", errors="ignore")
        if "fastapi" in req_text.lower():
            frameworks.append("FastAPI")
        if "langgraph" in req_text.lower() or "langchain" in req_text.lower():
            frameworks.append("LangGraph")
        if "flask" in req_text.lower():
            frameworks.append("Flask")
        if "django" in req_text.lower():
            frameworks.append("Django")

    if has_pyproject:
        languages.append("Python")
        pyproject_text = (root_dir / "pyproject.toml").read_text(encoding="utf-8", errors="ignore")
        if "fastapi" in pyproject_text.lower():
            frameworks.append("FastAPI")

    if has_package_json:
        languages.append("JavaScript/TypeScript")
        pkg_text = (root_dir / "package.json").read_text(encoding="utf-8", errors="ignore")
        if '"react"' in pkg_text.lower() or '"react-dom"' in pkg_text.lower():
            frameworks.append("React")
        if '"vite"' in pkg_text.lower():
            frameworks.append("Vite")
        if '"next"' in pkg_text.lower():
            frameworks.append("Next.js")
        if '"vue"' in pkg_text.lower():
            frameworks.append("Vue")

    if (root_dir / "go.mod").exists():
        languages.append("Go")
    if (root_dir / "Cargo.toml").exists():
        languages.append("Rust")

    languages = list(dict.fromkeys(languages))
    frameworks = list(dict.fromkeys(frameworks))

    if not languages:
        all_files = list(root_dir.rglob("*"))
        exts = {p.suffix.lower() for p in all_files if p.is_file() and p.suffix}
        ext_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".jsx": "React JSX", ".tsx": "React TSX", ".go": "Go",
            ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
            ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
            ".vue": "Vue", ".css": "CSS", ".html": "HTML",
        }
        for ext, lang in ext_map.items():
            if ext in exts:
                languages.append(lang)

    project_type = "unknown"
    if has_backend and has_frontend:
        project_type = "fullstack"
    elif has_backend:
        project_type = "backend"
    elif has_frontend:
        project_type = "frontend"

    key_files = {
        "README.md": (root_dir / "README.md").exists(),
        "requirements.txt": has_requirements,
        "pyproject.toml": has_pyproject,
        "package.json": has_package_json,
        ".env.example": (root_dir / ".env.example").exists(),
        ".gitignore": (root_dir / ".gitignore").exists(),
        "Dockerfile": has_dockerfile,
        "docker-compose.yml": has_docker_compose,
        "LICENSE": (root_dir / "LICENSE").exists() or (root_dir / "LICENSE.txt").exists(),
        "tests/": (root_dir / "tests").exists() or (root_dir / "test").exists(),
    }

    return {
        "project_type": project_type,
        "has_backend": has_backend,
        "has_frontend": has_frontend,
        "detected_languages": languages,
        "detected_frameworks": frameworks,
        "key_files": key_files,
        "root_dir": str(root_dir),
    }


def should_ignore(name: str) -> bool:
    return name in settings.IGNORED_DIRS
