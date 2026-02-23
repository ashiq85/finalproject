import requests
import json
import traceback

BASE_URL = "http://localhost:8000/api"

def test_verbose():
    print("=== Testing Backend ===")
    
    # Test simple status
    try:
        r = requests.get(f"http://localhost:8000/docs")
        print(f"Docs status: {r.status_code}")
    except Exception as e:
        print(f"Backend unreachable: {e}")
        return

    # Try signup with full error output
    signup_data = {
        "email": "verbose_test@example.com",
        "full_name": "Verbose Test",
        "password": "password123",
        "role": "patient"
    }
    print(f"\nAttempting signup...")
    r = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:1000]}")
    
    # If success, try login
    if r.status_code in [200, 201]:
        print("\nAttempting login...")
        login_data = {"username": signup_data["email"], "password": signup_data["password"]}
        r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"Login Status: {r.status_code}")
        print(f"Login Response: {r.text[:1000]}")
        
        if r.status_code == 200:
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("\nAttempting /auth/me...")
            r = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"Me Status: {r.status_code}")
            print(f"Me Response: {r.text[:1000]}")
    
    # Try existing doctor user
    print("\n=== Testing existing doctor login ===")
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "doctor@hospital.com", "password": "doctor123"})
    print(f"Doctor login status: {r.status_code}, response: {r.text[:500]}")
    
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin@hospital.com", "password": "admin123"})
    print(f"Admin login status: {r.status_code}, response: {r.text[:500]}")
    
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "patient@hospital.com", "password": "patient123"})
    print(f"Patient login status: {r.status_code}, response: {r.text[:500]}")

if __name__ == "__main__":
    test_verbose()
