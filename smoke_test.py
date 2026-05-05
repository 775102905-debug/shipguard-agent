import requests, sys
files = {"file": open(r"D:\Users\77510\Desktop\shipguard-agent\test_sources\good_project.zip","rb")}
r = requests.post("http://127.0.0.1:8000/api/review", files=files, data={"review_mode":"interview_project"})
print(f"good_project: status={r.status_code}")
resp = r.json()
print(f"total_score={resp.get('total_score')}, verdict={resp.get('verdict')}")
print(f"findings_count={resp.get('findings_count')}")
pp = resp.get("project_profile",{})
print(f"project_type={pp.get('project_type')}, frameworks={pp.get('detected_frameworks')}, languages={pp.get('detected_languages')}")
print(f"report_md_len={len(resp.get('report_markdown',''))}")
print("---")
files2 = {"file": open(r"D:\Users\77510\Desktop\shipguard-agent\test_sources\bad_project.zip","rb")}
r2 = requests.post("http://127.0.0.1:8000/api/review", files=files2, data={"review_mode":"student_assignment"})
print(f"bad_project: status={r2.status_code}")
resp2 = r2.json()
print(f"total_score={resp2.get('total_score')}, verdict={resp2.get('verdict')}")
print(f"findings_count={resp2.get('findings_count')}")
print(f"report_md_len={len(resp2.get('report_markdown',''))}")
md = resp2.get("report_markdown","")
for kw in ["README", ".env.example", "C:\\\\Users", "node_modules", "secret", "password", "Authorization"]:
    if kw.lower() in md.lower():
        print(f"  FOUND in report: {kw}")
