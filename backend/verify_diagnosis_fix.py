import requests
import json

BASE_URL = "http://localhost:8000/api"

def get_token():
    # Login as admin to get token
    login_data = {"username": "admin@agenthealth.com", "password": "admin123"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_diagnosis_analyze(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test cases
    test_cases = [
        {"symptoms": ["face drooping", "slurred speech"], "vitals": {}},
        {"symptoms": ["chest pain", "shortness of breath"], "vitals": {"blood_pressure": {"systolic": 190}}},
        {"symptoms": ["fever", "cough"], "vitals": {}}
    ]
    
    for case in test_cases:
        print(f"\nTesting symptoms: {case['symptoms']}")
        response = requests.post(f"{BASE_URL}/diagnosis/analyze", json=case, headers=headers)
        if response.status_code == 200:
            print("Status: 200 OK")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    token = get_token()
    if token:
        test_diagnosis_analyze(token)
    else:
        print("Failed to get auth token")
