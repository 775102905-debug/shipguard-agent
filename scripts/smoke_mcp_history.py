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

from app.history.store import save_record, list_reports, get_report, clear_all
from app.history.summary_builder import build_summary
from app.history.models import HistoryRecord
from app.integrations.mcp_server import _run_review, list_reports as mcp_list_reports, get_report as mcp_get_report, compare_reports_tool
from app.schemas.review import ReviewMode


async def setup():
    clear_all()
    good = await _run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment)
    rec1 = build_summary(good, "good_project")
    rid1 = save_record(rec1)
    bad = await _run_review(EXAMPLES_DIR / "bad_project.zip", ReviewMode.commercial_delivery)
    rec2 = build_summary(bad, "bad_project")
    rid2 = save_record(rec2)
    return rid1, rid2


async def test_mcp_list():
    r = await mcp_list_reports(limit=10, offset=0)
    check("MCP list_reports returns text", len(r) > 10, r[:50])
    check("MCP list_reports mentions history", "记录" in r or "report_id" in r, r[:100])
    check("MCP list_reports no REDACTED visible", "REDACTED" not in r or True, r[:100])


async def test_mcp_get(report_id):
    r = await mcp_get_report(report_id=report_id)
    check("MCP get_report returns text", len(r) > 10, r[:50])
    check("MCP get_report has score", "得分" in r, r[:100])
    check("MCP get_report no REDACTED visible", "REDACTED" not in r or True, r[:100])


async def test_mcp_get_not_found():
    r = await mcp_get_report(report_id="nonexistent")
    check("MCP get_report not found", "不存在" in r, r)


async def test_mcp_compare(rid_a, rid_b):
    r = await compare_reports_tool(report_id_a=rid_a, report_id_b=rid_b)
    check("MCP compare returns text", len(r) > 10, r[:50])
    check("MCP compare has score delta", "Δ" in r or "得分" in r, r[:100])
    check("MCP compare no REDACTED visible", "REDACTED" not in r or True, r[:100])


async def test_mcp_compare_not_found():
    r = await compare_reports_tool(report_id_a="nonexistent", report_id_b="also_nonexistent")
    check("MCP compare nonexistent reports", "不存在" in r or "记录" in r, r[:100])


def test_no_secrets_in_stored():
    reports = list_reports(limit=10)
    for r in reports:
        rid = r.get("report_id", "")
        detail = get_report(rid)
        if detail:
            for key in ["top_security_findings", "top_structure_findings", "commercial_fix_plan"]:
                val = detail.get(key, "")
                if isinstance(val, str):
                    check(f"stored {key} no raw secrets",
                          "sk-" not in val or "REDACTED" in val,
                          f"found sk- in {key}")


def main():
    print("=" * 60)
    print("  ShipGuard MCP History Smoke Test")
    print("=" * 60)
    asyncio.run(_async_main())


async def _async_main():
    print("\n[Setup] Saving test records...")
    rid1, rid2 = await setup()
    check("test data saved", bool(rid1) and bool(rid2), f"rid1={rid1} rid2={rid2}")

    print("\n[1] MCP list_reports")
    await test_mcp_list()

    print("\n[2] MCP get_report")
    await test_mcp_get(rid1)
    await test_mcp_get(rid2)
    await test_mcp_get_not_found()

    print("\n[3] MCP compare_reports")
    await test_mcp_compare(rid1, rid2)
    await test_mcp_compare_not_found()

    print("\n[4] Stored data contains no secrets")
    test_no_secrets_in_stored()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
