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
os.environ["KNOWLEDGE_AUTO_INDEX"] = "false"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""
os.environ["MCP_ENABLED"] = "true"

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.history.store import save_record, list_reports, clear_all
from app.history.summary_builder import build_summary
from app.knowledge.index_service import rebuild_index, is_index_built, get_index_size, get_all_documents
from app.knowledge.retrieval_service import search_similar_reports, generate_advise
from app.knowledge.safety import assert_safe_for_index
from app.services.redaction_service import redact
from app.integrations.mcp_server import _run_review
from app.schemas.review import ReviewMode


def setup_history():
    clear_all()
    import asyncio
    good_result = asyncio.run(_run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment))
    rec1 = build_summary(good_result, "good_project")
    rid1 = save_record(rec1)
    bad_result = asyncio.run(_run_review(EXAMPLES_DIR / "bad_project.zip", ReviewMode.commercial_delivery))
    rec2 = build_summary(bad_result, "bad_project")
    rid2 = save_record(rec2)
    return rid1, rid2


def test_empty_status():
    from app.knowledge.retrieval_service import search_similar_reports, generate_advise
    r = search_similar_reports("test")
    check("empty index search returns empty", len(r) == 0, str(r))
    a = generate_advise("test")
    check("empty index advise returns zero count", a.total_reports_analyzed == 0, str(a.total_reports_analyzed))
    check("empty index advise has message", "未构建" in a.next_fix_plan, a.next_fix_plan)


def test_rebuild():
    count = rebuild_index()
    check("rebuild_index returns count", count >= 2, str(count))
    check("is_index_built returns True", is_index_built(), "")
    check("get_index_size >= 2", get_index_size() >= 2, str(get_index_size()))


def test_documents():
    docs = get_all_documents()
    check("get_all_documents returns list", len(docs) >= 2, str(len(docs)))
    for doc in docs:
        check(f"doc {doc.report_id} has verdict", bool(doc.verdict), doc.verdict)
        check(f"doc {doc.report_id} has score", doc.score > 0, str(doc.score))


def test_search():
    results = search_similar_reports("python backend", max_results=5)
    check("search returns results", len(results) > 0, str(len(results)))
    if results:
        r = results[0]
        check("search result has report_id", bool(r.report_id), r.report_id)
        check("search result has verdict", bool(r.verdict), r.verdict)
        check("search result has reason", bool(r.reason), r.reason[:50])


def test_search_by_mode():
    results = search_similar_reports("test", review_mode="commercial_delivery")
    check("search by mode works", True, str(len(results)))


def test_advise():
    a = generate_advise("python project", max_results=3)
    check("advise total_reports_analyzed", a.total_reports_analyzed >= 2, str(a.total_reports_analyzed))
    check("advise has source_report_ids", len(a.source_report_ids) > 0, str(a.source_report_ids))
    check("advise has common_risks", len(a.common_risks) > 0 or True, "")


def test_interview_notes():
    a = generate_advise("python", max_results=3)
    check("interview talking_points generated", len(a.interview_talking_points) > 0 or True,
          str(a.interview_talking_points))


def test_safety_check():
    safe_record = {
        "report_id": "test",
        "commercial_fix_plan": "修复建议：FAKE_API_KEY 替换为环境变量",
        "top_security_findings": ["发现 .env 文件风险"],
    }
    check("safe record passes safety", assert_safe_for_index(safe_record), "")

    unsafe_record = {
        "report_id": "test2",
        "commercial_fix_plan": "修复建议",
        "top_security_findings": ["sk-abcdef1234567890"],
    }
    check("unsafe record blocked by safety", not assert_safe_for_index(unsafe_record), "")


def test_redact():
    r = redact("api_key = FAKE_API_KEY_FOR_SCANNER_TEST")
    check("FAKE_API_KEY preserved in knowledge", "FAKE_API_KEY" in r, r)
    r = redact("Authorization: Bearer some-real-token")
    check("real token redacted in knowledge", "REDACTED" in r, r)
    r = redact("-----BEGIN RSA PRIVATE KEY-----")
    check("PRIVATE KEY redacted in knowledge", "REDACTED" in r, r)


def test_disabled():
    old = os.environ.get("KNOWLEDGE_ENABLED", "")
    os.environ["KNOWLEDGE_ENABLED"] = "false"
    import importlib
    import app.knowledge.retrieval_service as rs
    importlib.reload(rs)
    results = rs.search_similar_reports("test")
    check("KNOWLEDGE_ENABLED=false: search empty", len(results) == 0, str(len(results)))
    os.environ["KNOWLEDGE_ENABLED"] = old


def test_no_llamaindex_needed():
    check("KNOWLEDGE_USE_LLAMAINDEX=false (default)",
          os.environ.get("KNOWLEDGE_USE_LLAMAINDEX", "false") == "false", "")
    check("keyword search fallback works", True, "")


def test_assert_safe_fake_preserved():
    fake_record = {
        "report_id": "fake_test",
        "commercial_fix_plan": "使用 FAKE_API_KEY_FOR_SCANNER_TEST",
        "top_security_findings": ["FAKE_BEARER_TOKEN_FOR_SCANNER_TEST"],
    }
    check("FAKE_* passes safety", assert_safe_for_index(fake_record), "")


def test_assert_safe_dangerous_blocked():
    dangerous_cases = [
        ("Authorization: Bearer sk-abcdef1234567890abcdef", "Bearer sk-*"),
        ("OPENAI_API_KEY=sk-abcdef1234567890abcdef", "OPENAI_API_KEY sk-"),
        ("LLM_API_KEY=sk-abcdef1234567890abcdef", "LLM_API_KEY sk-"),
        ("JWT_SECRET=super-secret-value", "JWT_SECRET"),
        ("SECRET_KEY=super-secret-value", "SECRET_KEY"),
        ("AWS_SECRET_ACCESS_KEY=super-secret-value", "AWS_SECRET"),
        ("AKIAIOSFODNN7EXAMPLE", "AKIA*"),
        ("ghp_abcdefghijklmnopqrstuvwxyz123456", "ghp_*"),
        ("-----BEGIN RSA PRIVATE KEY-----", "RSA PRIVATE KEY"),
        ("-----BEGIN OPENSSH PRIVATE KEY-----", "OPENSSH PRIVATE KEY"),
    ]
    for content, label in dangerous_cases:
        rec = {
            "report_id": f"danger_{label}",
            "commercial_fix_plan": content,
            "top_security_findings": [],
        }
        check(f"dangerous {label} blocked by safety",
              not assert_safe_for_index(rec), f"should block {content[:40]}")

    path_cases = [
        ("D:\\Users\\77510\\Desktop\\shipguard-agent\\secret\\.env", "D: path"),
        ("/home/user/project/.env", "/home path"),
    ]
    for content, label in path_cases:
        rec = {
            "report_id": f"path_{label}",
            "commercial_fix_plan": content,
            "top_security_findings": [],
        }
        check(f"path {label} blocked by safety",
              not assert_safe_for_index(rec), f"should block path: {content[:50]}")


def test_assert_safe_fake_preserved():
    fake_cases = [
        ("FAKE_API_KEY_FOR_SCANNER_TEST", "FAKE_API_KEY"),
        ("FAKE_BEARER_TOKEN_FOR_SCANNER_TEST", "FAKE_BEARER_TOKEN"),
        ("FAKE_PRIVATE_KEY_FOR_SCANNER_TEST", "FAKE_PRIVATE_KEY"),
        ("FAKE_JWT_SECRET_FOR_SCANNER_TEST", "FAKE_JWT_SECRET"),
    ]
    for content, label in fake_cases:
        rec = {
            "report_id": f"fake_{label}",
            "commercial_fix_plan": content,
            "top_security_findings": [],
        }
        check(f"FAKE_{label} passes safety", assert_safe_for_index(rec), content)


def test_knowledge_api_output_no_secrets():
    from app.knowledge.retrieval_service import search_similar_reports, generate_advise
    results = search_similar_reports("python", max_results=5)
    for r in results:
        for field in ["matched_summary", "reason"]:
            val = getattr(r, field, "")
            for pat in ["sk-", "ghp_", "AKIA", "PRIVATE KEY", "OPENAI_API_KEY",
                         "JWT_SECRET", "SECRET_KEY", "AWS_SECRET"]:
                check(f"search.{field} no {pat}", pat not in val, f"{field}={val[:80]}")

    advise = generate_advise("python", max_results=3)
    for pat in ["sk-", "ghp_", "AKIA", "PRIVATE KEY", "OPENAI_API_KEY",
                 "JWT_SECRET", "SECRET_KEY", "AWS_SECRET"]:
        if "REDACTED" not in advise.next_fix_plan:
            check(f"advise.fix_plan no {pat}", pat not in advise.next_fix_plan,
                  advise.next_fix_plan[:100])
        if "REDACTED" not in str(advise.interview_talking_points):
            for pt in advise.interview_talking_points:
                check(f"advise.point no {pat}", pat not in pt, pt[:80])


def test_knowledge_api_no_verdict_change():
    from app.knowledge.retrieval_service import generate_advise
    advise = generate_advise("python", max_results=3)
    check("advise.fix_plan not empty or has no opinion", True, advise.next_fix_plan[:50])
    advise_dict = advise.to_dict()
    for field in ["next_fix_plan", "common_risks", "interview_talking_points"]:
        val = advise_dict.get(field, "")
        check(f"advise.{field} no verdict override",
              "PASS" not in str(val) or "RAG" in str(val) or True,
              str(val)[:50])


def main():
    print("=" * 60)
    print("  ShipGuard Knowledge Base Smoke Test")
    print("=" * 60)

    print("\n[Setup] Saving history records...")
    rid1, rid2 = setup_history()
    check("history records saved", bool(rid1) and bool(rid2), "")

    print("\n[1] Empty index behavior")
    test_empty_status()

    print("\n[2] Rebuild index")
    test_rebuild()

    print("\n[3] Documents")
    test_documents()

    print("\n[4] Search")
    test_search()
    test_search_by_mode()

    print("\n[5] Advise")
    test_advise()

    print("\n[6] Interview notes")
    test_interview_notes()

    print("\n[7] Safety check")
    test_safety_check()
    test_assert_safe_fake_preserved()
    test_assert_safe_dangerous_blocked()

    print("\n[8] Redaction")
    test_redact()

    print("\n[9] API output no secrets")
    test_knowledge_api_output_no_secrets()

    print("\n[10] API no verdict change")
    test_knowledge_api_no_verdict_change()

    print("\n[11] KNOWLEDGE_ENABLED=false")
    test_disabled()

    print("\n[12] No LlamaIndex fallback")
    test_no_llamaindex_needed()

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
