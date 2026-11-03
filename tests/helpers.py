"""Shared test helpers: import path, temp dirs, and a mock VoiceStudio server built from its OpenAPI (v0.5.7)."""
import io
import json
import math
import os
import struct
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
SCRIPTS = os.path.join(ROOT, "scripts")


def tmpdir():
    return tempfile.mkdtemp(prefix="catana_test_")


def wav_bytes(seconds=0.5, sr=24000, freq=220.0):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        n = int(seconds * sr)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / sr))) for i in range(n)))
    return buf.getvalue()


class MockVoiceStudio:
    """Implements the VoiceStudio endpoints CATANA uses, with switchable failure modes.

    fail: None | 'server' (500 on speech) | 'auth' (require bearer token 'secret') | 'json' (speech returns JSON, no audio)
    """

    def __init__(self, fail=None, api_key=None):
        self.fail = fail
        self.api_key = api_key
        self.requests = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body, ctype="application/json"):
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _auth_ok(self):
                if outer.api_key and self.headers.get("Authorization") != f"Bearer {outer.api_key}":
                    self._send(401, {"detail": "Not authenticated"})
                    return False
                return True

            def do_GET(self):
                outer.requests.append(("GET", self.path, None, dict(self.headers)))
                if not self._auth_ok():
                    return
                if self.path == "/health":
                    return self._send(200, {"status": "ok"})
                if self.path == "/v1/audio/voices":
                    return self._send(200, {"voices": [{"id": "default", "name": "Default"}, {"id": "narrator-m", "name": "Narrator M"}]})
                if self.path.startswith("/archetypes"):
                    return self._send(200, {"items": [{"id": "warm-narrator", "name": "Warm narrator"}], "total": 1})
                if self.path == "/v1/audio/capabilities":
                    return self._send(200, {"protocol": "voicestudio.speech.v1", "service_version": "0.5.7"})
                self._send(404, {"detail": "Not Found"})

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                outer.requests.append(("POST", self.path, body, dict(self.headers)))
                if not self._auth_ok():
                    return
                if self.path == "/v1/audio/speech":
                    if not body.get("input"):
                        return self._send(422, {"detail": [{"loc": ["body", "input"], "msg": "Field required", "type": "missing"}]})
                    if len(body["input"]) > 4096:
                        return self._send(422, {"detail": [{"msg": "String should have at most 4096 characters"}]})
                    if outer.fail == "server":
                        return self._send(500, {"detail": "engine crashed"})
                    if outer.fail == "json":
                        return self._send(200, {"detail": "queued"})
                    if body.get("response_format", "mp3") == "wav":
                        return self._send(200, wav_bytes(0.3), "audio/wav")
                    return self._send(200, b"ID3fake-mp3-bytes", "audio/mpeg")
                if self.path == "/tools/rate-fit":
                    words = len(body.get("text", "").split())
                    return self._send(200, {"fits": words / 2.5 <= body.get("slot_seconds", 0), "estimated_seconds": round(words / 2.5, 2)})
                if self.path == "/design/describe":
                    return self._send(200, {"attrs": {"Gender": "male"}, "instruct": "male, low pitch", "matched": [], "unmatched": []})
                self._send(404, {"detail": "Not Found"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *a):
        self.server.shutdown()
        self.server.server_close()


def free_port_url():
    """A localhost URL where nothing listens (connection refused)."""
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return f"http://127.0.0.1:{port}"
