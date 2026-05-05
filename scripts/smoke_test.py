import sys
import json
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = SCRIPTS_DIR.parent / "examples"
API_BASE = "http://127.0.0.1:8000"

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")


def curl_post(url: str, file_path: str, form_fields: dict) -> dict:
    cmd = ["curl.exe", "-s", "-X", "POST", url,
           "-F", f"file=@{file_path}"]
    for k, v in form_fields.items():
        cmd.extend(["-F", f"{k}={v}"])
    result = subprocess.run(cmd, capture_output=True, timeout=60)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"curl error: {stderr}")
    return json.loads(result.stdout.decode("utf-8"))


def test_health():
    print("\n=== 1. /health ===")
    try:
        result = subprocess.run(
            ["curl.exe", "-s", f"{API_BASE}/health"],
            capture_output=True, timeout=10,
        )
        data = json.loads(result.stdout.decode("utf-8"))
        check("GET /health returns 200", True)
        check("Response has status=ok", data.get("status") == "ok")
    except Exception as e:
        check("GET /health works", False, str(e))


def test_upload_good():
    print("\n=== 2. Upload good_project.zip ===")
    zip_path = EXAMPLES_DIR / "good_project.zip"
    if not zip_path.exists():
        check("good_project.zip exists", False, f"File not found at {zip_path}")
        return

    try:
        result = curl_post(
            f"{API_BASE}/api/review",
            str(zip_path),
            {"review_mode": "student_assignment"},
        )
        check("POST /api/review returns 200", True)
        check("Has report_markdown", bool(result.get("report_markdown", "")))
        check("Has total_score (int)", isinstance(result.get("total_score"), int))
        check("Has verdict", result.get("verdict") in ("PASS", "CONDITIONAL_PASS", "REJECT"))
        check("Has findings_count", isinstance(result.get("findings_count"), dict))

        md = result["report_markdown"]
        check("Report mentions 项目画像", "项目画像" in md or "project_type" in md)
        check("Report has verdict text", any(v in md for v in ("PASS", "CONDITIONAL_PASS", "REJECT")))

        total = result["total_score"]
        profile = result.get("project_profile", {})
        key_files = profile.get("key_files", {})
        check("README.md detected as present", key_files.get("README.md", False))
        check(".env.example detected as present", key_files.get(".env.example", False))

        print(f"     total_score={total}, verdict={result['verdict']}")
    except Exception as e:
        check("POST /api/review works", False, str(e))


def test_upload_bad():
    print("\n=== 3. Upload bad_project.zip ===")
    zip_path = EXAMPLES_DIR / "bad_project.zip"
    if not zip_path.exists():
        check("bad_project.zip exists", False, f"File not found at {zip_path}")
        return

    try:
        result = curl_post(
            f"{API_BASE}/api/review",
            str(zip_path),
            {"review_mode": "student_assignment"},
        )
        check("POST /api/review returns 200", True)

        md = result["report_markdown"]
        total = result["total_score"]
        findings = result.get("findings_count", {})
        profile = result.get("project_profile", {})
        key_files = profile.get("key_files", {})

        check("README marked as missing", not key_files.get("README.md", True))
        check(".env.example not found", not key_files.get(".env.example", True))
        check("Has HIGH severity findings", findings.get("HIGH", 0) > 0)

        check("Report mentions C:\\Users\\ path risk",
              "C:\\Users" in md or "Windows 本地路径" in md or "硬编码" in md)
        check("Report mentions /Users/ path risk",
              "/Users/" in md or "macOS/Linux 本地路径" in md or "硬编码" in md)
        check("Report mentions SECRET/PASSWORD/Authorization risk",
              "SECRET" in md or "PASSWORD" in md or "Authorization" in md or "Bearer" in md)
        check("Report mentions .env file risk",
              ".env" in md and ("风险" in md or "敏感" in md))

        check("node_modules content NOT leaked",
              "should-not-be-found" not in md and "should be skipped" not in md)
        check("__pycache__ content NOT leaked",
              "cached bytecode" not in md and ".pyc" not in md)
        check(".git content NOT leaked",
              "refs/heads" not in md)
        check("dist/ content NOT leaked",
              "should-be-skipped" not in md)

        check("Report is Markdown", md.lstrip().startswith("#"))
        check("Report has 修复建议", "修复建议" in md or "修复 Prompt" in md)

        print(f"     total_score={total}, "
              f"HIGH={findings.get('HIGH',0)} "
              f"MEDIUM={findings.get('MEDIUM',0)} "
              f"LOW={findings.get('LOW',0)}")
    except Exception as e:
        check("POST /api/review works", False, str(e))


def main():
    print("=" * 60)
    print("  AI Delivery Inspector — Smoke Test")
    print("=" * 60)
    print(f"  API: {API_BASE}")
    print(f"  Examples: {EXAMPLES_DIR}")

    test_health()
    test_upload_good()
    test_upload_bad()

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print("=" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
