
import requests
import json

API_BASE = "http://localhost:8000"

print("=== Testing FortressVault API ===")

# 1. Test get categories (public)
print("\n1. Testing GET /api/vault/categories...")
try:
    r = requests.get(f"{API_BASE}/api/vault/categories")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        categories = r.json()
        print(f"   Categories: {[cat['category_name'] for cat in categories]}")
    else:
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Test register user
print("\n2. Testing POST /api/auth/register...")
test_username = "testuser1234"
test_password = "testpass1234"
try:
    r = requests.post(f"{API_BASE}/api/auth/register", json={
        "username": test_username,
        "password": test_password
    })
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text}")
except Exception as e:
    print(f"   Error: {e}")

# 3. Test login
print("\n3. Testing POST /api/auth/login...")
try:
    r = requests.post(f"{API_BASE}/api/auth/login", data={
        "username": test_username,
        "password": test_password
    })
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        login_data = r.json()
        token = login_data['access_token']
        user = login_data['user']
        print(f"   Logged in as {user['username']} ({user['role_name']})")
        print(f"   Token: {token[:50]}...")
    else:
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# 4. Test get vault items
print("\n4. Testing GET /api/vault/items...")
headers = {"Authorization": f"Bearer {token}"}
try:
    r = requests.get(f"{API_BASE}/api/vault/items", headers=headers)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        items = r.json()
        print(f"   Vault items: {len(items)}")
    else:
        print(f"   Response: {r.text}")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== Test Complete ===")

