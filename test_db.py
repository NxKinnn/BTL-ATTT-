
from config.database import execute_query, execute_non_query
from core.crypto_vault import CryptoVault
from services.auth_service import AuthService

print("Testing database connection...")

# Test 1: Check if roles exist
print("\n1. Checking roles:")
roles = execute_query("SELECT * FROM roles")
print(f"Roles found: {roles}")

# Test 2: Check if categories exist
print("\n2. Checking categories:")
categories = execute_query("SELECT * FROM categories")
print(f"Categories found: {categories}")

# Test 3: Check if cipher configs exist
print("\n3. Checking cipher configs:")
ciphers = execute_query("SELECT * FROM cipher_configs")
print(f"Ciphers found: {ciphers}")

# Test 4: Check if log actions exist
print("\n4. Checking log actions:")
actions = execute_query("SELECT * FROM log_actions")
print(f"Actions found: {actions}")
