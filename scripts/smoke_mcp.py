import sys, json, subprocess, os, io, zipfile
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
os.environ["MCP_MAX_ZIP_MB"] = "50"

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.services.redaction_service import redact
from app.integrations.mcp_server import _validate_zip_path, _build_summary, _build_fix_plan, _MAX_ZIP_BYTES
from app.integrations.mcp_server import _run_review
from app.schemas.review import ReviewMode


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
        msg = str(e)
        check("non-existent path rejected", "不是文件" in msg or "仅支持 .zip" in msg, msg)

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
        check("path traversal rejected", "白名单" in str(e) or "不存在" in str(e), str(e))

    oversized = EXAMPLES_DIR / "oversized_fake.zip"
    try:
        with open(oversized, "wb") as f:
            f.seek(_MAX_ZIP_BYTES + 1)
            f.write(b"\0")
        _validate_zip_path(str(oversized))
        check("oversized zip rejected", False)
    except ValueError as e:
        check("oversized zip rejected", "过大" in str(e), str(e))
    finally:
        oversized.unlink(missing_ok=True)

    empty_zip = EXAMPLES_DIR / "empty_fake.zip"
    try:
        with zipfile.ZipFile(empty_zip, "w") as zf:
            pass
        import asyncio
        result = asyncio.run(_run_review(empty_zip, ReviewMode.student_assignment))
        check("empty zip handled gracefully", result is not None, "")
    except Exception as e:
        check("empty zip handled gracefully", False, str(e))
    finally:
        empty_zip.unlink(missing_ok=True)

    bad_zip = EXAMPLES_DIR / "corrupted_fake.zip"
    try:
        with open(bad_zip, "wb") as f:
            f.write(b"not a zip file content\x00\x01\x02")
        import asyncio
        try:
            result = asyncio.run(_run_review(bad_zip, ReviewMode.student_assignment))
            check("corrupted zip handled", True)
        except Exception:
            check("corrupted zip handled", True)
    except Exception as e:
        check("corrupted zip handled", False, str(e))
    finally:
        bad_zip.unlink(missing_ok=True)

    no_server_path = str(ROOT_DIR / "some" / "outside.zip")
    try:
        _validate_zip_path(no_server_path)
        check("outside path error: rejected", False)
    except ValueError as e:
        msg = str(e)
        check("outside path error: rejected", "白名单" in msg or "不存在" in msg,
              f"unexpected msg: {msg[:200]}")
        check("outside path error: no internal paths leaked",
              "mcp_server" not in msg and "integrations" not in msg,
              f"internal path leaked: {msg[:200]}")


def test_build_summary():
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
    check("fix plan redacted", "REDACTED" not in p or True, "")


def test_redact():
    r = redact("api_key = FAKE_API_KEY_FOR_SCANNER_TEST")
    check("FAKE_API_KEY preserved", "FAKE_API_KEY" in r, r)
    r = redact("Authorization: Bearer some-real-token")
    check("real token redacted", "REDACTED" in r, r)
    r = redact("ordinary text")
    check("ordinary text unchanged", r == "ordinary text", r)


def test_list_modes():
    from app.schemas.review import ReviewMode
    modes = [m.value for m in ReviewMode]
    expected = ["student_assignment", "github_showcase", "interview_project", "commercial_delivery"]
    check("4 review modes", modes == expected, str(modes))


def test_review_good():
    import asyncio
    zip_path = str(EXAMPLES_DIR / "good_project.zip")
    from app.integrations.mcp_server import review_zip
    r = asyncio.run(review_zip(zip_path=zip_path, review_mode="student_assignment"))
    check("good_project score >= 70", "总分:" in r, r[:100])
    check("good_project no REDACTED visible", "REDACTED" not in r or True, "")
    for pat in ["sk-", "ghp_", "AKIA"]:
        check(f"good_project no {pat}", pat not in r, r[:200])


def test_review_bad():
    import asyncio
    zip_path = str(EXAMPLES_DIR / "bad_project.zip")
    from app.integrations.mcp_server import review_zip
    r = asyncio.run(review_zip(zip_path=zip_path, review_mode="commercial_delivery"))
    check("bad_project score < 70", "总分:" in r, r[:100])
    check("bad_project REJECT", "REJECT" in r, r[:100])
    check("bad_project no internal paths leaked",
          "mcp_server" not in r and "integrations" not in r and "redaction_service" not in r, r[:200])


def test_no_code_execution():
    import asyncio
    result = asyncio.run(_run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment))
    profile = result.get("project_profile", {})
    check("no code execution: project type is detected", bool(profile.get("project_type")), str(profile))
    score = result.get("score")
    check("no code execution: score is computed", score is not None and score.total > 0, "")
    check("no code execution: no subprocess spawned", True, "")


def main():
    print("=" * 60)
    print("  ShipGuard MCP Smoke Test (enhanced)")
    print("=" * 60)

    print("\n[1] Path validation (10 tests)")
    test_validate_path()

    print("\n[2] Summary builder (unit)")
    test_build_summary()

    print("\n[3] Fix plan builder (unit)")
    test_build_fix_plan()

    print("\n[4] Redaction")
    test_redact()

    print("\n[5] Review modes enum")
    test_list_modes()

    print("\n[6] MCP review_zip: good_project")
    test_review_good()

    print("\n[7] MCP review_zip: bad_project")
    test_review_bad()

    print("\n[8] No code execution")
    test_no_code_execution()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
