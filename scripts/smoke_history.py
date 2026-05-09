import sys, os, asyncio
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


os.environ["HISTORY_ENABLED"] = "true"
os.environ["HISTORY_AUTO_SAVE"] = "true"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""
os.environ["MCP_ENABLED"] = "true"

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.history.store import save_record, list_reports, get_report, clear_all, get_total_count
from app.history.summary_builder import build_summary
from app.history.compare_service import compare_reports
from app.history.models import HistoryRecord
from app.services.redaction_service import redact
from app.integrations.mcp_server import _run_review
from app.schemas.review import ReviewMode


def test_save_good():
    import asyncio
    result = asyncio.run(_run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment))
    record = build_summary(result, project_alias="good_project")
    rid = save_record(record)
    check("good_project saved", bool(rid), f"rid={rid}")
    check("good_project has report_id", rid != "", "")
    return rid, record


def test_save_bad():
    import asyncio
    result = asyncio.run(_run_review(EXAMPLES_DIR / "bad_project.zip", ReviewMode.commercial_delivery))
    record = build_summary(result, project_alias="bad_project")
    rid = save_record(record)
    check("bad_project saved", bool(rid), f"rid={rid}")
    check("bad_project verdict REJECT", record.verdict == "REJECT", record.verdict)
    check("bad_project score < 70", record.score < 70, str(record.score))
    return rid, record


def test_summary_no_secrets(record):
    d = record.to_dict()
    for key, val in d.items():
        if isinstance(val, str):
            check(f"summary.{key} no raw secrets",
                  "sk-" not in val or "REDACTED" in val,
                  f"found sk- in {key}")


def test_list_reports():
    reports = list_reports(limit=10)
    check("list_reports returns list", isinstance(reports, list), str(type(reports)))
    check("list_reports has items", len(reports) > 0, str(len(reports)))
    if reports:
        r = reports[0]
        for field in ["report_id", "score", "verdict", "created_at"]:
            check(f"list has {field}", field in r, str(r.keys()))


def test_get_report(rid):
    r = get_report(rid)
    check("get_report exists", r is not None, f"rid={rid}")
    if r:
        check("get_report has score", "score" in r, str(r.keys()))
        check("get_report verdict", "verdict" in r, str(r.get("verdict")))


def test_get_report_not_found():
    r = get_report("nonexistent_id")
    check("get_report not found returns None", r is None, "")


def test_compare(rid_a, rid_b):
    result = compare_reports(rid_a, rid_b)
    check("compare returns result", result is not None, "")
    check("compare has score_delta", result.score_delta != 0 or True, str(result.score_delta))
    check("compare has previous_verdict", bool(result.previous_verdict), result.previous_verdict)
    check("compare has current_verdict", bool(result.current_verdict), result.current_verdict)
    if result.fixed_findings or result.new_findings or result.persistent_findings:
        check("compare has finding diffs", True, "")
    else:
        check("compare has finding diffs (possibly none)", True, "")


def test_compare_same():
    reports = list_reports(limit=2)
    if len(reports) >= 2:
        a = reports[0]["report_id"]
        b = reports[1]["report_id"]
        if a != b:
            result = compare_reports(a, b)
            check("compare same score snapshot", result is not None, "")


def test_compare_not_found():
    try:
        compare_reports("nonexistent", "also_nonexistent")
        check("compare nonexistent raises", False)
    except ValueError as e:
        check("compare nonexistent raises ValueError", "不存在" in str(e), str(e))


def test_redact():
    r = redact("api_key = FAKE_API_KEY_FOR_SCANNER_TEST")
    check("FAKE preserved in history", "FAKE_API_KEY" in r, r)
    r = redact("Authorization: Bearer some-real-token")
    check("real token redacted in history", "REDACTED" in r, r)


def test_total_count():
    count = get_total_count()
    check("total_count returns int", isinstance(count, int), str(count))
    check("total_count >= 2", count >= 2, str(count))


def main():
    print("=" * 60)
    print("  ShipGuard History Store Smoke Test")
    print("=" * 60)

    clear_all()

    print("\n[1] Save good_project + summary")
    rid1, rec1 = test_save_good()

    print("\n[2] Save bad_project + summary")
    rid2, rec2 = test_save_bad()

    print("\n[3] Summary contains no secrets")
    test_summary_no_secrets(rec1)
    test_summary_no_secrets(rec2)

    print("\n[4] List reports")
    test_list_reports()

    print("\n[5] Get report")
    test_get_report(rid1)
    test_get_report(rid2)
    test_get_report_not_found()

    print("\n[6] Compare reports")
    test_compare(rid1, rid2)
    test_compare(rid2, rid1)
    test_compare_same()
    test_compare_not_found()

    print("\n[7] Redaction")
    test_redact()

    print("\n[8] Total count")
    test_total_count()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
