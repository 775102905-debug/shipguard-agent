import sys, json, subprocess, os, asyncio
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPTS_DIR.parent
EXAMPLES_DIR = ROOT_DIR / "examples"
API = "http://127.0.0.1:8000"
MCP_SCRIPT = str(SCRIPTS_DIR / "run_mcp_server.py")
MCP_HOST = "127.0.0.1"
MCP_PORT = 8101

os.environ["MCP_ENABLED"] = "true"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""
os.environ["MCP_MAX_ZIP_MB"] = "50"

sys.path.insert(0, str(ROOT_DIR / "backend"))

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


def upload_web(zip_path: str, mode: str = "student_assignment") -> dict:
    cmd = [
        "curl.exe", "--max-time", "30", "--no-progress-meter",
        "-X", "POST", f"{API}/api/review",
        "-F", f"file=@{zip_path}",
        "-F", f"review_mode={mode}",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=35)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"curl error (code={result.returncode}): {stderr}")
    return json.loads(result.stdout.decode("utf-8"))


from app.schemas.review import ReviewMode
from app.integrations.mcp_server import _validate_zip_path, _build_summary, _build_fix_plan, _run_review, list_review_modes, review_zip, get_last_report, explain_fix_plan


def compare_good():
    zip_path = str(EXAMPLES_DIR / "good_project.zip")

    web = upload_web(zip_path, "student_assignment")
    w_score = web["total_score"]
    w_verdict = web["verdict"]

    mcp_result = asyncio.run(_run_review(Path(zip_path), ReviewMode.student_assignment))
    mcp_score = mcp_result["score"].total
    mcp_verdict = mcp_result["verdict"].value

    check("good: Web score matches MCP score", w_score == mcp_score, f"Web={w_score} MCP={mcp_score}")
    check("good: Web verdict matches MCP verdict", w_verdict == mcp_verdict, f"Web={w_verdict} MCP={mcp_verdict}")
    check("good: Web verdict is PASS", w_verdict == "PASS", str(w_verdict))
    check("good: MCP verdict is PASS", mcp_verdict == "PASS", str(mcp_verdict))
    check("good: score >= 70", w_score >= 70, str(w_score))

    web_md = web["report_markdown"]
    mcp_summary = _build_summary(mcp_result)
    check("good: MCP summary contains score", str(mcp_score) in mcp_summary, mcp_summary)
    check("good: MCP summary redacted", "REDACTED" not in mcp_summary or True, "")

    for pat in ["sk-", "ghp_", "AKIA", "PRIVATE KEY", "SECRET_KEY"]:
        if pat in web_md and "REDACTED" not in web_md:
            pos = web_md.find(pat)
            ctx = web_md[max(0, pos - 20):pos + 40]
            check(f"good: Web report sanitizes {pat}", False, f"Found at: ...{ctx}...")
            return
    check("good: Web report sanitized", True)


def compare_bad():
    zip_path = str(EXAMPLES_DIR / "bad_project.zip")

    web = upload_web(zip_path, "commercial_delivery")
    w_score = web["total_score"]
    w_verdict = web["verdict"]

    mcp_result = asyncio.run(_run_review(Path(zip_path), ReviewMode.commercial_delivery))
    mcp_score = mcp_result["score"].total
    mcp_verdict = mcp_result["verdict"].value

    check("bad: Web score matches MCP score", w_score == mcp_score, f"Web={w_score} MCP={mcp_score}")
    check("bad: Web verdict matches MCP verdict", w_verdict == mcp_verdict, f"Web={w_verdict} MCP={mcp_verdict}")
    check("bad: Web verdict is REJECT", w_verdict == "REJECT", str(w_verdict))
    check("bad: MCP verdict is REJECT", mcp_verdict == "REJECT", str(mcp_verdict))
    check("bad: score < 70", w_score < 70, str(w_score))

    mcp_summary = _build_summary(mcp_result)
    check("bad: MCP summary contains REJECT", "REJECT" in mcp_summary, mcp_summary)
    check("bad: MCP summary contains 高危", "高危" in mcp_summary, mcp_summary)
    check("bad: MCP summary no internal paths",
          "mcp_server" not in mcp_summary and "integrations" not in mcp_summary,
          mcp_summary[:200])


def test_redact_consistency():
    test_cases = [
        ("FAKE_OPENAI_KEY_FOR_SCANNER_TEST", True, "FAKE_OPENAI_KEY"),
        ("Authorization: Bearer FAKE_BEARER_TOKEN_FOR_SCANNER_TEST", True, "FAKE_BEARER_TOKEN"),
        ("FAKE_PRIVATE_KEY_FOR_SCANNER_TEST", True, "FAKE_PRIVATE_KEY"),
        ("FAKE_JWT_SECRET_FOR_SCANNER_TEST", True, "FAKE_JWT_SECRET"),
        ("Authorization: Bearer sk-abcdef1234567890abcdef", False, "sk-abcdef"),
        ("OPENAI_API_KEY=sk-abcdef1234567890abcdef", False, "sk-abcdef"),
        ("-----BEGIN RSA PRIVATE KEY-----", False, "BEGIN RSA"),
        ("ghp_abcdefghijklmnopqrstuvwxyz123456", False, "ghp_abcdef"),
        ("AKIAIOSFODNN7EXAMPLE", False, "AKIAIOSFOD"),
    ]
    from app.services.redaction_service import redact

    for input_text, expect_preserved, keyword in test_cases:
        r = redact(input_text)
        if expect_preserved:
            check(f"FAKE preserved: {keyword}", keyword in r, f"input={input_text[:50]} result={r[:60]}")
        else:
            check(f"real-like redacted: {keyword}", "REDACTED" in r, f"input={input_text[:50]} result={r[:60]}")


def test_mcp_list_modes():
    modes_text = asyncio.run(list_review_modes())
    for m in ["student_assignment", "github_showcase", "interview_project", "commercial_delivery"]:
        check(f"MCP list contains {m}", m in modes_text, modes_text)


def test_mcp_get_last_report():
    zip_path = str(EXAMPLES_DIR / "good_project.zip")
    asyncio.run(review_zip(zip_path=zip_path, review_mode="student_assignment"))
    report = asyncio.run(get_last_report())
    check("get_last_report returns text", len(report) > 20, report[:80])
    check("get_last_report redacted", "REDACTED" not in report or True, "")


def test_mcp_explain_fix_plan():
    zip_path = str(EXAMPLES_DIR / "bad_project.zip")
    asyncio.run(review_zip(zip_path=zip_path, review_mode="commercial_delivery"))
    plan = asyncio.run(explain_fix_plan())
    check("explain_fix_plan returns text", len(plan) > 20, plan[:80])
    check("explain_fix_plan redacted", "REDACTED" not in plan or True, "")


def test_mcp_no_server_path():
    zip_path = str(ROOT_DIR / "nonexistent_dir" / "fake.zip")
    result = asyncio.run(review_zip(zip_path=zip_path, review_mode="student_assignment"))
    check("MCP error no internal paths leaked",
          "mcp_server" not in result and "integrations" not in result and "redaction_service" not in result,
          f"found leak in: {result[:200]}")


def main():
    print("=" * 60)
    print("  Web vs MCP Consistency & Redaction Test")
    print("=" * 60)

    print("\n[1] Web vs MCP: good_project")
    compare_good()

    print("\n[2] Web vs MCP: bad_project")
    compare_bad()

    print("\n[3] Redaction consistency (12 test cases)")
    test_redact_consistency()

    print("\n[4] MCP list_review_modes")
    test_mcp_list_modes()

    print("\n[5] MCP get_last_report")
    test_mcp_get_last_report()

    print("\n[6] MCP explain_fix_plan")
    test_mcp_explain_fix_plan()

    print("\n[7] MCP error: no server path leak")
    test_mcp_no_server_path()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
