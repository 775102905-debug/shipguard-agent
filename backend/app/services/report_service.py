from typing import List, Dict, Any, Optional
from datetime import datetime

from ..schemas.review import (
    ReviewRequest, ReviewMode, ReviewVerdict,
    Finding, ReviewScore,
)
from ..core.review_modes import get_profile


MODE_LABELS = {
    ReviewMode.student_assignment: "学生作业",
    ReviewMode.github_showcase: "GitHub 展示项目",
    ReviewMode.interview_project: "面试项目",
    ReviewMode.commercial_delivery: "商业交付",
}


def calculate_score(
    review_mode: ReviewMode,
    structure_findings: List[Finding],
    security_findings: List[Finding],
    dependency_findings: List[Finding],
    readme_findings: List[Finding],
    profile: Dict[str, Any],
) -> ReviewScore:
    mp = get_profile(review_mode)
    key_files = profile.get("key_files", {})

    delivery_score = 20
    required_files = ["README.md", ".env.example", ".gitignore"]
    if not key_files.get("README.md", False):
        delivery_score -= mp.penalty_missing_readme
    if not key_files.get(".env.example", False):
        delivery_score -= mp.penalty_missing_env_example
    if not key_files.get(".gitignore", False):
        delivery_score -= mp.penalty_missing_gitignore
    if not key_files.get("tests/"):
        delivery_score -= mp.penalty_missing_tests
    if not key_files.get("LICENSE"):
        delivery_score -= mp.penalty_missing_license
    delivery_score = max(0, delivery_score)

    security_score = 25
    high_count = sum(1 for f in security_findings if f.severity == "HIGH")
    med_count = sum(1 for f in security_findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in security_findings if f.severity == "LOW")
    security_score -= int(high_count * mp.security_high_penalty * mp.security_multiplier)
    security_score -= int(med_count * mp.security_med_penalty * mp.security_multiplier)
    security_score -= int(low_count * mp.security_low_penalty * mp.security_multiplier)
    if key_files.get(".env.example"):
        security_score += 3
    security_score = max(0, min(25, security_score))

    dep_score = 20
    has_any_dep = (
        key_files.get("requirements.txt", False)
        or key_files.get("pyproject.toml", False)
        or key_files.get("package.json", False)
    )
    if not has_any_dep:
        dep_score -= int(10 * mp.dependency_multiplier)
    for f in dependency_findings:
        if f.severity == "HIGH":
            dep_score -= int(mp.dependency_high_penalty * mp.dependency_multiplier)
        elif f.severity == "MEDIUM":
            dep_score -= int(mp.dependency_med_penalty * mp.dependency_multiplier)
        else:
            dep_score -= int(1 * mp.dependency_multiplier)
    dep_score = max(0, min(20, dep_score))

    readme_score = 15
    if not key_files.get("README.md", False):
        readme_score = 0
    else:
        high_readme = sum(1 for f in readme_findings if f.severity == "HIGH")
        med_readme = sum(1 for f in readme_findings if f.severity == "MEDIUM")
        readme_score -= int(high_readme * 5 * mp.documentation_multiplier)
        readme_score -= int(med_readme * 3 * mp.documentation_multiplier)
        readme_score = max(0, readme_score)

    docker_score = 10
    has_dockerfile = key_files.get("Dockerfile", False)
    has_docker_compose = key_files.get("docker-compose.yml", False)
    if not has_dockerfile:
        docker_score -= int(5 * mp.deployment_multiplier)
    if not has_docker_compose:
        docker_score -= int(3 * mp.deployment_multiplier)
    docker_score = max(0, docker_score)

    struct_score = 10
    has_backend = profile.get("has_backend", False)
    has_frontend = profile.get("has_frontend", False)
    if not has_backend and not has_frontend:
        struct_score -= int(3 * mp.maintainability_multiplier)
    struct_score -= int(len(structure_findings) * mp.maintainability_multiplier)
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


def determine_verdict(review_mode: ReviewMode, total_score: int, security_findings: List[Finding]) -> ReviewVerdict:
    mp = get_profile(review_mode)

    high_security_count = sum(1 for f in security_findings if f.severity == "HIGH")

    if mp.max_high_security_for_pass is not None and high_security_count > mp.max_high_security_for_pass:
        if mp.max_high_security_for_conditional_pass is not None and high_security_count > mp.max_high_security_for_conditional_pass:
            return ReviewVerdict.REJECT
        return ReviewVerdict.CONDITIONAL_PASS

    if total_score >= mp.pass_threshold:
        return ReviewVerdict.PASS
    elif total_score >= mp.conditional_threshold:
        return ReviewVerdict.CONDITIONAL_PASS
    return ReviewVerdict.REJECT


def generate_report(
    request: ReviewRequest,
    profile: Dict[str, Any],
    structure_findings: List[Finding],
    security_findings: List[Finding],
    dependency_findings: List[Finding],
    readme_findings: List[Finding],
    score: ReviewScore,
    verdict: ReviewVerdict,
    llm_review: Dict[str, Any],
    llm_guard_findings: Optional[List[Dict[str, Any]]] = None,
) -> str:
    all_findings = structure_findings + security_findings + dependency_findings + readme_findings
    high_issues = [f for f in all_findings if f.severity == "HIGH"]
    med_issues = [f for f in all_findings if f.severity == "MEDIUM"]
    low_issues = [f for f in all_findings if f.severity == "LOW"]

    mode_label = MODE_LABELS.get(request.review_mode, request.review_mode.value)
    mp = get_profile(request.review_mode)
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

## 当前审查模式说明

**{mode_label}**
{mp.guidance}

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

## AI 审查官意见

{_format_llm_section(llm_review, mode_label)}

---

{_format_llm_guard_section(llm_guard_findings)}

---

*报告由 AI Delivery Inspector 自动生成*
"""

    return report


def _format_llm_guard_section(guard_findings: Optional[List[Dict[str, Any]]]) -> str:
    if not guard_findings:
        return ""
    parts = ["## LLM Guard 安全扫描"]
    for f in guard_findings:
        parts.append(f"- 类型: {f.get('type', 'unknown')}, 严重程度: {f.get('severity', 'unknown')}")
    return "\n".join(parts)


def _format_llm_section(llm_review: Dict[str, Any], mode_label: str) -> str:
    if not llm_review.get("llm_reviewer_enabled", False):
        error_type = llm_review.get("llm_error_type", "")
        msg = llm_review.get("llm_error", "")
        if error_type == "malformed_json":
            return (
                f"LLM Reviewer 已调用，但模型返回内容不是合法 JSON，"
                f"系统已自动降级为规则审查报告。请检查模型是否遵守 JSON-only 输出格式。\n\n"
                f"本报告使用规则审查和 {mode_label} profile 生成。"
            )
        if msg:
            return f"LLM Reviewer 尝试运行但失败: {msg}\n\n本报告使用规则审查和 {mode_label} profile 生成。"
        return f"LLM Reviewer 未启用。本报告使用规则审查和 {mode_label} profile 生成。"

    parts = []
    model = llm_review.get("llm_model_used", "")
    profile = llm_review.get("llm_profile_used", "")
    conf = llm_review.get("confidence", "medium")

    parts.append(f"- **启用状态**: 已启用")
    if model:
        parts.append(f"- **模型**: {model}")
    if profile:
        parts.append(f"- **审查模式**: {profile}")
    parts.append(f"- **置信度**: {conf}")

    assessment = llm_review.get("mode_specific_assessment", "")
    if assessment:
        parts.append(f"\n**模式化审查结论**:\n{assessment}")

    risks = llm_review.get("top_risks", [])
    if risks:
        parts.append(f"\n**重点风险**:")
        for r in risks:
            parts.append(f"- {r}")

    actions = llm_review.get("recommended_actions", [])
    if actions:
        parts.append(f"\n**建议动作**:")
        for a in actions:
            parts.append(f"- {a}")

    notes = llm_review.get("interview_or_delivery_notes", [])
    if notes:
        parts.append(f"\n**附加说明**:")
        for n in notes:
            parts.append(f"- {n}")

    return "\n".join(parts)


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
