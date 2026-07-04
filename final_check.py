
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

print("=== Final Check ===")
try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"Backend server: UP (Status {r.status_code})")
    print(f"Response: {r.text}")
    
    print("\nTesting categories endpoint...")
    cats = requests.get(f"{BASE_URL}/api/vault/categories", timeout=5)
    print(f"Categories: {cats.json()}")
    
    print("\n✅ All systems operational!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    sys.exit(1)
