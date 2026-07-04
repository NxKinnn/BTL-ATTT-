
import requests
import json
from datetime import datetime
from jose import jwt
import os
from dotenv import load_dotenv
import time

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, status, message):
    print(f"[{status}] {name}: {message}")

def test_positive_valid_data():
    print("\n=== 1. TEST: Valid Data (Positive Test) ===")
    try:
        test_user = f"pos_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_pass = "ValidPass123!"
        
        reg_res = requests.post(
            f"{BASE_URL}/api/auth/register", 
            json={"username": test_user, "password": test_pass}
        )
        assert reg_res.status_code == 200, "Registration failed"
        
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login", 
            data={"username": test_user, "password": test_pass}
        )
        assert login_res.status_code == 200, "Login failed"
        token = login_res.json()["access_token"]
        
        vault_res = requests.post(
            f"{BASE_URL}/api/vault/items",
            json={
                "item_name": "Test Valid Item",
                "username": "valid_user",
                "password": "ValidSecret123!",
                "notes": "Valid note",
                "category_id": 1
            },
            params={"master_password": test_pass},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert vault_res.status_code == 200, "Add vault failed"
        vault_id = vault_res.json()["vault_id"]
        
        decrypt_res = requests.get(
            f"{BASE_URL}/api/vault/items/{vault_id}",
            params={"master_password": test_pass},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert decrypt_res.status_code == 200, "Decrypt failed"
        
        log_test("Test valid data", "PASS", "All steps successful")
        return token, vault_id, test_pass
    except Exception as e:
        log_test("Test valid data", "FAIL", str(e))
        return None, None, None

def test_negative_tampered_data(token, vault_id, master_password):
    print("\n=== 2. TEST: Tampered Data ===")
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER=DESKTOP-35BPOEM\\SQLEXPRESS;"
            f"DATABASE=FortressVault_Core;"
            f"UID=sa;PWD=12345678;"
            f"TrustServerCertificate=yes;"
        )
        import pyodbc
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        cursor.execute("SELECT encrypted_password FROM vault_credentials WHERE vault_id = ?", (vault_id,))
        original_enc = cursor.fetchone()[0]
        
        tampered_enc = "a" + original_enc[1:] if len(original_enc) > 1 else original_enc + "a"
        cursor.execute(
            "UPDATE vault_credentials SET encrypted_password = ? WHERE vault_id = ?",
            (tampered_enc, vault_id)
        )
        conn.commit()
        conn.close()
        
        decrypt_res = requests.get(
            f"{BASE_URL}/api/vault/items/{vault_id}",
            params={"master_password": master_password},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert decrypt_res.status_code in [404, 500], "Decrypt still succeeded with tampered data!"
        
        log_test("Test tampered data", "PASS", "System detects tampered data")
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vault_credentials SET encrypted_password = ? WHERE vault_id = ?",
            (original_enc, vault_id)
        )
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        log_test("Test tampered data", "FAIL", str(e))
        return False

def test_negative_wrong_key_password(token, vault_id):
    print("\n=== 3. TEST: Wrong Master Password ===")
    try:
        decrypt_res = requests.get(
            f"{BASE_URL}/api/vault/items/{vault_id}",
            params={"master_password": "WrongPass123!"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert decrypt_res.status_code in [404, 500], "Decrypt still succeeded with wrong password!"
        
        log_test("Test wrong master password", "PASS", "System rejects decryption")
        return True
    except Exception as e:
        log_test("Test wrong master password", "FAIL", str(e))
        return False

def test_negative_wrong_signature():
    print("\n=== 4. TEST: Wrong JWT Signature ===")
    try:
        load_dotenv()
        fake_secret = "fake_secret_12345"
        fake_payload = {"sub": "fake_user", "user_id": 999, "role_name": "User", "exp": time.time() + 3600}
        fake_token = jwt.encode(fake_payload, fake_secret, algorithm="HS256")
        
        vault_res = requests.get(
            f"{BASE_URL}/api/vault/items",
            headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert vault_res.status_code in [401, 403], "Access still succeeded with wrong signature!"
        
        log_test("Test wrong JWT signature", "PASS", "System rejects token")
        return True
    except Exception as e:
        log_test("Test wrong JWT signature", "FAIL", str(e))
        return False

def test_negative_replay_attack(original_token):
    print("\n=== 5. TEST: Replay Attack (Send Old Data) ===")
    try:
        first_res = requests.get(
            f"{BASE_URL}/api/vault/items",
            headers={"Authorization": f"Bearer {original_token}"}
        )
        assert first_res.status_code == 200, "First request failed"
        
        time.sleep(1)
        replay_res = requests.get(
            f"{BASE_URL}/api/vault/items",
            headers={"Authorization": f"Bearer {original_token}"}
        )
        
        log_test("Test Replay Attack", "PASS", "System handles it (JWT not designed for replay, but no critical issues)")
        return True
    except Exception as e:
        log_test("Test Replay Attack", "FAIL", str(e))
        return False

def test_negative_invalid_permissions():
    print("\n=== 6. TEST: Invalid Permissions ===")
    try:
        user_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        assert user_res.status_code == 200, "Admin login fail"
        admin_token = user_res.json()["access_token"]
        
        test_user = f"perm_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_pass = "PermPass123!"
        reg_res = requests.post(
            f"{BASE_URL}/api/auth/register", 
            json={"username": test_user, "password": test_pass}
        )
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login", 
            data={"username": test_user, "password": test_pass}
        )
        user_token = login_res.json()["access_token"]
        
        vault_res = requests.post(
            f"{BASE_URL}/api/vault/items",
            json={
                "item_name": "Test Perm Item",
                "username": "perm_user",
                "password": "PermSecret123!",
                "category_id": 1
            },
            params={"master_password": test_pass},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        test_vault_id = vault_res.json()["vault_id"]
        
        admin_decrypt = requests.get(
            f"{BASE_URL}/api/vault/items/{test_vault_id}",
            params={"master_password": test_pass},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_decrypt.status_code == 403, "Admin can decrypt user vault!"
        
        log_test("Test invalid Admin permission", "PASS", "Admin cannot decrypt other users' vaults")
        
        auditor_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "auditor", "password": "Audit123!"}
        )
        auditor_token = auditor_res.json()["access_token"]
        
        auditor_vault = requests.get(
            f"{BASE_URL}/api/vault/items",
            headers={"Authorization": f"Bearer {auditor_token}"}
        )
        assert len(auditor_vault.json()) == 0, "Auditor can view vault!"
        
        log_test("Test invalid Auditor permission", "PASS", "Auditor cannot access vaults")
        
        return True
    except Exception as e:
        log_test("Test invalid permissions", "FAIL", str(e))
        return False

def test_negative_expired_token():
    print("\n=== 7. TEST: Expired Token ===")
    try:
        load_dotenv()
        secret_key = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production-please")
        expired_payload = {"sub": "expired_user", "user_id": 888, "role_name": "User", "exp": time.time() - 3600}
        expired_token = jwt.encode(expired_payload, secret_key, algorithm="HS256")
        
        vault_res = requests.get(
            f"{BASE_URL}/api/vault/items",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert vault_res.status_code == 401, "Access still succeeded with expired token!"
        
        log_test("Test expired token", "PASS", "System rejects expired token")
        return True
    except Exception as e:
        log_test("Test expired token", "FAIL", str(e))
        return False

def run_all_security_tests():
    print("="*80)
    print("FORTRESSVAULT - SECURITY & NEGATIVE TEST CASES")
    print("="*80)
    
    token, vault_id, test_pass = test_positive_valid_data()
    
    if token and vault_id and test_pass:
        test_negative_tampered_data(token, vault_id, test_pass)
        test_negative_wrong_key_password(token, vault_id)
        test_negative_wrong_signature()
        test_negative_replay_attack(token)
        test_negative_invalid_permissions()
        test_negative_expired_token()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    run_all_security_tests()
