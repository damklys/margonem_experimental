"""Wysyłka logów postaci na serwer Kraken API (kraken_api_server) – w tle, paczkami, z ponawianiem.

Konfiguracja: api.json obok launchera (plik lokalny, poza gitem):
    {"url": "https://api.twojadomena.pl", "token": "..."}
Bez pliku (albo bez url/token) wysyłka jest wyłączona.
"""
import gzip
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import deque

_BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_BASE, "api.json")
MAX_QUEUE = 50_000          # linii w kolejce (gdy serwer nieosiągalny – najstarsze odpadają)
BATCH = 2_000               # linii w jednym żądaniu
FLUSH_EVERY = 3.0           # s


class LogShipper:
    def __init__(self):
        self.url = ""
        self.token = ""
        self.source = socket.gethostname()[:64]
        self._q = deque(maxlen=MAX_QUEUE)     # (world, char, line)
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._thread = None
        self.last_error = ""
        self.sent = 0
        self.reload()

    def reload(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
        self.url = str(cfg.get("url", "")).rstrip("/")
        self.token = str(cfg.get("token", ""))
        if cfg.get("source"):
            self.source = str(cfg["source"])[:64]
        if self.enabled and not self._thread:
            self._thread = threading.Thread(target=self._run, name="log-shipper", daemon=True)
            self._thread.start()

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.token)

    def add(self, world: str, char: str, line: str):
        if not self.enabled or not line or not line.strip():
            return
        with self._lock:
            self._q.append((world or "unknown", char or "unknown", line.rstrip("\n")))
        if len(self._q) >= BATCH:
            self._wake.set()

    def _take(self):
        with self._lock:
            items = [self._q.popleft() for _ in range(min(BATCH, len(self._q)))]
        groups = {}
        for world, char, line in items:
            groups.setdefault((world, char), []).append(line)
        return items, [{"world": w, "char": c, "lines": ls} for (w, c), ls in groups.items()]

    def _put_back(self, items):
        with self._lock:
            for it in reversed(items):
                if len(self._q) < MAX_QUEUE:
                    self._q.appendleft(it)

    def _post(self, entries):
        body = gzip.compress(json.dumps({"source": self.source, "entries": entries}, ensure_ascii=False).encode("utf-8"))
        req = urllib.request.Request(
            f"{self.url}/api/v1/logs", data=body, method="POST",
            headers={"Content-Type": "application/json", "Content-Encoding": "gzip",
                     "Authorization": f"Bearer {self.token}", "User-Agent": "KrakenLauncher"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8") or "{}")

    def _run(self):
        backoff = FLUSH_EVERY
        while True:
            self._wake.wait(backoff)
            self._wake.clear()
            if not self._q:
                backoff = FLUSH_EVERY
                continue
            items, entries = self._take()
            try:
                res = self._post(entries)
                self.sent += int(res.get("written", 0))
                self.last_error = ""
                backoff = FLUSH_EVERY
            except urllib.error.HTTPError as e:
                self.last_error = f"HTTP {e.code}"
                if e.code in (400, 413):          # zła paczka – nie ponawiamy w kółko
                    backoff = FLUSH_EVERY
                else:
                    self._put_back(items)
                    backoff = min(backoff * 2, 60.0)
            except Exception as e:                 # brak sieci / serwera
                self.last_error = str(e)[:200]
                self._put_back(items)
                backoff = min(backoff * 2, 60.0)


SHIPPER = LogShipper()
