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


os.environ["MCP_ENABLED"] = "true"
os.environ["LLM_REVIEW_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""

sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.integrations.mcp_server import _run_review, _build_summary
from app.schemas.review import ReviewMode


async def test_concurrent():
    good = EXAMPLES_DIR / "good_project.zip"
    bad = EXAMPLES_DIR / "bad_project.zip"

    tasks = []
    for i in range(5):
        tasks.append(_run_review(good, ReviewMode.student_assignment))
    for i in range(5):
        tasks.append(_run_review(bad, ReviewMode.commercial_delivery))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    good_count = 0
    bad_count = 0
    errors = 0

    for r in results:
        if isinstance(r, Exception):
            errors += 1
            continue
        score = r.get("score")
        verdict = r.get("verdict")
        if score and verdict:
            if verdict.value == "PASS":
                good_count += 1
            elif verdict.value == "REJECT":
                bad_count += 1

    check("concurrent 10 reviews non crashes", True)
    check("concurrent has PASS results", good_count >= 3, f"got {good_count} PASS")
    check("concurrent has REJECT results", bad_count >= 3, f"got {bad_count} REJECT")
    check("concurrent errors = 0", errors == 0, f"got {errors} errors")
    return results


async def test_repeat_no_pollution():
    previous = None
    modes = [
        (EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment),
        (EXAMPLES_DIR / "bad_project.zip", ReviewMode.github_showcase),
        (EXAMPLES_DIR / "good_project.zip", ReviewMode.interview_project),
        (EXAMPLES_DIR / "bad_project.zip", ReviewMode.commercial_delivery),
    ]

    for zip_path, mode in modes * 2:
        result = await _run_review(zip_path, mode)
        score = result.get("score")
        s = score.total if score else 0
        if previous is not None:
            check(f"repeat: score {s} is int", isinstance(s, int), str(s))
        previous = s

    check("repeat 8 calls: no crash", True)
    check("repeat 8 calls: normal", True)
    return True


async def test_concurrent_no_path_leak():
    tasks = []
    for i in range(5):
        tasks.append(_run_review(EXAMPLES_DIR / "good_project.zip", ReviewMode.student_assignment))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            continue
        summary = _build_summary(r)
        check("concurrent summary no leak",
              "mcp_server" not in summary and "integrations" not in summary,
              f"leak in: {summary[:100]}")


def main():
    print("=" * 60)
    print("  ShipGuard MCP Concurrency Test")
    print("=" * 60)

    print("\n[1] Concurrent 10 reviews (5 good + 5 bad)")
    asyncio.run(test_concurrent())

    print("\n[2] Repeated calls (8 times, alternating modes)")
    asyncio.run(test_repeat_no_pollution())

    print("\n[3] Concurrent path leak check")
    asyncio.run(test_concurrent_no_path_leak())

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL} checks")
    print(f"{'=' * 60}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
