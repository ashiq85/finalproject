import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_signup_login():
    print("🚀 Testing Signup and Login...")
    
    # 1. Signup
    signup_data = {
        "email": "test_login@example.com",
        "full_name": "Test Login User",
        "password": "password123",
        "role": "patient"
    }
    print(f"Attempting signup for {signup_data['email']}...")
    resp = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print(f"Signup Status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Signup Failed: {resp.text}")
        return

    # 2. Login
    login_data = {
        "username": signup_data["email"],
        "password": signup_data["password"]
    }
    print(f"Attempting login...")
    resp = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print(f"Login Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Login Failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    
    # 3. Get Me
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Attempting /auth/me...")
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Me Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Me Response: {resp.json()}")
    else:
        print(f"Me Failed: {resp.text}")

if __name__ == "__main__":
    test_signup_login()
