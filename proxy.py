import http.server
import socketserver
import urllib.request
import ssl

# ========== CONFIGURATION ==========
TARGET_HOST = "x2.mjpax.eu.cc"
TARGET_PORT = 26503         # change to your 3x-ui panel port (usually 54321)
TARGET_USE_SSL = True       # set False if your panel uses http://
LISTEN_PORT = 8080          # local port inside Codespace
# ===================================

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()

    def do_POST(self):
        self.proxy_request()

    def do_PUT(self):
        self.proxy_request()

    def do_DELETE(self):
        self.proxy_request()

    def do_HEAD(self):
        self.proxy_request()

    def proxy_request(self):
        # Build target URL
        protocol = "https" if TARGET_USE_SSL else "http"
        url = f"{protocol}://{TARGET_HOST}:{TARGET_PORT}{self.path}"

        # Read request body if any
        content_length = self.headers.get('Content-Length')
        body = self.rfile.read(int(content_length)) if content_length else None

        # Forward the request
        req = urllib.request.Request(url, data=body, method=self.command)
        # Copy relevant headers
        for header, value in self.headers.items():
            if header.lower() not in ('host', 'connection'):
                req.add_header(header, value)

        # Disable SSL verification if needed (e.g., self-signed cert)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ('transfer-encoding', 'connection'):
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Proxy error: {e}".encode())

# Run server
with socketserver.TCPServer(("", LISTEN_PORT), Proxy) as httpd:
    print(f"🚀 Reverse proxy running on port {LISTEN_PORT}")
    print(f"   Forwarding to {TARGET_HOST}:{TARGET_PORT}")
    httpd.serve_forever()
