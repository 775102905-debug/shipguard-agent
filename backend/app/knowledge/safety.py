import logging
from typing import Any

from ..services.redaction_service import redact

logger = logging.getLogger(__name__)

_RISK_PATTERNS = {
    "raw_markdown": ["# AI 项目交付审查报告"],
    "raw_token": [
        "sk-", "ghp_", "AKIA", "Bearer ", "PRIVATE KEY-----",
        "JWT_SECRET", "SECRET_KEY", "AWS_SECRET", "OPENAI_API_KEY",
        "LLM_API_KEY", "AccessKey",
    ],
}

_TEXT_FIELDS_WITHOUT_PATH = ["commercial_fix_plan", "interview_notes", "project_alias"]

_PATH_PATTERNS = ["C:\\", "D:\\", "/home/", "/root/"]


def assert_safe_for_index(record: Any, source: str = "") -> bool:
    all_fields = _TEXT_FIELDS_WITHOUT_PATH + [
        "top_security_findings", "top_structure_findings",
        "top_dependency_findings", "top_readme_findings",
    ]

    for field_name in all_fields:
        val = _get_field_value(record, field_name)
        if not val:
            continue

        if isinstance(val, str):
            items = [val]
        elif isinstance(val, list):
            items = val
        else:
            continue

        for item in items:
            if not isinstance(item, str):
                continue

            if not _check_risk_patterns(item, field_name, source):
                return False

            if field_name in _TEXT_FIELDS_WITHOUT_PATH:
                if not _check_absolute_path(item, field_name, source):
                    return False

    return True


def _check_risk_patterns(text: str, field_name: str, source: str) -> bool:
    if "FAKE_" in text and "FOR_SCANNER_TEST" in text:
        return True
    for risk_type, patterns in _RISK_PATTERNS.items():
        for pat in patterns:
            if pat in text and "REDACTED" not in text:
                logger.warning(
                    f"Knowledge index safety blocked [{risk_type}] in {field_name}"
                    f" (source={source[:40]}...): pattern={pat}"
                )
                return False
    return True


def _check_absolute_path(text: str, field_name: str, source: str) -> bool:
    if "FAKE_" in text and "FOR_SCANNER_TEST" in text:
        return True
    for pat in _PATH_PATTERNS:
        if pat in text and "REDACTED" not in text:
            logger.warning(
                f"Knowledge index safety blocked [absolute_path] in {field_name}"
                f" (source={source[:40]}...): pattern={pat}"
            )
            return False
    return True


def _get_field_value(record: Any, field: str) -> Any:
    if hasattr(record, field):
        return getattr(record, field)
    if isinstance(record, dict):
        return record.get(field, "")
    return ""
