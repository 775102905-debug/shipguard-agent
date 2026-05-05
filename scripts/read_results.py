import json

with open("good_final.json", encoding="utf-8") as f:
    d = json.load(f)

print("=== good_project ===")
print(f"  score={d['total_score']}, verdict={d['verdict']}")
print(f"  HIGH={d['findings_count']['HIGH']}, MED={d['findings_count']['MEDIUM']}, LOW={d['findings_count']['LOW']}")

with open("bad_final.json", encoding="utf-8") as f:
    d = json.load(f)

print()
print("=== bad_project ===")
print(f"  score={d['total_score']}, verdict={d['verdict']}")
print(f"  HIGH={d['findings_count']['HIGH']}, MED={d['findings_count']['MEDIUM']}, LOW={d['findings_count']['LOW']}")
kf = d["project_profile"].get("key_files", {})
print(f"  README={kf.get('README.md')}, .env.example={kf.get('.env.example')}")
md = d["report_markdown"]
print(f"  SECRET/PASSWORD risk: {'SECRET' in md or 'PASSWORD' in md or 'Authorization' in md}")
print(f"  .env risk: {'.env' in md and '风险' in md}")
print(f"  修复建议: {'修复建议' in md}")
