from typing import List, Dict, Any
from datetime import datetime

from ..schemas.review import (
    ReviewRequest, ReviewMode, ReviewVerdict,
    Finding, ReviewScore,
)
from ..core.config import settings


MODE_LABELS = {
    ReviewMode.student_assignment: "学生作业",
    ReviewMode.github_showcase: "GitHub 展示项目",
    ReviewMode.interview_project: "面试项目",
    ReviewMode.commercial_delivery: "商业交付",
}


def calculate_score(
    structure_findings: List[Finding],
    security_findings: List[Finding],
    dependency_findings: List[Finding],
    readme_findings: List[Finding],
    profile: Dict[str, Any],
) -> ReviewScore:
    # 1. 交付物完整性 (20分)
    delivery_score = 20
    key_files = profile.get("key_files", {})
    required_files = ["README.md", ".env.example", ".gitignore"]
    for f in required_files:
        if not key_files.get(f, False):
            delivery_score -= 4
    if not key_files.get("tests/"):
        delivery_score -= 3
    if not key_files.get("LICENSE"):
        delivery_score -= 2
    delivery_score = max(0, delivery_score)

    # 2. 安全风险 (25分) — 扣分制，找到越少分越高
    security_score = 25
    high_count = sum(1 for f in security_findings if f.severity == "HIGH")
    med_count = sum(1 for f in security_findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in security_findings if f.severity == "LOW")
    security_score -= high_count * 8
    security_score -= med_count * 4
    security_score -= low_count * 2
    if key_files.get(".env.example"):
        security_score += 3
    security_score = max(0, min(25, security_score))

    # 3. 运行与依赖配置 (20分)
    dep_score = 20
    has_any_dep = (
        key_files.get("requirements.txt", False)
        or key_files.get("pyproject.toml", False)
        or key_files.get("package.json", False)
    )
    if not has_any_dep:
        dep_score -= 10
    for f in dependency_findings:
        if f.severity == "HIGH":
            dep_score -= 5
        elif f.severity == "MEDIUM":
            dep_score -= 3
        else:
            dep_score -= 1
    dep_score = max(0, min(20, dep_score))

    # 4. README 文档质量 (15分)
    readme_score = 15
    if not key_files.get("README.md", False):
        readme_score = 0
    else:
        high_readme = sum(1 for f in readme_findings if f.severity == "HIGH")
        med_readme = sum(1 for f in readme_findings if f.severity == "MEDIUM")
        readme_score -= high_readme * 5
        readme_score -= med_readme * 3
        readme_score = max(0, readme_score)

    # 5. Docker / 部署说明 (10分)
    docker_score = 10
    has_dockerfile = key_files.get("Dockerfile", False)
    has_docker_compose = key_files.get("docker-compose.yml", False)
    if not has_dockerfile:
        docker_score -= 5
    if not has_docker_compose:
        docker_score -= 3
    docker_score = max(0, docker_score)

    # 6. 项目结构与可维护性 (10分)
    struct_score = 10
    has_backend = profile.get("has_backend", False)
    has_frontend = profile.get("has_frontend", False)
    if not has_backend and not has_frontend:
        struct_score -= 3
    struct_score -= len(structure_findings)
    struct_score = max(0, min(10, struct_score))

    total = delivery_score + security_score + dep_score + readme_score + docker_score + struct_score

    return ReviewScore(
        delivery_completeness=delivery_score,
        security_risk=security_score,
        dependency_config=dep_score,
        readme_quality=readme_score,
        docker_deploy=docker_score,
        structure_maintainability=struct_score,
        total=total,
    )


def determine_verdict(total_score: int) -> ReviewVerdict:
    if total_score >= settings.PASS_THRESHOLD:
        return ReviewVerdict.PASS
    elif total_score >= settings.CONDITIONAL_PASS_THRESHOLD:
        return ReviewVerdict.CONDITIONAL_PASS
    return ReviewVerdict.REJECT


def generate_report(
    request: ReviewRequest,
    profile: Dict[str, Any],
    structure_findings: List[Finding],
    security_findings: List[Finding],
    dependency_findings: List[Finding],
    readme_findings: List[Finding],
) -> str:
    score = calculate_score(
        structure_findings, security_findings,
        dependency_findings, readme_findings, profile,
    )
    verdict = determine_verdict(score.total)

    all_findings = structure_findings + security_findings + dependency_findings + readme_findings
    high_issues = [f for f in all_findings if f.severity == "HIGH"]
    med_issues = [f for f in all_findings if f.severity == "MEDIUM"]
    low_issues = [f for f in all_findings if f.severity == "LOW"]

    mode_label = MODE_LABELS.get(request.review_mode, request.review_mode.value)
    verdict_icon = {"PASS": "✅", "CONDITIONAL_PASS": "⚠️", "REJECT": "❌"}.get(verdict.value, "❓")

    key_files = profile.get("key_files", {})
    file_checklist = "\n".join(
        f"- {'✅' if present else '❌'} {name}"
        for name, present in sorted(key_files.items())
    )

    high_section = "\n".join(
        f"- 🔴 **{f.message}**"
        + (f"\n  - 修复建议: {f.recommendation}" if f.recommendation else "")
        for f in high_issues
    ) or "无高危问题 🎉"

    med_section = "\n".join(
        f"- 🟡 **{f.message}**"
        + (f"\n  - 修复建议: {f.recommendation}" if f.recommendation else "")
        for f in med_issues
    ) or "无中危问题 ✅"

    low_section = "\n".join(
        f"- 🟢 **{f.message}**"
        + (f"\n  - 修复建议: {f.recommendation}" if f.recommendation else "")
        for f in low_issues
    ) or "无低危问题 ✅"

    fix_prompts = _generate_fix_prompts(high_issues, med_issues, profile)

    report = f"""# AI 项目交付审查报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 审查模式: {mode_label}

---

## 审查结论

{verdict_icon} **{verdict.value}** | 总分: **{score.total}/100**

| 维度 | 得分 | 满分 |
|------|:----:|:----:|
| 交付物完整性 | {score.delivery_completeness} | 20 |
| 安全风险 | {score.security_risk} | 25 |
| 运行与依赖配置 | {score.dependency_config} | 20 |
| README 文档质量 | {score.readme_quality} | 15 |
| Docker / 部署说明 | {score.docker_deploy} | 10 |
| 项目结构与可维护性 | {score.structure_maintainability} | 10 |
| **总分** | **{score.total}** | **100** |

---

## 项目画像

| 属性 | 值 |
|------|-----|
| 项目类型 | {profile.get('project_type', 'unknown')} |
| 检测语言 | {', '.join(profile.get('detected_languages', ['N/A']))} |
| 检测框架 | {', '.join(profile.get('detected_frameworks', ['N/A']))} |
| 包含后端 | {'✅' if profile.get('has_backend') else '❌'} |
| 包含前端 | {'✅' if profile.get('has_frontend') else '❌'} |

---

## 文件完整度清单

{file_checklist}

---

## 高危问题 ({len(high_issues)})

{high_section}

---

## 中危问题 ({len(med_issues)})

{med_section}

---

## 低危问题 ({len(low_issues)})

{low_section}

---

## 修复建议（可复制给 AI 编码助手）

以下是可以复制给 Trae/Cursor 等 AI 编码助手的修复 Prompt：

{fix_prompts}

---

*报告由 AI Delivery Inspector 自动生成*
"""

    return report


def _generate_fix_prompts(
    high_issues: List[Finding],
    med_issues: List[Finding],
    profile: Dict[str, Any],
) -> str:
    prompts = []
    key_files = profile.get("key_files", {})

    if not key_files.get("README.md", False):
        prompts.append("### 1. 创建 README.md\n```\n请为项目创建 README.md 文件，需包含：\n1. 项目简介与目的\n2. 环境要求（Python/Node 版本等）\n3. 安装与运行步骤\n4. 测试说明\n5. 配置说明\n```")

    if not key_files.get(".env.example", False):
        prompts.append("### 2. 创建 .env.example\n```\n请根据项目实际使用的环境变量，创建 .env.example 文件，\n将所有密钥值替换为占位符（如 your-api-key-here）。\n确保 .env 已添加到 .gitignore。\n```")

    for h in high_issues:
        if h.recommendation:
            prompts.append(f"### 修复: {h.message}\n```\n{h.recommendation}\n```")

    for m in med_issues[:3]:
        if m.recommendation:
            prompts.append(f"### 优化: {m.message}\n```\n{m.recommendation}\n```")

    if not prompts:
        prompts.append("项目整体质量良好，无需重大修复。")

    return "\n\n".join(prompts)
