import re
from typing import List, Tuple

PatternReplacement = Tuple[re.Pattern, str]

_REDACT_PATTERNS: List[PatternReplacement] = []


def _p(pattern: str, placeholder: str) -> None:
    _REDACT_PATTERNS.append((re.compile(pattern, re.IGNORECASE), placeholder))


_p(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(authorization)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(bearer)\s+\S+", r"\1 ****REDACTED****")
_p(r"(?i)(token)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(secret[_-]?key|secret)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(password|passwd)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(private[_-]?key)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(ssh[_-]?key)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(jwt[_-]?secret)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(access[_-]?key)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(aws[_-]?secret)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(openai[_-]?api[_-]?key)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")
_p(r"(?i)(llm[_-]?api[_-]?key)\s*[:=]\s*['\"]?\S+['\"]?", r"\1: ****REDACTED****")

_p(r"(?i)(-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----)", r"-----****REDACTED****")
_p(r"(?i)(-----END\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----)", r"-----****REDACTED****")

_p(r"\b(sk-[A-Za-z0-9_-]{10,})\b", r"sk-****REDACTED****")
_p(r"\b(ghp_[A-Za-z0-9_-]{10,})\b", r"ghp-****REDACTED****")
_p(r"\b(AKIA[A-Z0-9]{16,})\b", r"AKIA****REDACTED****")


_FAKE_LINE_PROTECT = re.compile(
    r"^.*(FAKE_[A-Z_]+|replace_with_your_|your_api_key_here|your_openai_api_key_here|example_secret).*$",
    re.IGNORECASE | re.MULTILINE,
)


def redact(text: str) -> str:
    placeholders = {}
    idx = 0

    def _protect(m: re.Match) -> str:
        nonlocal idx
        key = f"__PH{idx}__"
        placeholders[key] = m.group(0)
        idx += 1
        return key

    text = _FAKE_LINE_PROTECT.sub(_protect, text)

    result = text
    for pattern, replacement in _REDACT_PATTERNS:
        result = pattern.sub(replacement, result)

    for key, val in placeholders.items():
        result = result.replace(key, val)

    return result


def redact_report_markdown(report_md: str) -> str:
    return redact(report_md)
