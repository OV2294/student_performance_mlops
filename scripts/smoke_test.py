"""Post-deploy smoke test used by Jenkins: hits the running API container."""
import sys, time
import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
payload = {"gender": "Female", "age": 21, "study_hours_per_week": 15, "attendance_pct": 85,
           "previous_score": 70, "assignments_completed_pct": 80, "sleep_hours": 7,
           "stress_level": 2, "midterm_score": 65, "internet_access": "Yes",
           "parental_education": "Graduate", "tutoring": "Yes", "extracurricular": "No"}
for i in range(20):
    try:
        if requests.get(f"{BASE}/health", timeout=3).ok:
            break
    except requests.RequestException:
        pass
    print("waiting for API...", i); time.sleep(3)
else:
    sys.exit("API never became healthy")
r = requests.post(f"{BASE}/predict", json=payload, timeout=10)
print(r.status_code, r.json())
sys.exit(0 if r.ok else 1)
