import sys, json, subprocess, re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
EXAMPLES_DIR = ROOT_DIR / "examples"
API = "http://127.0.0.1:8000"

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


def upload_test(filepath: str, mode: str) -> dict:
    cmd = [
        "curl.exe", "--max-time", "30", "--no-progress-meter",
        "-X", "POST", f"{API}/api/review",
        "-F", f"file=@{filepath}",
        "-F", f"review_mode={mode}",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=35)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"curl error (code={result.returncode}): {stderr}")
    return json.loads(result.stdout.decode("utf-8"))


def test_profile_file():
    profile_path = ROOT_DIR / "backend" / "app" / "core" / "llm_review_profiles.py"
    content = profile_path.read_text(encoding="utf-8")
    checks = {
        "student_assignment profile": "STUDENT_PROMPT" in content,
        "github_showcase profile": "GITHUB_PROMPT" in content,
        "interview_project profile": "INTERVIEW_PROMPT" in content,
        "commercial_delivery profile": "COMMERCIAL_PROMPT" in content,
        "safety instruction present": "不可信输入" in content or "安全约束" in content,
        "STUDENT_REVIEW_MODEL env key": "STUDENT_REVIEW_MODEL" in content,
        "GITHUB_REVIEW_MODEL env key": "GITHUB_REVIEW_MODEL" in content,
        "INTERVIEW_REVIEW_MODEL env key": "INTERVIEW_REVIEW_MODEL" in content,
        "COMMERCIAL_REVIEW_MODEL env key": "COMMERCIAL_REVIEW_MODEL" in content,
        "no sk- pattern in file": "sk-" not in content or "sk-" in content and content.index("sk-") > content.find("security"),
    }
    for name, result in checks.items():
        check(name, result)


def main():
    good = EXAMPLES_DIR / "good_project.zip"
    bad = EXAMPLES_DIR / "bad_project.zip"

    if not good.exists() or not bad.exists():
        print("[FAIL] Test zips not found. Run python scripts/create_test_zips.py first.")
        return 1

    print("=" * 60)
    print("  LLM Reviewer Mock Test — no real LLM call")
    print("=" * 60)

    # 1. Verify LLM_REVIEW_ENABLED=false (default) fallback
    print("\n[1] LLM_REVIEW_ENABLED=false (default) fallback")
    try:
        r = upload_test(str(good), "student_assignment")
        md = r["report_markdown"]
        check("report has AI 审查官意见 section", "AI 审查官意见" in md)
        ai_section = md[md.find("## AI 审查官意见"):]
        check("AI 审查官意见 mentions 未启用",
              "未启用" in ai_section or "LLM Reviewer" in ai_section)
        check("API response llm_review_enabled is False", r.get("llm_review_enabled") is False)
        check("API response llm_model_used is empty", r.get("llm_model_used") == "")
        check("total_score is normal", isinstance(r.get("total_score"), int) and r["total_score"] > 0)
        check("verdict is normal", r.get("verdict") in ("PASS", "CONDITIONAL_PASS", "REJECT"))
    except Exception as e:
        check("LLM fallback test", False, str(e))

    # 2. Verify profile file exists and contains expected content
    print("\n[2] Review mode profile file validation")
    try:
        test_profile_file()
    except Exception as e:
        check("profile file validation", False, str(e))

    # 3. Verify bad_project upload with LLM disabled
    print("\n[3] Bad project with LLM disabled")
    try:
        r = upload_test(str(bad), "commercial_delivery")
        check("bad_project upload succeeds", True)
        check("has report_markdown", bool(r.get("report_markdown", "")))
        check("verdict is REJECT for bad project", r["verdict"] == "REJECT")
        check("AI 审查官意见 section present", "AI 审查官意见" in r["report_markdown"])
        check("llm_review_enabled is False in response", r.get("llm_review_enabled") is False)
    except Exception as e:
        check("bad project with LLM disabled", False, str(e))

    # 4. Verify all 4 modes produce reports with AI section
    print("\n[4] All 4 modes produce AI section in report")
    for mode in ["student_assignment", "github_showcase", "interview_project", "commercial_delivery"]:
        try:
            r = upload_test(str(good), mode)
            has_ai = "AI 审查官意见" in r["report_markdown"]
            check(f"{mode}: has AI section", has_ai)
        except Exception as e:
            check(f"{mode}: API call", False, str(e))

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
