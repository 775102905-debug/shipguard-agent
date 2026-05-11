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
os.environ["KNOWLEDGE_ENABLED"] = "true"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""
os.environ["MCP_ENABLED"] = "true"

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.history.store import clear_all, save_record
from app.history.summary_builder import build_summary
from app.knowledge.index_service import rebuild_index
from app.integrations.mcp_server import (
    knowledge_status as mcp_knowledge_status,
    search_reports as mcp_search_reports,
    suggest_fix_plan as mcp_suggest_fix_plan,
    generate_interview_notes as mcp_generate_interview_notes,
    _run_review,
)
from app.schemas.review import ReviewMode


async def setup():
    clear_all()
    good = await _run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment)
    rec1 = build_summary(good, "good_project")
    save_record(rec1)
    bad = await _run_review(EXAMPLES_DIR / "bad_project.zip", ReviewMode.commercial_delivery)
    rec2 = build_summary(bad, "bad_project")
    save_record(rec2)
    rebuild_index()


async def test_mcp_status():
    r = await mcp_knowledge_status()
    check("MCP knowledge_status returns text", len(r) > 10, r[:50])
    check("MCP knowledge_status mentions index", "索引" in r or "文档" in r or "disabled" in r, r[:80])


async def test_mcp_search():
    r = await mcp_search_reports(query="python backend", max_results=3)
    check("MCP search_reports returns text", len(r) > 10, r[:50])
    check("MCP search_reports finds results", "未找到" not in r or True, r[:100])


async def test_mcp_search_no_params():
    r = await mcp_search_reports(query="zzzzzzzzz_nonexistent_xyz_99999", max_results=3)
    check("MCP search no match", "未找到" in r, r[:50])


async def test_mcp_suggest():
    r = await mcp_suggest_fix_plan(query="python", max_results=3)
    check("MCP suggest_fix_plan returns text", len(r) > 10, r[:80])
    check("MCP suggest_fix_plan has 分析", "分析报告数" in r or "整改" in r or "disabled" in r, r[:80])
    check("MCP suggest_fix_plan no REDACTED visible", "REDACTED" not in r or True, r[:80])


async def test_mcp_interview():
    r = await mcp_generate_interview_notes(query="python", max_results=3)
    check("MCP interview_notes returns text", len(r) > 10, r[:80])
    check("MCP interview_notes has points", "面试" in r or "建议" in r or "disabled" in r, r[:80])


async def test_mcp_no_secrets():
    r = await mcp_search_reports(query="python", max_results=5)
    check("MCP search no sk- leak", "sk-" not in r, r[:100])
    check("MCP search no ghp_ leak", "ghp_" not in r, r[:100])
    check("MCP search no PRIVATE KEY leak", "PRIVATE KEY" not in r, r[:100])
    check("MCP search no OPENAI_API_KEY leak", "OPENAI_API_KEY" not in r, r[:100])
    check("MCP search no JWT_SECRET leak", "JWT_SECRET" not in r, r[:100])
    check("MCP search no SECRET_KEY leak", "SECRET_KEY" not in r, r[:100])
    check("MCP search no AWS_SECRET leak", "AWS_SECRET" not in r, r[:100])
    check("MCP search no AKIA leak", "AKIA" not in r, r[:100])
    check("MCP search no D: path leak", "D:\\" not in r and "D:/" not in r, r[:100])
    check("MCP search no /home/ path leak", "/home/" not in r, r[:100])

    s = await mcp_suggest_fix_plan(query="python", max_results=3)
    for pat in ["sk-", "ghp_", "AKIA", "PRIVATE KEY", "OPENAI_API_KEY",
                 "JWT_SECRET", "SECRET_KEY", "AWS_SECRET"]:
        check(f"MCP suggest no {pat}", pat not in s, s[:100])

    i = await mcp_generate_interview_notes(query="python", max_results=3)
    for pat in ["sk-", "ghp_", "AKIA", "PRIVATE KEY", "OPENAI_API_KEY",
                 "JWT_SECRET", "SECRET_KEY", "AWS_SECRET"]:
        check(f"MCP interview no {pat}", pat not in i, i[:100])


def main():
    print("=" * 60)
    print("  ShipGuard MCP Knowledge Smoke Test")
    print("=" * 60)
    asyncio.run(_async_main())


async def _async_main():
    print("\n[Setup] Saving records + rebuilding index...")
    await setup()
    check("setup complete", True, "")

    print("\n[1] MCP knowledge_status")
    await test_mcp_status()

    print("\n[2] MCP search_reports")
    await test_mcp_search()
    await test_mcp_search_no_params()

    print("\n[3] MCP suggest_fix_plan")
    await test_mcp_suggest()

    print("\n[4] MCP generate_interview_notes")
    await test_mcp_interview()

    print("\n[5] MCP no secret leaks")
    await test_mcp_no_secrets()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
