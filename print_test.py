
import sys

print("Hello from Python!", flush=True)
sys.stdout.flush()
print("Testing 123...", flush=True)

try:
    import requests
    print("Requests imported!", flush=True)
    
    r = requests.get("http://127.0.0.1:8000/", timeout=3)
    print("Got response!", flush=True)
    print(r.status_code, flush=True)
    print(r.text, flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
