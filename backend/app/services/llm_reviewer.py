import json
import logging
from typing import Optional, Dict, Any

from ..schemas.review import ReviewMode
from ..core.llm_review_profiles import get_llm_profile, LLM_REVIEW_PROFILES
from ..core.config import settings

logger = logging.getLogger(__name__)


async def run_llm_review(
    review_mode: ReviewMode,
    evidence_summary: Dict[str, Any],
) -> Dict[str, Any]:
    if not settings.LLM_REVIEW_ENABLED:
        return _disabled_result()

    if not settings.LLM_API_KEY:
        logger.warning("LLM_REVIEW_ENABLED=true but LLM_API_KEY is empty")
        return _error_result("LLM_API_KEY not configured")

    profile = get_llm_profile(review_mode)
    model = _resolve_model(profile.model_env_key)

    system_prompt = profile.system_prompt
    user_prompt = _build_user_prompt(profile, evidence_summary)

    try:
        result = await _call_llm_api(system_prompt, user_prompt, model)
        return result
    except Exception as e:
        logger.exception(f"LLM review failed: {e}")
        return _error_result(str(e))


def _resolve_model(env_key: str) -> str:
    env_value = getattr(settings, env_key, None)
    return env_value or settings.LLM_DEFAULT_MODEL


def _build_user_prompt(profile: Any, summary: Dict[str, Any]) -> str:
    prompt = f"""审查模式: {profile.label}
关注领域: {profile.focus_areas}

项目画像:
- 类型: {summary.get('project_type', 'unknown')}
- 语言: {', '.join(summary.get('detected_languages', []))}
- 框架: {', '.join(summary.get('detected_frameworks', []))}
- 包含后端: {summary.get('has_backend', False)}
- 包含前端: {summary.get('has_frontend', False)}

评分: {summary.get('total_score', 0)}/100
当前结论: {summary.get('verdict', 'unknown')}

缺失关键文件: {summary.get('missing_critical_files', [])}

安全发现摘要:
"""
    sec = summary.get("security_severity_summary", {})
    prompt += f"- HIGH: {sec.get('HIGH', 0)}, MEDIUM: {sec.get('MEDIUM', 0)}, LOW: {sec.get('LOW', 0)}\n"
    for f in summary.get("top_security_findings", []):
        prompt += f"  - [{f['severity']}] {f['message']}\n"

    prompt += "\n依赖发现:\n"
    for f in summary.get("dependency_findings_summary", []):
        prompt += f"  - [{f['severity']}] {f['message']}\n"

    prompt += "\nREADME 发现:\n"
    for f in summary.get("readme_findings_summary", []):
        prompt += f"  - [{f['severity']}] {f['message']}\n"

    prompt += "\n结构发现:\n"
    for f in summary.get("structure_findings_summary", []):
        prompt += f"  - [{f['severity']}] {f['message']}\n"

    prompt += """
请返回 JSON 格式（不要包含 markdown 代码块标记）：
{
  "mode_specific_assessment": "...",
  "top_risks": ["..."],
  "recommended_actions": ["..."],
  "interview_or_delivery_notes": ["..."],
  "confidence": "low|medium|high"
}
"""
    return prompt


async def _call_llm_api(system_prompt: str, user_prompt: str, model: str) -> Dict[str, Any]:
    import httpx

    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    base_url = settings.LLM_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    result = json.loads(content)
    result["llm_reviewer_enabled"] = True
    result["llm_model_used"] = model
    result["llm_profile_used"] = profile.label if (profile := _match_profile(model)) else model
    return result


def _match_profile(model: str) -> Any:
    for mode, profile in LLM_REVIEW_PROFILES.items():
        if _resolve_model(profile.model_env_key) == model:
            return profile
    return None


def _disabled_result() -> Dict[str, Any]:
    return {
        "llm_reviewer_enabled": False,
    }


def _error_result(error_msg: str) -> Dict[str, Any]:
    return {
        "llm_reviewer_enabled": False,
        "llm_error": error_msg,
    }
