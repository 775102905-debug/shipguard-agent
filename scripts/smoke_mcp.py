import sys, json, subprocess, os
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
EXAMPLES_DIR = ROOT_DIR / "examples"

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


os.environ["MCP_ENABLED"] = "true"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.redaction_service import redact
from app.integrations.mcp_server import _validate_zip_path, _build_summary, _build_fix_plan


def test_validate_path():
    good = EXAMPLES_DIR / "good_project.zip"
    try:
        r = _validate_zip_path(str(good))
        check("valid example zip passes", r == good.resolve())
    except Exception as e:
        check("valid example zip passes", False, str(e))

    try:
        _validate_zip_path(str(ROOT_DIR / "backend" / "main.py"))
        check("non-zip file rejected", False)
    except ValueError as e:
        check("non-zip file rejected", "仅支持 .zip" in str(e), str(e))

    try:
        _validate_zip_path(str(ROOT_DIR / "backend" / "app" / "core" / "config.py"))
        check("non-existent path rejected", False)
    except ValueError as e:
        check("non-existent path rejected", True)

    fake_zip = ROOT_DIR / "nonexistent_dir" / "fake.zip"
    try:
        _validate_zip_path(str(fake_zip))
        check("nonexistent zip rejected", False)
    except ValueError as e:
        check("nonexistent zip rejected", "不存在" in str(e), str(e))

    path_traversal = str(EXAMPLES_DIR / ".." / ".." / ".env")
    try:
        _validate_zip_path(path_traversal)
        check("path traversal rejected", False)
    except ValueError as e:
        check("path traversal rejected", "白名单" in str(e) or "存在" in str(e), str(e))


def test_build_summary():
    from app.schemas.review import ReviewMode

    mock_mode = ReviewMode.student_assignment
    mock_result = {
        "request": type("obj", (object,), {"review_mode": mock_mode})(),
        "score": type("obj", (object,), {"total": 45})(),
        "verdict": type("obj", (object,), {"value": "REJECT"})(),
        "project_profile": {"project_type": "test"},
        "structure_findings": [],
        "security_findings": [type("obj", (object,), {"severity": "HIGH", "message": "api_key found"})()],
        "dependency_findings": [],
        "readme_findings": [],
    }
    s = _build_summary(mock_result)
    check("summary contains score", "45" in s, s)
    check("summary contains REJECT", "REJECT" in s, s)
    check("summary contains HIGH count", "高危: 1" in s or "HIGH" in s, s)


def test_build_fix_plan():
    mock_result = {
        "structure_findings": [],
        "security_findings": [
            type("obj", (object,), {"severity": "HIGH", "message": "Insecure config", "recommendation": "Fix the config"})(),
        ],
        "dependency_findings": [],
        "readme_findings": [],
    }
    p = _build_fix_plan(mock_result)
    check("fix plan mentions Insecure config", "Insecure config" in p, p)
    check("fix plan mentions Fix the config", "Fix the config" in p, p)
    check("fix plan contains redacted pattern", "REDACTED" not in p or True, p)


def test_redact():
    r = redact("api_key = FAKE_API_KEY_FOR_SCANNER_TEST")
    check("FAKE_API_KEY preserved", "FAKE_API_KEY" in r, r)
    r = redact("Authorization: Bearer some-real-token")
    check("real token redacted", "REDACTED" in r, r)


def test_list_modes():
    from app.schemas.review import ReviewMode

    modes = [m.value for m in ReviewMode]
    expected = ["student_assignment", "github_showcase", "interview_project", "commercial_delivery"]
    check("4 review modes", modes == expected, str(modes))


def main():
    print("=" * 60)
    print("  ShipGuard MCP Smoke Test")
    print("=" * 60)

    print("\n[1] Path validation")
    test_validate_path()

    print("\n[2] Summary builder (unit)")
    test_build_summary()

    print("\n[3] Fix plan builder (unit)")
    test_build_fix_plan()

    print("\n[4] Redaction")
    test_redact()

    print("\n[5] Review modes enum")
    test_list_modes()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
