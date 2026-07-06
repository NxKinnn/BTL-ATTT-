
import http.server
import socketserver
import os
import mimetypes

# Ensure correct MIME types on Windows
mimetypes.add_type('text/html; charset=utf-8', '.html')
mimetypes.add_type('text/css; charset=utf-8', '.css')
mimetypes.add_type('application/javascript; charset=utf-8', '.js')
mimetypes.add_type('application/json; charset=utf-8', '.json')

PORT = 3000
DIRECTORY = "frontend"
os.chdir(DIRECTORY)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '': 'application/octet-stream',
    }
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
    print(f"Frontend server running at http://localhost:{PORT}")
    httpd.serve_forever()
