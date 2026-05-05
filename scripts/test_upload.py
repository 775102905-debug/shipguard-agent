import subprocess, json, sys
from pathlib import Path

API = "http://127.0.0.1:8001"


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

    out = result.stdout.decode("utf-8", errors="replace")
    # Check if curl output starts with HTTP response or error
    if out.startswith("{"):
        return json.loads(out)
    # Try to parse as JSON from stderr (in case of redirect)
    raise RuntimeError(f"Unexpected output: {out[:200]}")


def main():
    examples = Path(__file__).resolve().parent.parent / "examples"

    print("=" * 60)
    print("  Frontend Integration Test — via curl.exe")
    print("=" * 60)

    # Health
    print("\n[1] /health")
    try:
        r = subprocess.run(
            ["curl.exe", "--max-time", "5", "--no-progress-meter", f"{API}/health"],
            capture_output=True, timeout=10,
        )
        d = json.loads(r.stdout.decode("utf-8"))
        print(f"  [OK] status={d.get('status')}")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return 1

    # Good project
    print("\n[2] good_project.zip")
    try:
        r = upload_test(str(examples / "good_project.zip"), "student_assignment")
        print(f"  score={r['total_score']}, verdict={r['verdict']}")
        print(f"  HIGH={r['findings_count']['HIGH']}, MED={r['findings_count']['MEDIUM']}, LOW={r['findings_count']['LOW']}")
        kf = r["project_profile"].get("key_files", {})
        print(f"  README={kf.get('README.md')}, .env.example={kf.get('.env.example')}")
        assert r["total_score"] >= 70, f"Expected >= 70, got {r['total_score']}"
        assert r["verdict"] == "PASS", f"Expected PASS, got {r['verdict']}"
        print("  [OK] assertions PASS")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()

    # Bad project
    print("\n[3] bad_project.zip")
    try:
        r = upload_test(str(examples / "bad_project.zip"), "student_assignment")
        print(f"  score={r['total_score']}, verdict={r['verdict']}")
        print(f"  HIGH={r['findings_count']['HIGH']}, MED={r['findings_count']['MEDIUM']}, LOW={r['findings_count']['LOW']}")
        kf = r["project_profile"].get("key_files", {})
        print(f"  README={kf.get('README.md')}, .env.example={kf.get('.env.example')}")

        md = r["report_markdown"]
        print(f"  [{'OK' if 'C:\\\\Users' in md or 'Windows' in md else 'NO'}] C:\\Users risk")
        print(f"  [{'OK' if 'SECRET' in md or 'PASSWORD' in md or 'Authorization' in md else 'NO'}] SECRET/PASSWORD/Authorization risk")
        print(f"  [{'OK' if '.env' in md and '风险' in md else 'NO'}] .env file risk")
        print(f"  [{'OK' if '修复建议' in md else 'NO'}] 修复建议 present")

        assert r["verdict"] == "REJECT", f"Expected REJECT, got {r['verdict']}"
        assert r["findings_count"]["HIGH"] > 0, "Expected HIGH > 0"
        print("  [OK] assertions PASS")
    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  Done")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
