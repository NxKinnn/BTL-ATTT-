
from config.database import execute_query, execute_non_query

print("Testing config.database module...")

try:
    print("\n1. Testing SELECT from roles...")
    roles = execute_query("SELECT * FROM roles")
    print(f"   Got {len(roles)} roles:")
    for r in roles:
        print(f"   - {r}")
        
    print("\n2. Testing SELECT from categories...")
    cats = execute_query("SELECT * FROM categories")
    print(f"   Got {len(cats)} categories")
    
    print("\n3. Testing SELECT from cipher_configs...")
    ciphers = execute_query("SELECT * FROM cipher_configs")
    print(f"   Got {len(ciphers)} cipher configs")
    
    print("\n4. Testing SELECT from log_actions...")
    actions = execute_query("SELECT * FROM log_actions")
    print(f"   Got {len(actions)} log actions")
    
    print("\n✅ All basic queries passed!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

