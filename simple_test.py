
import requests
import sys

BASE_URL = "http://localhost:8000"

print("Testing server...")
try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
    
    print("\nTesting register...")
    reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "simpleuser",
        "password": "SimplePass123!"
    }, timeout=5)
    print(f"Register status: {reg.status_code}")
    print(f"Register response: {reg.text}")
    
    print("\nTesting login...")
    login = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "simpleuser",
        "password": "SimplePass123!"
    }, timeout=5)
    print(f"Login status: {login.status_code}")
    print(f"Login response: {login.text}")
    
    if login.status_code == 200:
        token = login.json()["access_token"]
        print("\nGot token!")
        
        print("\nTesting categories...")
        cats = requests.get(f"{BASE_URL}/api/vault/categories", timeout=5)
        print(f"Cats status: {cats.status_code}")
        print(f"Cats: {cats.json()}")
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
