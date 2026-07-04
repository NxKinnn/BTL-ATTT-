
import http.server
import socketserver
import os

PORT = 5500
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
os.chdir(frontend_dir)
Handler = http.server.SimpleHTTPRequestHandler

print(f"Starting frontend server at http://localhost:{PORT}", flush=True)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Frontend server is running!", flush=True)
    httpd.serve_forever()
