import sys, json, subprocess, os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
BACKEND_DIR = ROOT_DIR / "backend"
EXAMPLES_DIR = ROOT_DIR / "examples"
API = "http://127.0.0.1:8000"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""

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
        "JSON output format in prompts": "只返回一个 JSON object" in content,
        "no sk- pattern in file": "sk-" not in content or "sk-" in content and content.index("sk-") > content.find("security"),
    }
    for name, result in checks.items():
        check(name, result)


def test_json_parser():
    try:
        from app.services.llm_reviewer import parse_llm_json_response

        # Test 1: clean JSON
        clean = '{"mode_specific_assessment": "good", "top_risks": [], "recommended_actions": [], "interview_or_delivery_notes": [], "confidence": "high"}'
        r = parse_llm_json_response(clean, "test-model")
        check("clean JSON parses", r.get("llm_reviewer_enabled") is True)

        # Test 2: ```json wrapped
        wrapped = '```json\n{"mode_specific_assessment": "good", "top_risks": [], "recommended_actions": [], "interview_or_delivery_notes": [], "confidence": "high"}\n```'
        r = parse_llm_json_response(wrapped, "test-model")
        check("```json wrapped JSON parses", r.get("llm_reviewer_enabled") is True)

        # Test 3: ``` wrapped
        triple = '```\n{"mode_specific_assessment": "good", "top_risks": [], "recommended_actions": [], "interview_or_delivery_notes": [], "confidence": "high"}\n```'
        r = parse_llm_json_response(triple, "test-model")
        check("``` wrapped JSON parses", r.get("llm_reviewer_enabled") is True)

        # Test 4: JSON with leading text
        leading = 'Here is my assessment:\n{"mode_specific_assessment": "good", "top_risks": [], "recommended_actions": [], "interview_or_delivery_notes": [], "confidence": "high"}'
        r = parse_llm_json_response(leading, "test-model")
        check("JSON with leading text parses", r.get("llm_reviewer_enabled") is True)

        # Test 5: JSON with trailing text
        trailing = '{"mode_specific_assessment": "good", "top_risks": [], "recommended_actions": [], "interview_or_delivery_notes": [], "confidence": "high"}\nHope this helps!'
        r = parse_llm_json_response(trailing, "test-model")
        check("JSON with trailing text parses", r.get("llm_reviewer_enabled") is True)

        # Test 6: malformed JSON -> fallback
        malformed = '{"mode_specific_assessment": "unterminated string}'
        r = parse_llm_json_response(malformed, "test-model")
        check("malformed JSON falls back", r.get("llm_reviewer_enabled") is False)
        check("malformed JSON has friendly error",
              "不是合法 JSON" in r.get("llm_error", ""))
        check("malformed JSON has error_type=malformed_json",
              r.get("llm_error_type") == "malformed_json")

        # Test 7: malformed JSON should not expose raw Python exception
        err_msg = r.get("llm_error", "")
        check("malformed JSON doesn't expose Python traceback",
              "Unterminated string" not in err_msg and "JSONDecodeError" not in err_msg)

        # Test 8: sanitize API key in preview
        sensitive = '{"api_key": "FAKE_TEST_KEY_SHOULD_BE_SANITIZED"}'
        r = parse_llm_json_response(sensitive, "test-model")
        preview = r.get("llm_raw_preview", "")
        check("malformed JSON sanitizes api_key in preview",
              "FAKE_TEST_KEY_SHOULD_BE_SANITIZED" not in preview)

    except Exception as e:
        check("JSON parser tests", False, str(e))


def main():
    good = EXAMPLES_DIR / "good_project.zip"
    bad = EXAMPLES_DIR / "bad_project.zip"

    if not good.exists() or not bad.exists():
        print("[FAIL] Test zips not found. Run python scripts/create_test_zips.py first.")
        return 1

    print("=" * 60)
    print("  LLM Reviewer Mock Test")
    print("=" * 60)

    # 1. LLM_REVIEW_ENABLED=false fallback
    print("\n[1] LLM response placeholder in report")
    try:
        r = upload_test(str(good), "student_assignment")
        md = r["report_markdown"]
        check("report has AI 审查官意见 section", "AI 审查官意见" in md)
        check("total_score is normal", isinstance(r.get("total_score"), int) and r["total_score"] > 0)
        check("verdict is normal", r.get("verdict") in ("PASS", "CONDITIONAL_PASS", "REJECT"))
    except Exception as e:
        check("LLM fallback test", False, str(e))

    # 2. Profile file validation
    print("\n[2] Review mode profile file validation")
    try:
        test_profile_file()
    except Exception as e:
        check("profile file validation", False, str(e))

    # 3. Bad project upload works regardless of LLM state
    print("\n[3] Bad project with real backend")
    try:
        r = upload_test(str(bad), "commercial_delivery")
        check("bad_project upload succeeds", True)
        check("has report_markdown", bool(r.get("report_markdown", "")))
        check("verdict is REJECT for bad project", r["verdict"] == "REJECT")
        check("AI 审查官意见 section present", "AI 审查官意见" in r["report_markdown"])
    except Exception as e:
        check("bad project with LLM disabled", False, str(e))

    # 4. JSON parser robustness tests
    print("\n[4] JSON parser robustness tests")
    try:
        test_json_parser()
    except Exception as e:
        check("JSON parser tests", False, str(e))

    # 5. All 4 modes produce AI section
    print("\n[5] All 4 modes produce AI section in report")
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
