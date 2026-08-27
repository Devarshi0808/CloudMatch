"""Dependency-free local server mirroring the Vercel routes."""
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from api.index import handler as ApiHandler

PUBLIC = Path(__file__).parent / "public"
ASSETS = {"/": ("index.html", "text/html; charset=utf-8"), "/react-app.js": ("react-app.js", "text/javascript; charset=utf-8"), "/react-app.css": ("react-app.css", "text/css; charset=utf-8")}

class DevHandler(ApiHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"): return super().do_GET()
        asset, content_type = ASSETS.get(path, ASSETS["/"])
        body = (PUBLIC / asset).read_bytes()
        self.send_response(200); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

if __name__ == "__main__":
    print("CloudMatch dev server: http://127.0.0.1:8000", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8000), DevHandler).serve_forever()
