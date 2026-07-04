
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
results = []


def log_result(component, status, message=""):
    results.append({"component": component, "status": status, "message": message})
    print(f"[{status}] {component}: {message}")


def test_root():
    print("\n=== TEST ROOT ENDPOINT ===")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        log_result("Backend Server", "PASS", "Server running, root endpoint responding")
        return True
    except Exception as e:
        log_result("Backend Server", "FAIL", str(e))
        return False


def test_categories():
    print("\n=== TEST CATEGORIES ===")
    try:
        r = requests.get(f"{BASE_URL}/api/vault/categories", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        cats = r.json()
        assert len(cats) == 4, f"Expected 4 categories, got {len(cats)}"
        log_result("Categories API", "PASS", f"Got {len(cats)} categories")
        return True
    except Exception as e:
        log_result("Categories API", "FAIL", str(e))
        return False


def test_register():
    print("\n=== TEST REGISTER ===")
    try:
        test_user = f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        data = {"username": test_user, "password": "TestPass123!"}
        r = requests.post(f"{BASE_URL}/api/auth/register", json=data, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        log_result("Register API", "PASS", f"User {test_user} registered successfully")
        return test_user, "TestPass123!"
    except Exception as e:
        log_result("Register API", "FAIL", str(e))
        return None, None


def test_login(username, password):
    print("\n=== TEST LOGIN ===")
    try:
        data = {"username": username, "password": password}
        r = requests.post(f"{BASE_URL}/api/auth/login", data=data, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        login_res = r.json()
        assert "access_token" in login_res, "No access token in response"
        assert "user" in login_res, "No user info in response"
        log_result("Login API", "PASS", f"User {username} logged in, got JWT token")
        return login_res["access_token"], login_res["user"]
    except Exception as e:
        log_result("Login API", "FAIL", str(e))
        return None, None


def test_add_vault(token, master_password):
    print("\n=== TEST ADD VAULT ITEM ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        vault_data = {
            "item_name": "Test Gmail",
            "username": "test@gmail.com",
            "password": "SecretGmailPass123!",
            "notes": "My test email account",
            "category_id": 1
        }
        params = {"master_password": master_password}
        r = requests.post(
            f"{BASE_URL}/api/vault/items",
            json=vault_data,
            params=params,
            headers=headers,
            timeout=5
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        add_res = r.json()
        assert "vault_id" in add_res, "No vault_id in response"
        log_result("Add Vault API", "PASS", f"Vault item added, id: {add_res['vault_id']}")
        return add_res["vault_id"]
    except Exception as e:
        log_result("Add Vault API", "FAIL", str(e))
        return None


def test_get_vault_items(token):
    print("\n=== TEST GET VAULT ITEMS ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/vault/items", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        items = r.json()
        assert len(items) > 0, "Expected at least 1 vault item"
        log_result("Get Vault API", "PASS", f"Got {len(items)} vault items")
        return items
    except Exception as e:
        log_result("Get Vault API", "FAIL", str(e))
        return None


def test_decrypt_vault(token, vault_id, master_password):
    print("\n=== TEST DECRYPT VAULT ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"master_password": master_password}
        r = requests.get(
            f"{BASE_URL}/api/vault/items/{vault_id}",
            params=params,
            headers=headers,
            timeout=5
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        decrypted = r.json()
        assert decrypted["item_name"] == "Test Gmail", "Item name mismatch"
        assert decrypted["username"] == "test@gmail.com", "Username mismatch"
        assert decrypted["password"] == "SecretGmailPass123!", "Password mismatch"
        log_result("Decrypt Vault API (AES-GCM)", "PASS", "Item decrypted successfully")
        return True
    except Exception as e:
        log_result("Decrypt Vault API (AES-GCM)", "FAIL", str(e))
        return False


def test_audit_log(token):
    print("\n=== TEST AUDIT LOG ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/audit/logs", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        logs = r.json()
        assert len(logs) > 0, "Expected at least 1 audit log"
        log_result("Audit Log API", "PASS", f"Got {len(logs)} audit log entries")
        return True
    except Exception as e:
        log_result("Audit Log API", "FAIL", str(e))
        return False


def test_admin_permissions():
    print("\n=== TEST ADMIN PERMISSIONS ===")
    try:
        # Login as admin
        admin_token, admin_user = test_login("admin", "Admin123!")
        if not admin_token:
            log_result("Admin Login", "FAIL", "Admin login failed")
            return False
        
        # Admin should have empty vault
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = requests.get(f"{BASE_URL}/api/vault/items", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        items = r.json()
        assert len(items) == 0, "Admin should have empty vault"
        
        log_result("Admin Role - Vault Access", "PASS", "Admin cannot access other vaults")
        return True
    except Exception as e:
        log_result("Admin Role - Vault Access", "FAIL", str(e))
        return False


def test_auditor_permissions():
    print("\n=== TEST AUDITOR PERMISSIONS ===")
    try:
        auditor_token, auditor_user = test_login("auditor", "Audit123!")
        if not auditor_token:
            log_result("Auditor Login", "FAIL", "Auditor login failed")
            return False
        
        headers = {"Authorization": f"Bearer {auditor_token}"}
        
        # Check vault access (should be empty)
        r = requests.get(f"{BASE_URL}/api/vault/items", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        items = r.json()
        assert len(items) == 0, "Auditor should have empty vault"
        
        # Check audit log access
        r = requests.get(f"{BASE_URL}/api/audit/logs", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        logs = r.json()
        assert len(logs) > 0, "Auditor should see audit logs"
        
        log_result("Auditor Role", "PASS", "Auditor can see audit logs, no vault access")
        return True
    except Exception as e:
        log_result("Auditor Role", "FAIL", str(e))
        return False


def test_logout(token):
    print("\n=== TEST LOGOUT ===")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers, timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        log_result("Logout API", "PASS", "User logged out successfully")
        return True
    except Exception as e:
        log_result("Logout API", "FAIL", str(e))
        return False


def test_aes_gcm():
    print("\n=== TEST AES-GCM ENCRYPTION/DECRYPTION (Core) ===")
    try:
        from core.crypto_vault import CryptoVault
        test_data = "This is a secret message for testing AES-GCM encryption!"
        key = CryptoVault.derive_master_key("TestPass123!", b"salt123456789012")  # 16-byte salt
        
        encrypted, iv, auth_tag = CryptoVault.encrypt_aes_gcm(test_data, key)
        assert encrypted is not None, "Encryption failed"
        assert iv is not None, "IV not generated"
        assert auth_tag is not None, "Auth tag not generated"
        
        decrypted = CryptoVault.decrypt_aes_gcm(encrypted, iv, auth_tag, key)
        assert decrypted == test_data, "Decrypted data mismatch"
        
        log_result("AES-GCM Encryption/Decryption", "PASS", "Encrypt + decrypt working correctly")
        return True
    except Exception as e:
        log_result("AES-GCM Encryption/Decryption", "FAIL", str(e))
        return False


def test_tripledes():
    print("\n=== TEST TRIPLEDES ENCRYPTION/DECRYPTION (Core) ===")
    try:
        from core.crypto_vault import CryptoVault
        test_data = "This is a secret message for testing TripleDES!"
        # TripleDES needs 24-byte key
        key = CryptoVault.derive_master_key("TestPass123!", b"salt123456789012", key_size=24)
        
        encrypted, iv = CryptoVault.encrypt_3des_cbc(test_data, key)
        assert encrypted is not None, "Encryption failed"
        assert iv is not None, "IV not generated"
        
        decrypted = CryptoVault.decrypt_3des_cbc(encrypted, iv, key)
        assert decrypted == test_data, "Decrypted data mismatch"
        
        log_result("TripleDES Encryption/Decryption", "PASS", "Encrypt + decrypt working correctly")
        return True
    except Exception as e:
        log_result("TripleDES Encryption/Decryption", "FAIL", str(e))
        return False


def test_jwt_token():
    print("\n=== TEST JWT TOKEN ===")
    try:
        from jose import jwt
        from dotenv import load_dotenv
        import os
        load_dotenv()
        secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production-please")
        
        test_payload = {"sub": "test_jwt_user", "user_id": 999, "role_name": "User", "exp": datetime.utcnow().timestamp() + 3600}
        encoded = jwt.encode(test_payload, secret_key, algorithm="HS256")
        decoded = jwt.decode(encoded, secret_key, algorithms=["HS256"])
        
        assert decoded["sub"] == test_payload["sub"], "JWT subject mismatch"
        log_result("JWT Token", "PASS", "Token encode/decode working correctly")
        return True
    except Exception as e:
        log_result("JWT Token", "FAIL", str(e))
        return False


def run_full_test():
    print("=" * 80)
    print("FORTRESSVAULT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Test core system
    if not test_root():
        return
    test_categories()
    
    # Test crypto
    test_aes_gcm()
    test_tripledes()
    test_jwt_token()
    
    # Test user flow
    test_user, test_pass = test_register()
    if not test_user:
        return
    token, user = test_login(test_user, test_pass)
    if not token:
        return
    
    vault_id = test_add_vault(token, test_pass)
    if not vault_id:
        return
    test_get_vault_items(token)
    test_decrypt_vault(token, vault_id, test_pass)
    test_audit_log(token)
    test_logout(token)
    
    # Test admin and auditor roles
    test_admin_permissions()
    test_auditor_permissions()
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"PASS: {passed}/{total}")
    print(f"Completion: {round(passed/total*100, 2)}%")
    print("\nDetailed Results:")
    for r in results:
        print(f"  [{r['status']}] {r['component']}: {r['message']}")
    return passed, total


if __name__ == "__main__":
    run_full_test()

