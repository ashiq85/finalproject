import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def verify_health_system():
    print("🧪 Verifying Patient IDs and Health Metrics System...")
    
    # login as doctor
    doc_login = {"username": "doctor@agenthealth.com", "password": "doctor123"}
    resp = requests.post(f"{BASE_URL}/auth/login", data=doc_login)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Register new patient and check Medical ID
    print("\n1️⃣ Registering patient to check Medical ID...")
    email = f"p_{int(time.time())}@test.com"
    reg_data = {
        "user_data": {"email": email, "full_name": "Verified Patient", "password": "password123", "role": "patient"},
        "patient_data": {
            "date_of_birth": "1990-05-15T00:00:00",
            "gender": "female",
            "blood_type": "A+",
            "phone": "555-0101",
            "address": "456 Verify Ave",
            "emergency_contact": "Guardian",
            "emergency_phone": "555-0202"
        }
    }
    resp = requests.post(f"{BASE_URL}/patients/register", json=reg_data, headers=headers)
    patient = resp.json()
    medical_id = patient.get("medical_id")
    print(f"Generated Medical ID: {medical_id}")
    if medical_id and medical_id.startswith("AH-"):
        print("✅ Medical ID generated correctly")
    else:
        print("❌ Medical ID generation failed")
        return

    # 2. Search by Medical ID
    print("\n2️⃣ Searching patient by Medical ID...")
    resp = requests.get(f"{BASE_URL}/patients/search?query={medical_id}", headers=headers)
    results = resp.json()
    if any(p["medical_id"] == medical_id for p in results):
        print("✅ Patient searchable by Medical ID")
    else:
        print("❌ Search by Medical ID failed")

    # 3. Log Health Metrics
    print("\n3️⃣ Logging health metrics (High Sugar)...")
    p_id = patient["id"]
    metrics = [
        {"metric_name": "blood_sugar_before", "value": 150.5, "unit": "mg/dL", "notes": "Fasting"},
        {"metric_name": "bp_systolic", "value": 145.0, "unit": "mmHg", "notes": "Resting"},
        {"metric_name": "cholesterol", "value": 250.0, "unit": "mg/dL", "notes": "Routine"}
    ]
    for m in metrics:
        requests.post(f"{BASE_URL}/patients/{p_id}/health-metrics", json=m, headers=headers)
    print("✅ Metrics logged")

    # 4. Verify AI Analysis using metrics
    print("\n4️⃣ Verifying AI Analysis (CrewAI Integration)...")
    analysis_req = {"patient_id": p_id, "symptoms": ["feeling thirsty", "frequent urination"]}
    resp = requests.post(f"{BASE_URL}/diagnosis/analyze", json=analysis_req, headers=headers)
    analysis = resp.json()
    
    print(f"Risk Level: {analysis.get('risk_level')}")
    print(f"Diagnoses: {analysis.get('potential_diagnosis')}")
    
    # Check if AI identified the risks from metrics
    diagnoses_str = str(analysis.get('potential_diagnosis')).lower()
    if "diabetes" in diagnoses_str or "sugar" in diagnoses_str:
        print("✅ AI successfully detected Diabetes/Sugar risk")
    if "hypertension" in diagnoses_str or "blood pressure" in diagnoses_str:
        print("✅ AI successfully detected Hypertension risk")
    if "cholesterol" in diagnoses_str:
        print("✅ AI successfully detected Cholesterol risk")
        
    print("\n🏁 Health Records System Verification Complete.")

if __name__ == "__main__":
    verify_health_system()
