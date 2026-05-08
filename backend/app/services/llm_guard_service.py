import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(authorization|bearer)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(secret|secret[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(password|passwd)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(jwt[_-]?secret|access[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"\b(sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[A-Z0-9]{16,})\b"),
]

INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(ignore\s+(all\s+)?(previous|above|below)\s+instructions)"),
    re.compile(r"(?i)(forget|disregard|ignore)\s+(all\s+)?(rules|instructions|prompts?)"),
    re.compile(r"(?i)(直接给\s*(PASS|通过|满分)|不要(审查|检查|扫描))"),
    re.compile(r"(?i)(say\s+\"PASS\"|always\s+(pass|accept)|无条件通过)"),
]


def scan_input(text: str) -> Dict[str, Any]:
    findings = []
    risk_level = "low"

    for pattern in INJECTION_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            findings.append({
                "type": "prompt_injection",
                "pattern": pattern.pattern,
                "match_count": len(matches),
                "severity": "HIGH",
            })
            risk_level = "high"

    for pattern in SENSITIVE_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            findings.append({
                "type": "sensitive_data_in_input",
                "pattern": pattern.pattern,
                "match_count": len(matches),
                "severity": "HIGH",
            })
            if risk_level != "high":
                risk_level = "medium"

    token_count = len(text.split())
    if token_count > 3000:
        findings.append({
            "type": "token_length_warning",
            "pattern": "token_count",
            "match_count": token_count,
            "severity": "LOW",
        })

    return {
        "scanned": True,
        "risk_level": risk_level,
        "findings": findings,
        "blocked": risk_level == "high",
    }


def scan_output(text: str) -> Dict[str, Any]:
    findings = []
    risk_level = "low"

    for pattern in SENSITIVE_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            findings.append({
                "type": "sensitive_data_leak",
                "pattern": pattern.pattern,
                "match_count": len(matches),
                "severity": "HIGH",
            })
            risk_level = "high"

    return {
        "scanned": True,
        "risk_level": risk_level,
        "findings": findings,
    }
