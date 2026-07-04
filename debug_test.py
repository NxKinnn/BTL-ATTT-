
import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

print("=== Debug Admin Permission Test ===\n")

# Step 1: Create new test user
test_user = f"debug_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
test_pass = "DebugPass123!"

print("1. Registering test user:", test_user)
reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={"username": test_user, "password": test_pass})
print("   Register status:", reg_res.status_code)
print("   Register response:", reg_res.text)


# Step 2: Login test user
print("\n2. Logging in test user")
login_res = requests.post(f"{BASE_URL}/api/auth/login", data={"username": test_user, "password": test_pass})
print("   Login status:", login_res.status_code)
user_token = login_res.json()['access_token']
print("   User token obtained")


# Step3: Add a vault item
print("\n3. Adding a vault item")
vault_res = requests.post(
    f"{BASE_URL}/api/vault/items",
    json={
        "item_name": "Debug Test Item",
        "username": "debug_user",
        "password": "DebugSecret123!",
        "category_id": 1
    },
    params={"master_password": test_pass},
    headers={"Authorization": f"Bearer {user_token}"}
)
print("   Add vault status:", vault_res.status_code)
test_vault_id = vault_res.json()['vault_id']
print("   Vault ID:", test_vault_id)


# Step4: Login as admin
print("\n4. Logging in as admin")
admin_login = requests.post(
    f"{BASE_URL}/api/auth/login",
    data={"username": "admin", "password": "Admin123!"}
)
print("   Admin login status:", admin_login.status_code)
admin_token = admin_login.json()['access_token']
print("   Admin token obtained")


# Step5: Try to decrypt as admin
print("\n5. Trying to decrypt as admin")
admin_decrypt = requests.get(
    f"{BASE_URL}/api/vault/items/{test_vault_id}",
    params={"master_password": test_pass},
    headers={"Authorization": f"Bearer {admin_token}"}
)
print("   Admin decrypt status:", admin_decrypt.status_code)
print("   Admin decrypt response:", admin_decrypt.text)

print("\n=== Debug Complete ===")
