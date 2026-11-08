#!/usr/bin/env python3
"""DOM-F1 PoC server: two origins (8801 publisher / 8802 ad frame), no-store, report beacon."""
import http.server, socketserver, threading, os, sys, time, random

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "rounds.log")

class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def translate_path(self, path):
        root = self.server.serve_root
        p = path.split("?", 1)[0].split("#", 1)[0]
        return os.path.join(root, p.lstrip("/"))
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
    def log_message(self, fmt, *args):
        pass  # quiet
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/api/report"):
            self._report()
            return
        return self._serve(path)
    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path.startswith("/api/report"):
            self._report(body=True)
            return
        self.send_response(405); self.send_header("Content-Length", "0"); self.end_headers()
    def _report(self, body=False):
        if body:
            try: self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            except Exception: pass
        with open(LOG, "a") as f:
            f.write("%s %s\n" % (time.strftime("%H:%M:%S"), self.path.split("?", 1)[1] if "?" in self.path else ""))
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()
    def _serve(self, path):
        if path.startswith("/api/junk"):
            body = os.urandom(256)
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()
def serve(port, root):
    class S(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
    httpd = S(("127.0.0.1", port), Handler)
    httpd.serve_root = root
    httpd.serve_forever()

if __name__ == "__main__":
    open(LOG, "w").close()
    t1 = threading.Thread(target=serve, args=(8801, os.path.join(ROOT, "origin-a")), daemon=True)
    t2 = threading.Thread(target=serve, args=(8802, os.path.join(ROOT, "origin-b")), daemon=True)
    t1.start(); t2.start()
    print("serving 8801 (publisher) + 8802 (ad) — rounds logged to rounds.log", flush=True)
    while True:
        time.sleep(3600)
