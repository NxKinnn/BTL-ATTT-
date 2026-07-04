
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = "frontend"

os.chdir(DIRECTORY)

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend server running at http://localhost:{PORT}")
    httpd.serve_forever()
