from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

# ── Set this after Railway is deployed ──────────────────────
# Add this as an environment variable in Vercel:
# Key:   RAILWAY_URL
# Value: https://your-app.up.railway.app
RAILWAY_URL = os.environ.get("RAILWAY_URL", "")


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        if not RAILWAY_URL:
            self._json(503, {
                "error": "RAILWAY_URL not configured. Add it as a Vercel environment variable."
            })
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "application/octet-stream")

            req = urllib.request.Request(
                url=f"{RAILWAY_URL}/extract_contract",
                data=body,
                headers={"Content-Type": content_type},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                result = resp.read()
                self._raw(200, result)

        except urllib.error.HTTPError as e:
            self._json(e.code, {"error": str(e)})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _json(self, code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _raw(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")