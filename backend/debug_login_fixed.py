import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_login(email, password):
    print(f"\nAttempting login for {email}...")
    login_data = {"username": email, "password": password}
    try:
        r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"Login Status: {r.status_code}")
        if r.status_code == 200:
            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            r_me = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"Me Status: {r_me.status_code}")
            print(f"Me Response: {r_me.text[:200]}")
            return r_me.status_code == 200
        else:
            print(f"Login Response: {r.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_tests():
    # Test built-in users
    users = [
        ("admin@agenthealth.com", "admin123"),
        ("doctor@agenthealth.com", "doctor123"),
        ("patient@agenthealth.com", "patient123"),
        ("verbose_test@example.com", "password123")
    ]
    
    for email, password in users:
        test_login(email, password)

if __name__ == "__main__":
    run_tests()
