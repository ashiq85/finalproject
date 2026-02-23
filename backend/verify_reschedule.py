import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def get_token(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]

def test_reschedule():
    # 1. Login as patient
    patient_token = get_token("patient@agenthealth.com", "patient123")
    headers = {"Authorization": f"Bearer {patient_token}"}
    
    # Get appointments
    appointments = requests.get(f"{BASE_URL}/appointments/", headers=headers).json()
    if not appointments:
        print("No appointments found for patient.")
        return
    
    apt_id = appointments[0]["id"]
    print(f"Testing reschedule for appointment {apt_id}...")
    
    # 2. Request reschedule
    new_date = (datetime.now() + timedelta(days=2)).isoformat()
    res = requests.post(
        f"{BASE_URL}/appointments/{apt_id}/request-reschedule",
        headers=headers,
        json={"requested_new_date": new_date}
    )
    print(f"Request Result: {res.status_code}, Status: {res.json().get('status')}")
    
    # 3. Login as doctor (using the default doctor)
    doctor_token = get_token("doctor@agenthealth.com", "doctor123")
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
    
    # 4. Approve reschedule
    res = requests.post(f"{BASE_URL}/appointments/{apt_id}/approve-reschedule", headers=doctor_headers)
    print(f"Approve Result: {res.status_code}, Status: {res.json().get('status')}, New Date: {res.json().get('appointment_date')}")

if __name__ == "__main__":
    try:
        test_reschedule()
    except Exception as e:
        print(f"Error: {e}")
