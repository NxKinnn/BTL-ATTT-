
"""
Comprehensive Security Test Suite for FortressVault
Covers: valid data, tampered data, wrong password, invalid signature, replay attacks, invalid permissions
"""
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from jose import jwt, JWTError

# Load env vars
load_dotenv()
BASE_URL = "http://127.0.0.1:8000"
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production-please")

# Test results storage
test_results = []


def log_test_result(test_name, status, details=""):
    test_results.append({"test": test_name, "status": status, "details": details})
    print(f"\n=== {test_name} ===")
    print(f"STATUS: {status}")
    if details:
        print(f"DETAILS: {details}")


def test_valid_data_flow():
    """1. Test with valid data"""
    try:
        # Register test user
        username = f"valid_user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        password = "ValidPass123!"
        register_res = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": username,
            "password": password
        })
        assert register_res.status_code == 200, "Registration failed"
        
        # Login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": username,
            "password": password
        })
        assert login_res.status_code == 200, "Login failed"
        token = login_res.json()["access_token"]
        
        # Add vault item
        vault_res = requests.post(f"{BASE_URL}/api/vault/items", json={
            "item_name": "Valid Test Item",
            "username": "valid@test.com",
            "password": "Secret123!",
            "notes": "Valid test notes"
        }, params={"master_password": password}, headers={"Authorization": f"Bearer {token}"})
        assert vault_res.status_code == 200, "Add vault failed"
        vault_id = vault_res.json()["vault_id"]
        
        # Decrypt vault
        decrypt_res = requests.get(f"{BASE_URL}/api/vault/items/{vault_id}", 
                                   params={"master_password": password},
                                   headers={"Authorization": f"Bearer {token}"})
        assert decrypt_res.status_code == 200, "Decrypt failed"
        decrypted = decrypt_res.json()
        assert decrypted["item_name"] == "Valid Test Item", "Data mismatch"
        
        log_test_result("1. Valid Data Flow", "PASS")
        return token, vault_id, password
    except Exception as e:
        log_test_result("1. Valid Data Flow", "FAIL", str(e))
        return None, None, None


def test_tampered_data(token, vault_id, master_password):
    """2. Test tampered data (modify ciphertext directly in DB)"""
    try:
        from config.database import execute_query, execute_non_query
        
        # First get original ciphertext
        vault_data = execute_query("SELECT vault_id, encrypted_password, iv, auth_tag FROM vault_credentials WHERE vault_id = ?", (vault_id,))
        if not vault_data:
            log_test_result("2. Tampered Data Test", "FAIL", "Vault item not found")
            return
        
        original = vault_data[0]
        
        # Tamper the ciphertext (flip first byte)
        tampered_encrypted = original["encrypted_password"]
        if len(tampered_encrypted) >= 2:
            tampered_encrypted = ("0" if tampered_encrypted[0] == "1" else "1") + tampered_encrypted[1:]
        
        # Update DB with tampered data
        execute_non_query("""
            UPDATE vault_credentials 
            SET encrypted_password = ?
            WHERE vault_id = ?
        """, (tampered_encrypted, vault_id))
        
        # Try to decrypt
        decrypt_res = requests.get(f"{BASE_URL}/api/vault/items/{vault_id}",
                                   params={"master_password": master_password},
                                   headers={"Authorization": f"Bearer {token}"})
        
        # Should fail to decrypt or return error
        assert decrypt_res.status_code != 200 or "Error" in str(decrypt_res.text), "Tampered data decrypted successfully!"
        
        log_test_result("2. Tampered Data Test", "PASS", "System detected tampered data")
    except Exception as e:
        log_test_result("2. Tampered Data Test", "FAIL", str(e))
    finally:
        # Restore original data
        try:
            execute_non_query("""
                UPDATE vault_credentials 
                SET encrypted_password = ?
                WHERE vault_id = ?
            """, (original["encrypted_password"], vault_id))
        except:
            pass


def test_wrong_password(token, vault_id):
    """3. Test wrong master password"""
    try:
