"""VoiceStudio client — the user's free, local voice engine (OpenAPI v0.5.7).

Base URL: $CATANA_VOICE_STUDIO_URL (default http://127.0.0.1:3900). Loopback needs no auth; a remote/LAN instance
needs $OMNIVOICE_API_KEY sent as a bearer token. Standard library only.

Used for: voiceovers (POST /v1/audio/speech), voice selection (/v1/audio/voices, /archetypes, /profiles), voice design
(/design/describe), fitting a line to a time slot (/tools/rate-fit). VoiceStudio has no SFX or music generation.

This runs where VoiceStudio is reachable — Claude Code on the same computer. A cloud session cannot see the user's
localhost; the client reports that as `unavailable`, never as a success.
"""
import io
import json
import os
import re
import socket
import urllib.error
import urllib.request
import wave

DEFAULT_URL = "http://127.0.0.1:3900"
MAX_CHARS = 4096
FORMATS = ("mp3", "opus", "aac", "flac", "wav", "pcm")


class VoiceStudioError(Exception):
    """category: unavailable | auth | invalid_input | server_error | timeout | network | unknown"""

    def __init__(self, message, category="unknown", status=None):
        super().__init__(message)
        self.category = category
        self.status = status


class VoiceStudio:
    def __init__(self, base_url=None, api_key=None, timeout=300):
        self.base_url = (base_url or os.environ.get("CATANA_VOICE_STUDIO_URL") or DEFAULT_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else os.environ.get("OMNIVOICE_API_KEY")
        self.timeout = timeout

    # ------------------------------------------------------------------ transport
    def _request(self, method, path, body=None, raw=False, timeout=None):
        url = self.base_url + path
        data, headers = None, {"Accept": "application/json" if not raw else "*/*"}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                payload = r.read()
                ctype = r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf8", "replace")[:500]
            except Exception:
                pass
            cat = ("auth" if e.code in (401, 403) else "invalid_input" if e.code in (400, 404, 409, 413, 422)
                   else "server_error" if e.code >= 500 else "unknown")
            raise VoiceStudioError(f"VoiceStudio {method} {path} -> HTTP {e.code}: {detail}", cat, e.code) from None
        except (socket.timeout, TimeoutError):
            raise VoiceStudioError(f"VoiceStudio {method} {path} timed out", "timeout") from None
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                raise VoiceStudioError(f"VoiceStudio {method} {path} timed out", "timeout") from None
            raise VoiceStudioError(f"VoiceStudio is not reachable at {self.base_url} ({reason}). Start the VoiceStudio app, "
                                   f"or set CATANA_VOICE_STUDIO_URL. A cloud session cannot reach your computer's localhost.",
                                   "unavailable") from None
        if raw:
            return payload, ctype
        if not payload:
            return None
        try:
            return json.loads(payload)
        except ValueError:
            return payload.decode("utf8", "replace")

    # ------------------------------------------------------------------ discovery
    def health(self):
        return self._request("GET", "/health", timeout=5)

    def available(self):
        try:
            self.health()
            return True
        except VoiceStudioError:
            return False

    def capabilities(self):
        return self._request("GET", "/v1/audio/capabilities")

    def voices(self):
        return self._request("GET", "/v1/audio/voices")

    def models(self):
        return self._request("GET", "/v1/models")

    def profiles(self):
        return self._request("GET", "/profiles")

    def archetypes(self, q=None, limit=20, **filters):
        params = {"q": q, "limit": limit, **filters}
        qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items() if v is not None)
        return self._request("GET", "/archetypes" + (f"?{qs}" if qs else ""))

    def describe_voice(self, description):
        return self._request("POST", "/design/describe", {"description": description})

    def rate_fit(self, text, slot_seconds, target_lang="en"):
        return self._request("POST", "/tools/rate-fit", {"text": text, "slot_seconds": float(slot_seconds), "target_lang": target_lang})

    def direction(self, text):
        return self._request("POST", "/tools/direction", {"text": text})

    # ------------------------------------------------------------------ synthesis
    def speech(self, text, out_path, voice="default", model="omnivoice", instructions=None, instruct=None,
               response_format=None, speed=1.0, language=None, duration=None, seed=None):
        """Synthesize `text` to `out_path`. Scripts over 4096 chars are split on sentence boundaries and joined (WAV).

        Returns {'path', 'bytes', 'format', 'chunks', 'voice', 'model'}.
        """
        if not text or not text.strip():
            raise VoiceStudioError("speech() needs non-empty text", "invalid_input")
        if not (0.25 <= float(speed) <= 4.0):
            raise VoiceStudioError("speed must be between 0.25 and 4.0", "invalid_input")
        fmt = response_format or (os.path.splitext(out_path)[1].lstrip(".").lower() or "wav")
        if fmt not in FORMATS:
            raise VoiceStudioError(f"format must be one of {FORMATS}", "invalid_input")
        chunks = split_text(text, MAX_CHARS - 96)
        if len(chunks) > 1 and fmt != "wav":
            raise VoiceStudioError(f"text is {len(text)} chars (> {MAX_CHARS}); long scripts are joined as WAV — use a .wav output",
                                   "invalid_input")
        if duration is not None and len(chunks) > 1:
            raise VoiceStudioError("a target duration can only be set for a single chunk (<= 4096 chars)", "invalid_input")
        audio = []
        for c in chunks:
            body = {"model": model, "input": c, "voice": voice, "response_format": fmt, "speed": float(speed)}
            for k, v in (("instructions", instructions), ("instruct", instruct), ("language", language),
                         ("duration", duration), ("seed", seed)):
                if v is not None:
                    body[k] = v
            data, ctype = self._request("POST", "/v1/audio/speech", body, raw=True)
            if not data or ctype.startswith("application/json"):
                raise VoiceStudioError(f"VoiceStudio returned no audio (Content-Type {ctype!r}): {data[:200]!r}", "server_error")
            audio.append(data)
        blob = audio[0] if len(audio) == 1 else join_wavs(audio)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(blob)
        return {"path": out_path, "bytes": len(blob), "format": fmt, "chunks": len(chunks), "voice": voice, "model": model}


def split_text(text, limit):
    """Split on sentence boundaries into chunks of at most `limit` chars (hard-split only if a sentence is longer)."""
    text = text.strip()
    if len(text) <= limit:
        return [text]
    sentences = re.split(r"(?<=[.!?…])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        while len(s) > limit:
            cut = s.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if len(cur) + len(s) + 1 > limit:
            chunks.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


def join_wavs(blobs):
    params, frames = None, []
    for b in blobs:
        with wave.open(io.BytesIO(b)) as w:
            p = w.getparams()[:3]
            if params and p != params:
                raise VoiceStudioError("cannot join WAV chunks with different formats", "server_error")
            params = p
            frames.append(w.readframes(w.getnframes()))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(params[0]); w.setsampwidth(params[1]); w.setframerate(params[2])
        for f in frames:
            w.writeframes(f)
    return out.getvalue()
