import sys, json, subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = SCRIPTS_DIR.parent / "examples"
API = "http://127.0.0.1:8000"

MODES = ["student_assignment", "github_showcase", "interview_project", "commercial_delivery"]


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


def main():
    good = EXAMPLES_DIR / "good_project.zip"
    bad = EXAMPLES_DIR / "bad_project.zip"

    if not good.exists() or not bad.exists():
        print("[FAIL] Test zips not found. Run python scripts/create_test_zips.py first.")
        return 1

    all_pass = True

    # Test good_project across all modes
    print("=" * 72)
    print(f"  good_project.zip — 4 review modes comparison")
    print("=" * 72)
    print(f"  {'Review Mode':<25} {'Score':>6} {'Verdict':<18} {'HIGH':>5} {'MED':>5} {'LOW':>5}")
    print("  " + "-" * 66)

    scores_good = []
    verdicts_good = []
    for mode in MODES:
        try:
            r = upload_test(str(good), mode)
            s = r["total_score"]
            v = r["verdict"]
            h = r["findings_count"].get("HIGH", 0)
            m = r["findings_count"].get("MEDIUM", 0)
            l = r["findings_count"].get("LOW", 0)
            scores_good.append(s)
            verdicts_good.append(v)
            print(f"  {mode:<25} {s:>6} {v:<18} {h:>5} {m:>5} {l:>5}")
        except Exception as e:
            print(f"  {mode:<25} {'ERR':>6} {str(e)[:30]:<18}")
            all_pass = False

    print()

    # Test bad_project across all modes
    print("=" * 72)
    print(f"  bad_project.zip — 4 review modes comparison")
    print("=" * 72)
    print(f"  {'Review Mode':<25} {'Score':>6} {'Verdict':<18} {'HIGH':>5} {'MED':>5} {'LOW':>5}")
    print("  " + "-" * 66)

    scores_bad = []
    verdicts_bad = []
    for mode in MODES:
        try:
            r = upload_test(str(bad), mode)
            s = r["total_score"]
            v = r["verdict"]
            h = r["findings_count"].get("HIGH", 0)
            m = r["findings_count"].get("MEDIUM", 0)
            l = r["findings_count"].get("LOW", 0)
            scores_bad.append(s)
            verdicts_bad.append(v)
            print(f"  {mode:<25} {s:>6} {v:<18} {h:>5} {m:>5} {l:>5}")
        except Exception as e:
            print(f"  {mode:<25} {'ERR':>6} {str(e)[:30]:<18}")
            all_pass = False

    print()

    # Verification
    print("=" * 72)
    print("  Verification")
    print("=" * 72)

    # 1. Four modes should not all have identical scores
    unique_good = len(set(scores_good))
    unique_bad = len(set(scores_bad))
    if unique_good >= 2:
        print(f"  [OK] good_project: {unique_good} unique scores across 4 modes")
    else:
        print(f"  [FAIL] good_project: all 4 modes returned same score ({scores_good[0]})")
        all_pass = False

    if unique_bad >= 2:
        print(f"  [OK] bad_project: {unique_bad} unique scores across 4 modes")
    else:
        print(f"  [FAIL] bad_project: all 4 modes returned same score ({scores_bad[0]})")
        all_pass = False

    # 2. commercial_delivery should be stricter than student_assignment
    if scores_bad[3] <= scores_bad[0]:
        print(f"  [OK] bad: commercial ({scores_bad[3]}) <= student ({scores_bad[0]})")
    else:
        print(f"  [FAIL] bad: commercial ({scores_bad[3]}) should be <= student ({scores_bad[0]})")
        all_pass = False

    # 3. good_project should still get scores >= 70 in student mode
    if scores_good[0] >= 70:
        print(f"  [OK] good (student): score={scores_good[0]} >= 70")
    else:
        print(f"  [FAIL] good (student): score={scores_good[0]} < 70")
        all_pass = False

    # 4. bad_project should get REJECT in all modes
    if all(v == "REJECT" for v in verdicts_bad):
        print(f"  [OK] bad_project: all verdicts=REJECT")
    else:
        print(f"  [FAIL] bad_project: not all verdicts=REJECT {verdicts_bad}")
        all_pass = False

    # 5. Report contains mode guidance
    try:
        r = upload_test(str(good), "commercial_delivery")
        md = r["report_markdown"]
        if "当前审查模式说明" in md:
            print("  [OK] report contains '当前审查模式说明' section")
        else:
            print("  [FAIL] report missing '当前审查模式说明' section")
            all_pass = False
    except Exception as e:
        print(f"  [FAIL] mode guidance check: {e}")
        all_pass = False

    print()
    print(f"  Overall: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
    print("=" * 72)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
