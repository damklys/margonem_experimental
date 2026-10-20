"""Wysyłka logów postaci na serwer Kraken API (kraken_api_server) – w tle, paczkami, z ponawianiem.

Konfiguracja: api.json obok launchera (plik lokalny, poza gitem):
    {"url": "https://api.twojadomena.pl", "token": "..."}
Bez pliku (albo bez url/token) wysyłka jest wyłączona.
"""
import gzip
import json
import os
import platform
import queue
import socket
import uuid
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
        self.url = str(cfg.get("url", "")).strip().rstrip("/")
        self.token = str(cfg.get("token", "")).strip()
        # Stały identyfikator i nazwa tego launchera (host w panelu) – nadawane przy pierwszym uruchomieniu.
        self.host_id = str(cfg.get("host_id", "")) or uuid.uuid4().hex[:16]
        self.host_name = str(cfg.get("host_name", "")) or socket.gethostname().split(".")[0][:40]
        if not cfg.get("host_id") and (self.url or self.token):
            _write_api_json({**cfg, "host_id": self.host_id, "host_name": self.host_name})
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


def _write_api_json(data: dict) -> None:
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, CONFIG_PATH)


def save_config(url: str, token: str, host_name: str = None) -> None:
    """Zapis adresu, tokenu i nazwy hosta (Ustawienia launchera) do api.json – tylko dla właściciela pliku."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data.update(url=url.strip().rstrip("/"), token=token.strip(), host_id=SHIPPER.host_id,
                host_name=(host_name or SHIPPER.host_name).strip()[:40])
    _write_api_json(data)
    SHIPPER.reload()


def check(url: str, token: str) -> str:
    """Test połączenia: GET /api/v1/me z tokenem → opis wyniku."""
    try:
        req = urllib.request.Request(f"{url.strip().rstrip('/')}/api/v1/me",
                                     headers={"Authorization": f"Bearer {token.strip()}", "User-Agent": "KrakenLauncher"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode("utf-8") or "{}")
            return f"✅ Połączono – konto: {d.get('user')}" if d.get("ok") else "❌ Serwer odrzucił token"
    except urllib.error.HTTPError as e:
        return "❌ Zły token" if e.code == 401 else f"❌ HTTP {e.code}"
    except Exception as e:
        return f"❌ Brak połączenia: {str(e)[:120]}"


SHIPPER = LogShipper()

LAUNCHER_VERSION = "4.1"
PLATFORM = {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(platform.system(), platform.system())


def _api(method: str, path: str, body=None, timeout=15):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{SHIPPER.url}{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {SHIPPER.token}",
                                          "User-Agent": "KrakenLauncher"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


class HostLink:
    """Launcher jako host w panelu: co 10 s sygnał „żyję” z listą sesji, w odpowiedzi polecenia z panelu (start/stop
    sesji). Okno launchera podaje migawkę sesji (snapshot) i odbiera polecenia z kolejki (w swoim wątku)."""

    def __init__(self):
        self.snapshot = []                 # lista sesji ustawiana przez okno (wątek Tk)
        self.options = {}                  # grupy, configi, serwery, przeglądarki, szablony, programy (formularze panelu)
        self.commands = queue.Queue()      # polecenia dla okna
        self._results = []
        self._lock = threading.Lock()
        self._thread = None
        self.last_error = ""
        self.online = False

    def start(self):
        if not self._thread:
            self._thread = threading.Thread(target=self._run, name="host-link", daemon=True)
            self._thread.start()

    def report(self, cmd_id: str, ok: bool, message: str = ""):
        with self._lock:
            self._results.append({"id": cmd_id, "ok": bool(ok), "message": message})

    def _run(self):
        while True:
            if SHIPPER.enabled:
                with self._lock:
                    results, self._results = self._results, []
                try:
                    res = _api("POST", "/api/v1/host/heartbeat", {
                        "host_id": SHIPPER.host_id, "name": SHIPPER.host_name, "platform": PLATFORM,
                        "version": LAUNCHER_VERSION, "sessions": list(self.snapshot),
                        "options": dict(self.options), "results": results})
                    self.online, self.last_error = True, ""
                    for c in res.get("commands") or []:
                        self.commands.put(c)
                except Exception as e:
                    self.online, self.last_error = False, str(e)[:200]
                    with self._lock:
                        self._results = results + self._results
            time.sleep(10)

    def push_state(self, state: dict, configs: dict):
        """Ustawienia launchera (grupy, sesje, configi kont) na serwer – w tle."""
        if not SHIPPER.enabled:
            return
        body = {"host_id": SHIPPER.host_id, "name": SHIPPER.host_name, "state": state, "configs": configs}
        def run():
            try:
                _api("POST", "/api/v1/host/state", body, timeout=30)
            except Exception as e:
                self.last_error = f"zapis ustawień: {str(e)[:150]}"
        threading.Thread(target=run, daemon=True).start()

    @staticmethod
    def saved_hosts() -> list:
        return _api("GET", "/api/v1/host/state?list=1").get("hosts") or []

    @staticmethod
    def fetch_state(host_id: str) -> dict:
        from urllib.parse import quote
        return _api("GET", f"/api/v1/host/state?host_id={quote(host_id)}", timeout=30)


HOST = HostLink()
