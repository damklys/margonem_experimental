#!/usr/bin/env python3
"""Kraken API – serwer zbierania logów (demon systemd, sama biblioteka standardowa, Python 3.8+).

Launchery wysyłają paczki linii logów każdej postaci; serwer dopisuje je do plików
<data_dir>/logs/<świat>/<postać>.log (rotacja po przekroczeniu rozmiaru).

API (nagłówek: Authorization: Bearer <token>):
  GET  /api/v1/health                        – bez tokenu: {"ok": true, "version": ...}
  POST /api/v1/logs                          – {"source": "...", "entries": [{"char": "...", "world": "...", "lines": ["..."]}]}
                                               (opcjonalnie Content-Encoding: gzip)
  GET  /api/v1/chars                         – [{"world", "char", "bytes", "modified"}]
  GET  /api/v1/logs?world=W&char=C&tail=200  – ostatnie linie (text/plain)
"""
import argparse
import gzip
import hmac
import json
import logging
import os
import re
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

VERSION = "1.0.0"
log = logging.getLogger("kraken-api")

DEFAULTS = {
    "host": "127.0.0.1",          # za reverse proxy (Caddy/nginx z HTTPS); bez proxy: "0.0.0.0"
    "port": 8787,
    "data_dir": "/var/lib/kraken-api",
    "tokens": [],                 # dozwolone tokeny (launchery); pusty = API zamknięte
    "max_body_bytes": 4 * 1024 * 1024,
    "max_line_chars": 4000,
    "max_file_bytes": 50 * 1024 * 1024,   # rotacja pliku postaci
    "keep_rotated": 5,
}

_NAME_RE = re.compile(r"[^\w\-. ]+", re.UNICODE)


def safe_name(s, default):
    """Nazwa pliku/katalogu z nazwy postaci lub świata (bez ścieżek, znaków specjalnych i kropek na początku)."""
    s = _NAME_RE.sub("_", str(s or "")).strip(" ._")[:64]
    return s or default


class Store:
    """Dopisywanie linii do plików postaci; osobna blokada na plik, rotacja po rozmiarze."""

    def __init__(self, cfg):
        self.root = os.path.join(cfg["data_dir"], "logs")
        self.max_bytes = int(cfg["max_file_bytes"])
        self.keep = int(cfg["keep_rotated"])
        self.max_line = int(cfg["max_line_chars"])
        self._locks = {}
        self._guard = threading.Lock()
        os.makedirs(self.root, exist_ok=True)

    def path(self, world, char):
        return os.path.join(self.root, safe_name(world, "unknown"), safe_name(char, "unknown") + ".log")

    def _lock(self, path):
        with self._guard:
            return self._locks.setdefault(path, threading.Lock())

    def _rotate(self, path):
        for i in range(self.keep - 1, 0, -1):
            src, dst = f"{path}.{i}", f"{path}.{i + 1}"
            if os.path.exists(src):
                os.replace(src, dst)
        os.replace(path, f"{path}.1")

    def append(self, world, char, lines, source=""):
        path = self.path(world, char)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        clean = []
        for ln in lines:
            ln = str(ln).replace("\r", " ").replace("\n", " ")[: self.max_line]
            if ln.strip():
                clean.append(ln + "\n")
        if not clean:
            return 0
        data = "".join(clean).encode("utf-8")
        with self._lock(path):
            try:
                if os.path.getsize(path) + len(data) > self.max_bytes:
                    self._rotate(path)
            except FileNotFoundError:
                pass
            with open(path, "ab") as f:
                f.write(data)
        return len(clean)

    def chars(self):
        out = []
        for world in sorted(os.listdir(self.root)):
            wdir = os.path.join(self.root, world)
            if not os.path.isdir(wdir):
                continue
            for fn in sorted(os.listdir(wdir)):
                if fn.endswith(".log"):
                    st = os.stat(os.path.join(wdir, fn))
                    out.append({"world": world, "char": fn[:-4], "bytes": st.st_size,
                                "modified": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime))})
        return out

    def tail(self, world, char, n):
        path = self.path(world, char)
        if not os.path.exists(path):
            return None
        n = max(1, min(int(n), 5000))
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size, block, data = f.tell(), 64 * 1024, b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
        return b"\n".join(data.splitlines()[-n:]).decode("utf-8", "replace") + "\n"


def make_handler(cfg, store):
    tokens = [t for t in cfg["tokens"] if t]

    class Handler(BaseHTTPRequestHandler):
        server_version = f"KrakenAPI/{VERSION}"
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):   # dziennik dostępu do journald (poziom DEBUG)
            log.debug("%s %s", self.address_string(), fmt % args)

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            raw = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _authorized(self):
            auth = self.headers.get("Authorization", "")
            got = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
            return bool(got) and any(hmac.compare_digest(got, t) for t in tokens)

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/api/v1/health":
                return self._send(200, {"ok": True, "version": VERSION})
            if not self._authorized():
                return self._send(401, {"ok": False, "error": "unauthorized"})
            if url.path == "/api/v1/chars":
                return self._send(200, store.chars())
            if url.path == "/api/v1/logs":
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                text = store.tail(q.get("world", ""), q.get("char", ""), q.get("tail", 200))
                if text is None:
                    return self._send(404, {"ok": False, "error": "not found"})
                return self._send(200, text, "text/plain; charset=utf-8")
            self._send(404, {"ok": False, "error": "not found"})

        def do_POST(self):
            url = urlparse(self.path)
            if url.path != "/api/v1/logs":
                return self._send(404, {"ok": False, "error": "not found"})
            if not self._authorized():
                return self._send(401, {"ok": False, "error": "unauthorized"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > cfg["max_body_bytes"]:
                return self._send(413, {"ok": False, "error": "body size"})
            raw = self.rfile.read(length)
            try:
                if self.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)[: cfg["max_body_bytes"] * 8]
                body = json.loads(raw.decode("utf-8"))
                entries = body.get("entries") or []
                assert isinstance(entries, list)
            except Exception:
                return self._send(400, {"ok": False, "error": "bad json"})
            written = 0
            source = str(body.get("source", ""))[:64]
            for e in entries:
                if isinstance(e, dict) and isinstance(e.get("lines"), list):
                    written += store.append(e.get("world", ""), e.get("char", ""), e["lines"], source)
            log.info("logi: %d linii od %s (%s)", written, source or "?", self.address_string())
            self._send(200, {"ok": True, "written": written})

    return Handler


def load_config(path):
    cfg = dict(DEFAULTS)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    env = os.environ
    if env.get("KRAKEN_API_HOST"):
        cfg["host"] = env["KRAKEN_API_HOST"]
    if env.get("KRAKEN_API_PORT"):
        cfg["port"] = int(env["KRAKEN_API_PORT"])
    if env.get("KRAKEN_API_DATA"):
        cfg["data_dir"] = env["KRAKEN_API_DATA"]
    if env.get("KRAKEN_API_TOKENS"):
        cfg["tokens"] = [t.strip() for t in env["KRAKEN_API_TOKENS"].split(",") if t.strip()]
    return cfg


def main():
    ap = argparse.ArgumentParser(description="Kraken API – zbieranie logów")
    ap.add_argument("--config", default=os.environ.get("KRAKEN_API_CONFIG", "/etc/kraken-api/config.json"))
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    cfg = load_config(args.config)
    if not cfg["tokens"]:
        log.warning("brak tokenów w konfiguracji – API przyjmie tylko /api/v1/health")
    store = Store(cfg)
    httpd = ThreadingHTTPServer((cfg["host"], int(cfg["port"])), make_handler(cfg, store))
    httpd.daemon_threads = True

    def stop(*_):
        log.info("zatrzymuję serwer")
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log.info("Kraken API %s na %s:%s, dane: %s", VERSION, cfg["host"], cfg["port"], cfg["data_dir"])
    httpd.serve_forever()
    httpd.server_close()


if __name__ == "__main__":
    main()
