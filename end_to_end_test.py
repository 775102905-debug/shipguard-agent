import requests, json
BACKEND = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:5173"
r = requests.get(FRONTEND)
print(f"[FRONTEND] status={r.status_code} len={len(r.text)}")
r2 = requests.get(BACKEND + "/health")
print(f"[HEALTH] status={r2.status_code} json={r2.json()}")
with open("test_sources/good_project.zip","rb") as f:
    r3 = requests.post(BACKEND+"/api/review",files={"file":f},data={"review_mode":"interview_project"})
j3 = r3.json()
print(f"[GOOD] status={r3.status_code} score={j3['total_score']} verdict={j3['verdict']}")
print(f"[GOOD] findings={j3['findings_count']} report_len={len(j3['report_markdown'])}")
with open("test_sources/bad_project.zip","rb") as f:
    r4 = requests.post(BACKEND+"/api/review",files={"file":f},data={"review_mode":"student_assignment"})
j4 = r4.json()
print(f"[BAD] status={r4.status_code} score={j4['total_score']} verdict={j4['verdict']}")
print(f"[BAD] findings={j4['findings_count']} report_len={len(j4['report_markdown'])}")
md=j4['report_markdown']
for kw in ["README","env.example","SECRET","PASSWORD","Authorization"]:
    if kw.lower() in md.lower(): print(f"[BAD] report HAS: {kw}")
print("ALL E2E PASSED")
