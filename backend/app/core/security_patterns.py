import re
from dataclasses import dataclass
from typing import List


@dataclass
class SecurityPattern:
    name: str
    pattern: re.Pattern
    severity: str
    description: str


SECURITY_PATTERNS: List[SecurityPattern] = [
    SecurityPattern(
        name="OpenAI API Key (sk-)",
        pattern=re.compile(r'sk-[A-Za-z0-9]{20,}'),
        severity="HIGH",
        description="检测到疑似 OpenAI API 密钥 (sk-...)",
    ),
    SecurityPattern(
        name="GitHub Personal Access Token (ghp_)",
        pattern=re.compile(r'ghp_[A-Za-z0-9]{36,}'),
        severity="HIGH",
        description="检测到疑似 GitHub Personal Access Token (ghp_)",
    ),
    SecurityPattern(
        name="AWS Access Key (AKIA)",
        pattern=re.compile(r'AKIA[0-9A-Z]{16}'),
        severity="HIGH",
        description="检测到疑似 AWS Access Key ID (AKIA...)",
    ),
    SecurityPattern(
        name="Generic SECRET",
        pattern=re.compile(r'(SECRET|secret|SECRET_KEY|secret_key)\s*[=:]\s*["\']?.+["\']?', re.IGNORECASE),
        severity="MEDIUM",
        description="检测到疑似密钥变量赋值 (SECRET/secret)",
    ),
    SecurityPattern(
        name="Generic PASSWORD",
        pattern=re.compile(r'(PASSWORD|password|PASSWD|passwd)\s*[=:]\s*["\']?.+["\']?', re.IGNORECASE),
        severity="MEDIUM",
        description="检测到疑似密码变量赋值 (PASSWORD/password)",
    ),
    SecurityPattern(
        name="Bearer Token",
        pattern=re.compile(r'(Bearer\s+[A-Za-z0-9\-._~+/]+=*)'),
        severity="MEDIUM",
        description="检测到疑似 Bearer Token",
    ),
    SecurityPattern(
        name="Authorization Header",
        pattern=re.compile(r'Authorization\s*[=:]\s*["\']?.+["\']?', re.IGNORECASE),
        severity="MEDIUM",
        description="检测到 Authorization 头信息",
    ),
    SecurityPattern(
        name="Windows Local Path (C:\\Users\\)",
        pattern=re.compile(r'C:\\Users\\'),
        severity="MEDIUM",
        description="检测到硬编码的 Windows 本地路径 (C:\\Users\\)",
    ),
    SecurityPattern(
        name="macOS/Linux Local Path (/Users/)",
        pattern=re.compile(r'/Users/'),
        severity="MEDIUM",
        description="检测到硬编码的 macOS/Linux 本地路径 (/Users/)",
    ),
    SecurityPattern(
        name="Debug Mode Enabled (debug=True)",
        pattern=re.compile(r'debug\s*=\s*True', re.IGNORECASE),
        severity="LOW",
        description="检测到 debug=True 开启，生产环境应关闭",
    ),
    SecurityPattern(
        name="DEBUG Mode Enabled (DEBUG=True)",
        pattern=re.compile(r'DEBUG\s*=\s*True', re.IGNORECASE),
        severity="LOW",
        description="检测到 DEBUG=True 开启，生产环境应关闭",
    ),
    SecurityPattern(
        name="CORS Wildcard (*)",
        pattern=re.compile(r'cors.*\*|allow_origins\s*=\s*["\']\*["\']', re.IGNORECASE),
        severity="LOW",
        description="检测到 CORS 配置为通配符 *，生产环境应限制具体域名",
    ),
]
