import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_api():
    print("🚀 Starting API Verification...")
    
    # 1. Health Check
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return

    # 2. Authentication (Login Default Admin)
    print("\n🔐 Testing Authentication...")
    login_data = {
        "username": "admin@agenthealth.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Admin Login Successful")
    else:
        print(f"❌ Admin Login Failed: {response.status_code} - {response.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. List Patients
    print("\n📋 Testing Patient Listing...")
    response = requests.get(f"{BASE_URL}/patients/", headers=headers)
    if response.status_code == 200:
        patients = response.json()
        print(f"✅ Patient Listing Successful - Count: {len(patients)}")
    else:
        print(f"❌ Patient Listing Failed: {response.status_code} - {response.text}")

    # 4. Search Patients
    print("\n🔍 Testing Patient Search...")
    response = requests.get(f"{BASE_URL}/patients/search?query=System", headers=headers)
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Patient Search Successful - Results: {len(results)}")
    else:
        print(f"❌ Patient Search Failed: {response.status_code} - {response.text}")

    # 5. Get My Profile (as Admin - should fail or show error since admin has no patient profile)
    print("\n👤 Testing 'Me' Endpoint...")
    response = requests.get(f"{BASE_URL}/patients/me", headers=headers)
    print(f"Admin 'me' profile (expected restricted): {response.status_code}")

    # 6. Test Doctor Login & Patient Registration
    print("\n👨‍⚕️ Testing Doctor Role & Registration...")
    doc_login = {
        "username": "doctor@agenthealth.com",
        "password": "doctor123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=doc_login)
    if response.status_code == 200:
        doc_token = response.json()["access_token"]
        doc_headers = {"Authorization": f"Bearer {doc_token}"}
        print("✅ Doctor Login Successful")
        
        # Register new patient
        print("📝 Registering new patient as doctor...")
        reg_data = {
            "user_data": {
                "email": f"test_patient_{int(time.time())}@example.com",
                "full_name": "Test Patient",
                "password": "patient123",
                "role": "patient"
            },
            "patient_data": {
                "user_id": 0, # Will be set by backend
                "date_of_birth": "1990-01-01T00:00:00",
                "gender": "male",
                "blood_type": "O+",
                "phone": "1234567890",
                "address": "123 Test St",
                "emergency_contact": "Emergency Name",
                "emergency_phone": "0987654321"
            }
        }
        response = requests.post(f"{BASE_URL}/patients/register", json=reg_data, headers=doc_headers)
        if response.status_code == 201:
            patient = response.json()
            print(f"✅ Patient Registration Successful - ID: {patient['id']}")
            
            # 7. Test Appointment Creation
            print("\n📅 Testing Appointment Scheduling...")
            apt_data = {
                "patient_id": patient["id"],
                "doctor_id": 2, # Assuming doctor ID 2 is the default doctor
                "appointment_date": "2026-03-01T10:00:00",
                "duration_minutes": 30,
                "reason": "Regular Checkup"
            }
            response = requests.post(f"{BASE_URL}/appointments/", json=apt_data, headers=doc_headers)
            if response.status_code == 201:
                print("✅ Appointment Scheduled Successful")
            else:
                print(f"❌ Appointment Scheduling Failed: {response.status_code} - {response.text}")
        else:
            print(f"❌ Patient Registration Failed: {response.status_code} - {response.text}")
    else:
        print(f"❌ Doctor Login Failed: {response.status_code} - {response.text}")

    print("\n🏁 API Verification Phase Complete.")

if __name__ == "__main__":
    test_api()
