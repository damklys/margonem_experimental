#!/usr/bin/env python3
"""Kraken API – serwer logów i panel WWW (demon systemd, sama biblioteka standardowa, Python 3.8+).

Użytkownicy panelu mają token. Bot Kraken (przeglądarka) i launcher wysyłają z tym tokenem logi postaci i sygnał
„żyję” – serwer odkłada logi danego użytkownika w <data_dir>/users/<użytkownik>/logs/<świat>/<postać>.log,
a panel pokazuje, które sesje są online, i log sesji na żywo.

Pierwsze uruchomienie: użytkownik admin / hasło admin – panel wymusza zmianę hasła po zalogowaniu.

API bota / launchera (nagłówek Authorization: Bearer <token użytkownika>, CORS dla stron gry):
  GET  /api/v1/health      – bez tokenu
  GET  /api/v1/me          – czy token jest poprawny i ważny: {"ok", "user", "expires"}; 401 {"error"} – zły / wygasły
  POST /api/v1/logs        – {"source", "entries": [{"char", "world", "lines": [...]}]} (opcjonalnie gzip)
  POST /api/v1/heartbeat   – {"char", "world", "version", "running", "map", "lvl", "step", "source"}
API launchera (host):
  POST /api/v1/host/heartbeat – {"host_id", "name", "platform", "version", "sessions": [...], "results": [...]}
                                → {"ok", "commands": [{"id", "action", "session", "session_name"}]}
  POST /api/v1/host/state     – {"host_id", "name", "state": {...}, "configs": {"plik.json": {...}}} – ustawienia launchera
  GET  /api/v1/host/state?host_id=…   – zapisane ustawienia (odtworzenie); ?list=1 – hosty z zapisanymi ustawieniami
Dane bota (checkout repo na serwerze, data_repo.py; odpowiedzi gzip przy Accept-Encoding: gzip):
  GET  /api/v1/data/status                 – {"ref", "updated", "counts"}
  GET  /api/v1/data/list?kind=route[&prof=m] – klucze i krótkie opisy (bez całych plików)
  GET  /api/v1/data/get?kind=route&key=…   – {"ok", "ref", "data"}
  POST /api/v1/data/batch {"items": [{"kind", "key"}]} (do 100) – {"ok", "ref", "items": [{"kind", "key", "data"}]}
  GET  /api/v1/data/world                  – graf świata (world, heros, e2)
Blokady tras (wspólne dla botów konta, także z różnych komputerów):
  POST /api/v1/locks {"world", "char", "acquire"?: trasa, "release"?: trasa}
       → {"ok", "granted", "holder", "locks": {trasa: {"owner", "age"}}}; ważność 120 s bez odnowienia,
       jedna trasa na postać (przejęcie nowej zwalnia poprzednią)
  GET  /api/v1/data/pack?kind=map|npc|route|playbook|set|skill[&prof=m] – cały rodzaj jedną odpowiedzią
Panel: /  (hosty, sesje, token), /host?id=  (sesje hosta, start/stop), /session?world=&char=  (log na żywo),
       /password, /login, /logout
"""
import argparse
import gzip
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import signal
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_repo import KINDS, DataRepo  # noqa: E402

VERSION = "5.5.0"
log = logging.getLogger("kraken-api")

DEFAULTS = {
    "host": "127.0.0.1",          # za reverse proxy (Caddy z HTTPS)
    "port": 8787,
    "data_dir": "/var/lib/kraken-api",
    "tokens": [],                 # dodatkowe tokeny (stary format) – przypisane do użytkownika admin
    "max_body_bytes": 4 * 1024 * 1024,
    "max_line_chars": 4000,
    "max_file_bytes": 50 * 1024 * 1024,
    "keep_rotated": 5,
    "online_seconds": 45,         # sesja online, gdy sygnał „żyję” był w tym czasie
    "panel_session_hours": 24,
    "repo_url": "https://github.com/damklys/margonem_experimental.git",
    "repo_branch": "main",
    "repo_sync_seconds": 600,     # co ile sprawdzać nowe dane w repo (git fetch)
}

_NAME_RE = re.compile(r"[^\w\-.]+", re.UNICODE)


def safe_name(s, default):
    """Nazwa pliku/katalogu (bez ścieżek, znaków specjalnych i kropek na początku). Spacje → „_”, więc
    „Solony Borowik Ósmy” (bot) i „Solony_Borowik_Ósmy” (plik configu w launcherze) to ta sama postać."""
    s = _NAME_RE.sub("_", str(s or "").strip()).strip("._")[:64]
    return s or default


def display_name(key):
    """Nazwa postaci do panelu (z nazwy pliku): podkreślenia jak spacje w nicku."""
    return key.replace("_", " ")


# ───────────────────────── użytkownicy ─────────────────────────

def hash_password(pw, salt=None, rounds=200_000):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("ascii"), rounds)
    return f"pbkdf2${rounds}${salt}${dk.hex()}"


def check_password(pw, stored):
    try:
        _, rounds, salt, _h = stored.split("$")
        return hmac.compare_digest(hash_password(pw, salt, int(rounds)), stored)
    except Exception:
        return False


TOKEN_DAYS = 365   # ważność tokenu konta (dni); pole "token_days" użytkownika w users.json zmienia ją dla konta


class Users:
    def __init__(self, data_dir, legacy_tokens):
        self.path = os.path.join(data_dir, "users.json")
        self.lock = threading.Lock()
        self.data = {"users": {}}
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        if not self.data["users"]:
            self.data["users"]["admin"] = {"pw": hash_password("admin"), "must_change": True,
                                           "token": secrets.token_urlsafe(32), "created": int(time.time())}
            self.save()
            log.warning("utworzono użytkownika admin / admin – zmiana hasła wymagana po pierwszym logowaniu")
        # Tokeny bez terminu ważności (sprzed wersji 5.1) – ważne od dziś przez okres konta.
        changed = False
        for u in self.data["users"].values():
            if not u.get("token_expires"):
                u["token_created"] = u.get("token_created") or int(time.time())
                u["token_expires"] = int(time.time()) + self.days(u) * 86400
                changed = True
        if changed:
            self.save()
        self.legacy = [t for t in legacy_tokens if t]

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def get(self, name):
        return self.data["users"].get(name)

    @staticmethod
    def days(u):
        try:
            return max(1, int(u.get("token_days") or TOKEN_DAYS))
        except (TypeError, ValueError):
            return TOKEN_DAYS

    def lookup(self, token):
        """(użytkownik, wygasł?) albo (None, False) – nieznany token."""
        if not token:
            return None, False
        for name, u in self.data["users"].items():
            if hmac.compare_digest(token, u.get("token", "")):
                return name, bool(u.get("token_expires")) and time.time() > u["token_expires"]
        if any(hmac.compare_digest(token, t) for t in self.legacy):
            return "admin", False
        return None, False

    def by_token(self, token):
        """Użytkownik tokenu – tylko ważnego (wygasły = brak autoryzacji)."""
        name, expired = self.lookup(token)
        return None if expired else name

    def set_password(self, name, pw):
        with self.lock:
            u = self.data["users"][name]
            u["pw"] = hash_password(pw)
            u["must_change"] = False
            self.save()

    def new_token(self, name):
        """Rotacja: nowy token z nowym terminem ważności; stary przestaje działać od razu (boty i launchery na nim
        tracą autoryzację przy najbliższym sprawdzeniu)."""
        with self.lock:
            u = self.data["users"][name]
            u["token"] = secrets.token_urlsafe(32)
            u["token_created"] = int(time.time())
            u["token_expires"] = int(time.time()) + self.days(u) * 86400
            self.save()
            return self.data["users"][name]["token"]


# ───────────────────────── logi i sesje ─────────────────────────

class Store:
    """Logi użytkownika: <root>/<użytkownik>/logs/<świat>/<postać>.log; blokada na plik, rotacja po rozmiarze."""

    def __init__(self, cfg):
        self.root = os.path.join(cfg["data_dir"], "users")
        self.max_bytes = int(cfg["max_file_bytes"])
        self.keep = int(cfg["keep_rotated"])
        self.max_line = int(cfg["max_line_chars"])
        self._locks = {}
        self._guard = threading.Lock()
        os.makedirs(self.root, exist_ok=True)
        self._merge_legacy_names()

    def _merge_legacy_names(self):
        """Pliki z dawnymi nazwami (spacje) → nazwa kanoniczna; gdy oba istnieją – dopisanie i usunięcie starego."""
        for user in os.listdir(self.root):
            base = os.path.join(self.root, user, "logs")
            if not os.path.isdir(base):
                continue
            for world in os.listdir(base):
                wdir = os.path.join(base, world)
                if not os.path.isdir(wdir):
                    continue
                for fn in sorted(os.listdir(wdir)):
                    if not fn.endswith(".log"):
                        continue
                    canon = safe_name(fn[:-4], "unknown") + ".log"
                    if canon == fn:
                        continue
                    src, dst = os.path.join(wdir, fn), os.path.join(wdir, canon)
                    if os.path.exists(dst):
                        with open(src, "rb") as a, open(dst, "ab") as b:
                            b.write(a.read())
                        os.remove(src)
                    else:
                        os.replace(src, dst)
                    log.info("scalono log postaci: %s/%s → %s", world, fn, canon)

    def path(self, user, world, char):
        return os.path.join(self.root, safe_name(user, "unknown"), "logs", safe_name(world, "unknown"),
                            safe_name(char, "unknown") + ".log")

    def _lock(self, path):
        with self._guard:
            return self._locks.setdefault(path, threading.Lock())

    def _rotate(self, path):
        for i in range(self.keep - 1, 0, -1):
            if os.path.exists(f"{path}.{i}"):
                os.replace(f"{path}.{i}", f"{path}.{i + 1}")
        os.replace(path, f"{path}.1")

    def append(self, user, world, char, lines):
        path = self.path(user, world, char)
        clean = []
        for ln in lines:
            ln = str(ln).replace("\r", " ").replace("\n", " ")[: self.max_line]
            if ln.strip():
                clean.append(ln + "\n")
        if not clean:
            return 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
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

    def chars(self, user):
        base = os.path.join(self.root, safe_name(user, "unknown"), "logs")
        out = []
        if not os.path.isdir(base):
            return out
        for world in sorted(os.listdir(base)):
            wdir = os.path.join(base, world)
            for fn in sorted(os.listdir(wdir)) if os.path.isdir(wdir) else []:
                if fn.endswith(".log"):
                    st = os.stat(os.path.join(wdir, fn))
                    out.append({"world": world, "char": fn[:-4], "bytes": st.st_size, "mtime": int(st.st_mtime)})
        return out

    def read_from(self, user, world, char, offset, limit=256 * 1024):
        """Nowe dane od offsetu (podgląd na żywo); offset < 0 – ostatnie `limit` bajtów. Plik po rotacji – od zera."""
        path = self.path(user, world, char)
        if not os.path.exists(path):
            return 0, ""
        size = os.path.getsize(path)
        if offset < 0:
            offset = max(0, size - limit)
        elif offset > size:
            offset = 0
        with open(path, "rb") as f:
            f.seek(offset)
            raw = f.read(limit)
        if offset and raw and not raw.startswith(b"\n"):
            # pierwsza (ucięta) linia przy starcie od środka pliku – pomijamy do najbliższego końca linii
            if offset == max(0, size - limit):
                cut = raw.find(b"\n")
                raw = raw[cut + 1:] if cut >= 0 else raw
        return offset + len(raw) if raw else offset, raw.decode("utf-8", "replace")


class Presence:
    """Sygnał „żyję” sesji bota: (użytkownik, świat, postać) → ostatnie dane."""

    def __init__(self):
        self.lock = threading.Lock()
        self.data = {}

    def beat(self, user, info):
        key = (user, safe_name(info.get("world"), "unknown"), safe_name(info.get("char"), "unknown"))
        with self.lock:
            self.data[key] = dict(info, ts=time.time())

    def of(self, user):
        with self.lock:
            return {(w, c): v for (u, w, c), v in self.data.items() if u == user}


class Hosts:
    """Launchery (hosty) użytkowników: stan z sygnału „żyję” (w pamięci), zapisane ustawienia launchera (dysk)
    i kolejka poleceń z panelu (start/stop sesji) odbierana przez launcher w odpowiedzi na sygnał."""

    def __init__(self, cfg):
        self.root = os.path.join(cfg["data_dir"], "users")
        self.lock = threading.Lock()
        self.live = {}          # (user, host_id) → info z sygnału + ts
        self.cmds = {}          # (user, host_id) → [polecenia]
        self.seq = 0

    def _dir(self, user):
        d = os.path.join(self.root, safe_name(user, "unknown"), "hosts")
        os.makedirs(d, exist_ok=True)
        return d

    def _file(self, user, host_id):
        return os.path.join(self._dir(user), safe_name(host_id, "host") + ".json")

    def load(self, user, host_id):
        try:
            with open(self._file(user, host_id), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_state(self, user, host_id, name, state, configs):
        data = {"host_id": host_id, "name": name, "state": state, "configs": configs, "updated": int(time.time())}
        path = self._file(user, host_id)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.chmod(tmp, 0o600)          # configi zawierają loginy i hasła kont gry
        os.replace(tmp, path)
        return data["updated"]

    def saved(self, user):
        out = []
        for fn in sorted(os.listdir(self._dir(user))):
            if fn.endswith(".json"):
                d = self.load(user, fn[:-5]) or {}
                out.append({"host_id": d.get("host_id", fn[:-5]), "name": d.get("name", ""), "updated": d.get("updated"),
                            "sessions": len((d.get("state") or {}).get("sessions") or []), "configs": len(d.get("configs") or {})})
        return out

    def beat(self, user, info):
        """Sygnał „żyję” launchera; zwraca polecenia do wykonania (oznaczone jako wysłane)."""
        key = (user, info["host_id"])
        with self.lock:
            if not info.get("options") and key in self.live:
                info["options"] = self.live[key].get("options") or {}
            self.live[key] = dict(info, ts=time.time())
            cmds = self.cmds.setdefault(key, [])
            for r in info.get("results") or []:
                for c in cmds:
                    if c["id"] == r.get("id"):
                        c.update(status="done" if r.get("ok") else "error", result=str(r.get("message", ""))[:300], done=time.time())
            out = []
            for c in cmds:
                if c["status"] == "queued":
                    c["status"] = "sent"
                    c["sent"] = time.time()
                    out.append({k: c[k] for k in ("id", "action", "session", "session_name", "params")})
                elif c["status"] == "sent" and time.time() - c.get("sent", 0) > 120:
                    c.update(status="error", result="brak odpowiedzi launchera")
            del cmds[:-50]
            return out

    def command(self, user, host_id, action, session, session_name, params=None):
        with self.lock:
            self.seq += 1
            c = {"id": f"c{int(time.time())}{self.seq}", "action": action, "session": session,
                 "session_name": session_name, "params": params or {}, "status": "queued", "created": time.time(), "result": ""}
            self.cmds.setdefault((user, host_id), []).append(c)
            return c["id"]

    def of(self, user, online_s):
        """Hosty użytkownika: online (sygnał) + zapisane na dysku (offline)."""
        now = time.time()
        rows = {}
        for d in self.saved(user):
            rows[d["host_id"]] = {"host_id": d["host_id"], "name": d["name"], "online": False, "last": d["updated"],
                                  "sessions": [], "saved": d["updated"]}
        with self.lock:
            for (u, hid), v in self.live.items():
                if u != user:
                    continue
                r = rows.setdefault(hid, {"host_id": hid, "saved": None})
                r.update(name=v.get("name") or r.get("name") or hid, platform=v.get("platform", ""), version=v.get("version", ""),
                         sessions=v.get("sessions") or [], options=v.get("options") or {},
                         online=now - v["ts"] < online_s, last=int(v["ts"]))
                r["commands"] = [dict(c, params={k: v for k, v in (c.get("params") or {}).items() if k != "password"})
                                 for c in self.cmds.get((u, hid), [])][-15:]
        return sorted(rows.values(), key=lambda r: (not r.get("online"), (r.get("name") or "").lower()))


PROF_NAMES = {"w": "wojownik", "p": "paladyn", "b": "tancerz ostrzy", "h": "łowca", "t": "tropiciel", "m": "mag"}
UNMANAGED = "niezarządzany"


def build_overview(user, store, presence, hosts, online_s):
    """Hosty (launchery) i jedna lista sesji: sesje launcherów (online – z sygnału, offline – z zapisanych ustawień)
    z dołączonym botem (po hoście i id sesji z bota, potem po świecie i nazwie postaci) i logiem; reszta – host
    „niezarządzany”."""
    now = time.time()
    rows, by_uid, by_name, host_rows = [], {}, {}, []

    def blank(**kw):
        r = {"host": UNMANAGED, "host_id": "", "managed": False, "host_online": False, "uid": "", "group": "", "session": "",
             "world": "", "char": "", "log_char": "", "prof": "", "lvl": None, "program": "", "step": "", "map": "",
             "last": None, "launcher": "", "online": False, "running": None, "version": ""}
        r.update(kw)
        return r

    for h in hosts.of(user, online_s):
        sess = h.get("sessions") if h.get("online") else None
        if not sess:
            st = (hosts.load(user, h["host_id"]) or {}).get("state") or {}
            sess = [{"uid": x.get("uid", ""), "name": x.get("name", ""), "group": x.get("group", ""),
                     "world": str(x.get("server", "")).lower(), "char": os.path.splitext(str(x.get("config", "")))[0],
                     "program": x.get("program", ""), "status": "OFFLINE"} for x in st.get("sessions") or []]
        name = h.get("name") or h["host_id"]
        for x in sess:
            r = blank(host=name, host_id=h["host_id"], managed=True, host_online=bool(h.get("online")), uid=str(x.get("uid") or ""),
                      group=x.get("group", ""), session=x.get("name", ""), world=str(x.get("world", "")).lower(),
                      char=display_name(str(x.get("char", ""))), log_char=safe_name(x.get("char"), "unknown"),
                      # „(wybór w bocie)” ze starszych launcherów to brak profesji, nie profesja
                      prof="" if str(x.get("prof", "")).startswith("(") else x.get("prof", ""),
                      program=x.get("program", ""), launcher=x.get("status", "OFFLINE"))
            rows.append(r)
            if r["uid"]:
                by_uid[(h["host_id"], r["uid"])] = r
            by_name.setdefault((r["world"], r["log_char"]), r)
        host_rows.append({"host_id": h["host_id"], "name": name, "online": bool(h.get("online")), "platform": h.get("platform", ""),
                          "version": h.get("version", ""), "last": h.get("last")})

    seen = set()
    for (w, c), v in presence.of(user).items():
        r = by_uid.get((v.get("host_id"), v.get("session"))) or by_name.get((w, c))
        if r is None:
            r = blank(world=w, char=display_name(c), log_char=c)
            rows.append(r)
            by_name[(w, c)] = r
        seen.add((w, c))
        r["char"] = str(v.get("char") or r["char"])
        r["log_char"] = c
        r["world"] = r["world"] or w
        for k in ("lvl", "step", "map", "version"):
            if v.get(k) not in (None, ""):
                r[k] = v[k]
        if v.get("prof"):
            r["prof"] = PROF_NAMES.get(v["prof"], v["prof"])
        r["running"] = v.get("running")
        r["last"] = max(r["last"] or 0, int(v["ts"]))
        r["online"] = r["online"] or now - v["ts"] < online_s
    for c in store.chars(user):
        key = (c["world"], c["char"])
        if key in seen:
            continue
        r = by_name.get(key)
        if r is None:
            r = blank(world=c["world"], char=display_name(c["char"]), log_char=c["char"])
            rows.append(r)
            by_name[key] = r
        r["last"] = max(r["last"] or 0, c["mtime"])

    for r in rows:
        if r["online"] and r["running"]:
            r["state"], r["state_key"] = "▶ pracuje", "run"
        elif r["online"]:
            r["state"], r["state_key"] = "⏸ bot stoi", "idle"
        elif r["launcher"] in ("RUNNING", "STOPPING"):
            r["state"], r["state_key"] = "⏳ uruchamia", "start"
        elif r["launcher"] == "ERROR":
            r["state"], r["state_key"] = "✖ błąd", "err"
        else:
            r["state"], r["state_key"] = "○ offline", "off"
    # Poza launcherem liczy się tylko bot online – stare logi postaci, których już nikt nie uruchamia, nie są sesjami.
    rows = [r for r in rows if r["managed"] or r["online"]]
    order = {"run": 0, "idle": 1, "start": 2, "err": 3, "off": 4}
    rows.sort(key=lambda r: (order[r["state_key"]], not r["managed"], r["host"].lower(), str(r["group"]).lower(),
                             str(r["session"]).lower(), str(r["char"]).lower()))
    active = lambda r: r["state_key"] in ("run", "idle", "start")
    for hr in host_rows:
        mine = [r for r in rows if r["host_id"] == hr["host_id"]]
        hr.update(sessions=len(mine), active=sum(1 for r in mine if active(r)))
    um = [r for r in rows if not r["managed"]]
    totals = {"hosts_total": len(host_rows), "hosts_online": sum(1 for h in host_rows if h["online"]),
              "sessions_total": len(rows), "sessions_active": sum(1 for r in rows if active(r)),
              "bots_running": sum(1 for r in rows if r["state_key"] == "run"),
              "unmanaged_total": len(um), "unmanaged_active": sum(1 for r in um if active(r))}
    return {"hosts": host_rows, "sessions": rows, "totals": totals}


class History:
    """Aktywność konta co 5 min (hosty online, sesje aktywne, boty pracujące) – wykres na pulpicie; 7 dni na dysku."""
    KEEP = 7 * 86400

    def __init__(self, root):
        self.root = root
        self.lock = threading.Lock()
        self.data = {}

    def _path(self, user):
        return os.path.join(self.root, safe_name(user, "unknown"), "stats.json")

    def _load(self, user):
        if user not in self.data:
            try:
                with open(self._path(user), "r", encoding="utf-8") as f:
                    self.data[user] = [p for p in json.load(f) if isinstance(p, dict)]
            except Exception:
                self.data[user] = []
        return self.data[user]

    def add(self, user, point):
        with self.lock:
            pts = self._load(user)
            pts.append(point)
            cut = time.time() - self.KEEP
            self.data[user] = pts = [p for p in pts if p.get("t", 0) >= cut]
            os.makedirs(os.path.dirname(self._path(user)), exist_ok=True)
            tmp = self._path(user) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(pts, f)
            os.replace(tmp, self._path(user))

    def get(self, user, hours=24):
        cut = time.time() - hours * 3600
        with self.lock:
            return [p for p in self._load(user) if p.get("t", 0) >= cut]


def range_hours(q, default=24):
    """Zakres pulpitu: hours=1, 8, 24, 72, 168, 336, 720."""
    try:
        h = int(q.get("hours", default))
    except (TypeError, ValueError):
        h = default
    return h if h in (1, 8, 24, 72, 168, 336, 720) else default


class Issues:
    """Ostrzeżenia i błędy z logów botów i launcherów – osobno, do późniejszej analizy:
    <data_dir>/users/<użytkownik>/issues/RRRR-MM-DD.jsonl, wiersz JSON na wpis
    {"ts", "t", "level": warn|error, "source": bot|launcher, "world", "char", "prog", "step", "msg", "line"}; 30 dni."""
    KEEP_DAYS = 30
    # Program i krok mogą zawierać nawiasy („[1-300] Zero to hero”, „Exp: [44lvl] gnolle”) – granice to „][” i „]: ”.
    BOT = re.compile(r"^\[(?P<time>[\d:]+)\]\[(?P<char>[^\]]*)\]\[(?P<type>[^\]]*)\]\[(?P<prog>.*?)\]\[(?P<step>.*?)\]: (?P<msg>.*)$")
    WARN_ICONS = ("⚠️", "⚠")
    ERR_ICONS = ("❌", "⛔", "🔴", "💀", "✖")

    def __init__(self, root):
        self.root = root
        self.lock = threading.Lock()
        self.pruned = ""

    def classify(self, line):
        """(poziom, źródło, pola) albo None – zwykła linia."""
        ln = line.strip()
        src = "bot"
        if ln.startswith("[launcher]"):
            src, ln = "launcher", ln[len("[launcher]"):].strip()
            m = re.match(r"^\[[\d:]+\]\s*(.*)$", ln)
            msg = m.group(1) if m else ln
            lvl = "error" if msg.startswith(self.ERR_ICONS) else "warn" if msg.startswith(self.WARN_ICONS) else None
            return (lvl, src, {"prog": "", "step": "", "msg": msg}) if lvl else None
        m = self.BOT.match(ln)
        if not m:
            return None
        lvl = {"błąd": "error", "ostrzeżenie": "warn"}.get(m.group("type"))
        return (lvl, src, {"prog": m.group("prog"), "step": m.group("step"), "msg": m.group("msg")}) if lvl else None

    def append(self, user, world, char, lines):
        now = time.time()
        rows = []
        for ln in lines:
            c = self.classify(str(ln)[:4000])
            if not c:
                continue
            lvl, src, f = c
            rows.append(json.dumps(dict({"ts": int(now), "t": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)), "level": lvl,
                                         "source": src, "world": str(world)[:40], "char": str(char)[:60], "line": str(ln)[:4000]}, **f),
                                   ensure_ascii=False))
        if not rows:
            return 0
        d = os.path.join(self.root, safe_name(user, "unknown"), "issues")
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        with self.lock:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{day}.jsonl"), "a", encoding="utf-8") as fh:
                fh.write("\n".join(rows) + "\n")
            if self.pruned != day:
                self.pruned = day
                cut = time.strftime("%Y-%m-%d", time.localtime(now - self.KEEP_DAYS * 86400))
                for fn in os.listdir(d):
                    if fn.endswith(".jsonl") and fn[:10] < cut:
                        try:
                            os.remove(os.path.join(d, fn))
                        except OSError:
                            pass
        return len(rows)

    def read(self, user, hours=24):
        """Wpisy z ostatnich `hours` godzin, jako tekst JSONL (pliki dni, które obejmuje zakres)."""
        d = os.path.join(self.root, safe_name(user, "unknown"), "issues")
        if not os.path.isdir(d):
            return ""
        cut = time.time() - hours * 3600
        first = time.strftime("%Y-%m-%d", time.localtime(cut))
        out = []
        for fn in sorted(f for f in os.listdir(d) if f.endswith(".jsonl") and f[:10] >= first):
            with open(os.path.join(d, fn), "r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        if json.loads(line).get("ts", 0) >= cut:
                            out.append(line)
                    except ValueError:
                        pass
        return "".join(out)

    @staticmethod
    def pattern(msg):
        """Komunikat bez liczb (współrzędne, czasy, poziomy) – grupuje podobne wpisy."""
        m = re.sub(r"\d+(?:[.,]\d+)?", "N", str(msg or ""))
        return re.sub(r"\s+", " ", m).strip()[:140]

    def summary(self, user, hours=24, limit=300):
        rows = []
        for line in self.read(user, hours).splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
        rows.sort(key=lambda r: r.get("ts", 0))
        groups = {}
        for r in rows:
            g = groups.setdefault(self.pattern(r.get("msg")), {"pattern": self.pattern(r.get("msg")), "warn": 0, "error": 0, "chars": set(), "last": 0})
            g["error" if r.get("level") == "error" else "warn"] += 1
            g["chars"].add(r.get("char", ""))
            g["last"] = max(g["last"], r.get("ts", 0))
        top = sorted(groups.values(), key=lambda g: -(g["warn"] + g["error"]))[:15]
        for g in top:
            g["chars"] = sorted(c for c in g["chars"] if c)[:8]
        keys = ("ts", "level", "source", "world", "char", "prog", "step", "msg")
        return {"total": len(rows), "warn": sum(1 for r in rows if r.get("level") != "error"),
                "error": sum(1 for r in rows if r.get("level") == "error"), "groups": top,
                "items": [{k: r.get(k) for k in keys} for r in reversed(rows[-limit:])]}


class RouteLocks:
    """Blokady tras (expowiska, trasy ZR): (użytkownik, świat) → trasa → {owner, ts}; w pamięci, 120 s ważności."""
    TTL = 120

    def __init__(self):
        self.lock = threading.Lock()
        self.data = {}

    def call(self, user, world, char, acquire="", release=""):
        now = time.time()
        key = (user, safe_name(world, "unknown").lower())
        acquire, release, char = str(acquire or "")[:120], str(release or "")[:120], str(char or "")[:60]
        with self.lock:
            t = self.data.setdefault(key, {})
            for name in [n for n, v in t.items() if now - v["ts"] > self.TTL]:
                del t[name]
            if release and t.get(release, {}).get("owner") == char:
                del t[release]
            granted, holder = None, ""
            if acquire and char:
                cur = t.get(acquire)
                if not cur or cur["owner"] == char:
                    for name in [n for n, v in t.items() if v["owner"] == char and n != acquire]:
                        del t[name]
                    t[acquire] = {"owner": char, "ts": now}
                    granted, holder = True, char
                else:
                    granted, holder = False, cur["owner"]
            return {"granted": granted, "holder": holder,
                    "locks": {n: {"owner": v["owner"], "age": int(now - v["ts"])} for n, v in t.items()}}

    def of(self, user):
        now = time.time()
        with self.lock:
            return {w: {n: {"owner": v["owner"], "age": int(now - v["ts"])} for n, v in t.items() if now - v["ts"] <= self.TTL}
                    for (u, w), t in self.data.items() if u == user}


class OpStats:
    """Operacje botów (z sygnału „żyję”): przedział 5 min → typ → {start, ok, slow, fail}; 30 dni na dysku (ops.json).
    Zakresy pulpitu (1 h … 30 d) liczone wstecz od teraz, nie od pełnej godziny."""
    KEEP = 30 * 86400
    BUCKET = 300
    KEYS = ("start", "ok", "slow", "fail")

    def __init__(self, root):
        self.root = root
        self.lock = threading.Lock()
        self.data = {}
        self.dirty = set()

    def _path(self, user):
        return os.path.join(self.root, safe_name(user, "unknown"), "ops.json")

    def _load(self, user):
        if user not in self.data:
            try:
                with open(self._path(user), "r", encoding="utf-8") as f:
                    self.data[user] = {int(k): v for k, v in json.load(f).items()}
            except Exception:
                self.data[user] = {}
        return self.data[user]

    def add(self, user, ops):
        slot = int(time.time() // self.BUCKET * self.BUCKET)
        with self.lock:
            d = self._load(user)
            b = d.setdefault(slot, {})
            for t, c in list(ops.items())[:40]:
                if not isinstance(c, dict):
                    continue
                cur = b.setdefault(safe_name(t, "inne")[:24], dict.fromkeys(self.KEYS, 0))
                for k in self.KEYS:
                    try:
                        cur[k] += max(0, min(100000, int(c.get(k) or 0)))
                    except (TypeError, ValueError):
                        pass
            self.dirty.add(user)

    def flush(self):
        with self.lock:
            cut = time.time() - self.KEEP
            for user in list(self.dirty):
                d = {h: v for h, v in self.data.get(user, {}).items() if h >= cut}
                self.data[user] = d
                os.makedirs(os.path.dirname(self._path(user)), exist_ok=True)
                tmp = self._path(user) + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump({str(h): v for h, v in d.items()}, f)
                os.replace(tmp, self._path(user))
            self.dirty.clear()

    def last(self, user, hours=24):
        """Suma z ostatnich `hours` godzin (wstecz od teraz): typ → {start, ok, slow, fail}."""
        cut = time.time() - hours * 3600 - self.BUCKET
        out = {}
        with self.lock:
            for h, b in self._load(user).items():
                if h < cut:
                    continue
                for t, c in b.items():
                    o = out.setdefault(t, dict.fromkeys(self.KEYS, 0))
                    for k in self.KEYS:
                        o[k] += int(c.get(k) or 0)
        return out


def history_sampler(users, store, presence, hosts, history, online_s, every=300, opstats=None):
    time.sleep(60)
    while True:
        if opstats:
            try:
                opstats.flush()
            except Exception as e:
                log.warning("operacje: %s", e)
        for user in list(users.data.get("users", {})):
            try:
                t = build_overview(user, store, presence, hosts, online_s)["totals"]
                if t["sessions_total"] or t["hosts_total"]:
                    history.add(user, {"t": int(time.time()), "hosts": t["hosts_online"], "sessions": t["sessions_active"],
                                       "bots": t["bots_running"]})
            except Exception as e:
                log.warning("historia %s: %s", user, e)
        time.sleep(every)


# ───────────────────────── HTML panelu ─────────────────────────

CSS = """
:root{--bg:#0b0e1a;--bg2:#111526;--bg3:#1a2038;--fg:#d8c79a;--dim:#7d8aa8;--acc:#c8921e;--ok:#3fb26b;--off:#6b7280;--bad:#d55}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--acc)}header{display:flex;align-items:center;gap:12px;padding:10px 18px;background:var(--bg2);border-bottom:1px solid #222a44}
header b{font-size:16px}header .sp{flex:1}main{max-width:1100px;margin:0 auto;padding:18px}
.tag{display:inline-block;padding:1px 7px;border-radius:9px;background:var(--bg3);color:var(--dim);font-size:12px}
.ok{color:var(--ok)}button.sm{padding:3px 9px;font-size:12.5px}button:disabled{opacity:.4;cursor:default}
.spin{display:inline-block;width:11px;height:11px;border:2px solid var(--dim);border-top-color:var(--acc);border-radius:50%;animation:sp .8s linear infinite;vertical-align:-1px;margin-right:6px}
@keyframes sp{to{transform:rotate(360deg)}}.busy{color:var(--acc);font-size:12.5px;white-space:nowrap}tr.pending td{background:#151b30}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}.grid2 label{display:grid;gap:4px;color:var(--dim);font-size:12.5px}
select{background:var(--bg3);color:var(--fg);border:1px solid #2c3656;border-radius:5px;padding:6px 8px;font:inherit;width:100%}
.card{background:var(--bg2);border:1px solid #222a44;border-radius:8px;padding:14px 16px;margin-bottom:14px}
h2{margin:0 0 10px;font-size:15px;color:var(--acc)}input,button{font:inherit}
input[type=text],input[type=password]{background:var(--bg3);color:var(--fg);border:1px solid #2c3656;border-radius:5px;padding:7px 9px;width:100%}
button,.btn{background:var(--bg3);color:var(--fg);border:1px solid #2c3656;border-radius:5px;padding:6px 12px;cursor:pointer;text-decoration:none;display:inline-block}
button.pri{background:var(--acc);color:#111;border-color:var(--acc);font-weight:600}
table{width:100%;border-collapse:collapse}td,th{padding:6px 8px;border-bottom:1px solid #1d2440;text-align:left}th{color:var(--dim);font-weight:500}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:var(--off)}.dot.on{background:var(--ok)}
.tok{font-family:ui-monospace,Menlo,Consolas,monospace;background:var(--bg3);padding:6px 9px;border-radius:5px;word-break:break-all}
.err{color:var(--bad)}.hint{color:var(--dim);font-size:12.5px}
main.wide{max-width:1400px}.card{min-width:0}header{flex-wrap:wrap}
@media (max-width:600px){main{padding:12px}.tile .v{font-size:24px}.tiles{grid-template-columns:1fr 1fr}}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:14px}
.tile{background:var(--bg2);border:1px solid #222a44;border-radius:8px;padding:12px 14px}
.tile .l{color:var(--dim);font-size:12.5px}.tile .v{font-size:30px;font-weight:600;line-height:1.15;color:var(--fg)}.tile .s{color:var(--dim);font-size:12px}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}.charts .card{margin:0;min-width:0}
@media (max-width:820px){.charts{grid-template-columns:1fr}}
.chart svg{width:100%;height:auto;display:block}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--dim);margin:0 0 6px}.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
#tip{position:fixed;pointer-events:none;background:#070912;border:1px solid #2b3556;border-radius:6px;padding:6px 9px;font-size:12.5px;color:var(--fg);display:none;z-index:9;white-space:nowrap}
.tbl-wrap{overflow-x:auto}.flt{padding:4px}.flt input,.flt select{padding:3px 5px;font-size:12px;min-width:70px}
.st-run{color:var(--ok)}.st-idle,.st-start{color:var(--acc)}.st-err{color:var(--bad)}.st-off{color:var(--off)}
.login{max-width:360px;margin:12vh auto}.login form>*{margin-bottom:10px}
#log{font:12.5px/1.4 ui-monospace,Menlo,Consolas,monospace;background:#070912;border:1px solid #1d2440;border-radius:6px;padding:10px;height:70vh;overflow:auto;white-space:pre-wrap;word-break:break-word}
.l-blad{color:#e06c6c}.l-ostrzezenie{color:#e0b44c}.l-sukces{color:#5fc77f}.l-launcher{color:#7d8aa8}
"""


def page(title, body, user=None):
    nav = (f'<header><b>🐙 Kraken</b><span class="sp"></span><span class="hint">{html.escape(user)}</span>'
           f'<a class="btn" href="/">Panel</a><a class="btn" href="/password">Hasło</a><a class="btn" href="/logout">Wyloguj</a></header>'
           if user else "")
    return (f'<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)} – Kraken</title><style>{CSS}</style></head><body>{nav}{body}</body></html>')


DASH_JS = r"""
const esc=(s)=>String(s??'').replace(/[&<>"]/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt=(s)=>{if(s==null)return'—';const d=Math.round(Date.now()/1000-s);return d<60?d+' s temu':d<3600?Math.round(d/60)+' min temu':d<86400?Math.round(d/3600)+' godz. temu':new Date(s*1000).toLocaleString('pl-PL')};
const $=(i)=>document.getElementById(i);
const NS='http://www.w3.org/2000/svg';
// Serie (walidacja palety: ciemne tło #111526 – CVD i kontrast OK): sesje aktywne, boty pracujące.
const SER={sessions:['#3987e5','Sesje aktywne'],bots:['#d95926','Boty pracują']};
const BAR='#3987e5';
const tip=$('tip');
function showTip(e,html){tip.innerHTML=html;tip.style.display='block';const x=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8);tip.style.left=x+'px';tip.style.top=(e.clientY+14)+'px'}
const hideTip=()=>{tip.style.display='none'};
const el=(tag,attrs,parent)=>{const n=document.createElementNS(NS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);if(parent)parent.appendChild(n);return n};
const txt=(parent,x,y,s,attrs)=>{const t=el('text',Object.assign({x,y,fill:'#7d8aa8','font-size':11},attrs||{}),parent);t.textContent=s;return t};
// Oś liczb całkowitych: krok 1, 2, 5, 10… tak, żeby było najwyżej 5 podziałek.
const ticks=(m)=>{m=Math.max(1,m);let st=1;for(const k of [1,2,5,10,20,50,100,200,500,1000]){st=k;if(Math.ceil(m/k)<=5)break}return{max:Math.ceil(m/st)*st,step:st}};
const widthOf=(box,min)=>Math.max(min,Math.round(box.clientWidth||min));

// Aktywność z 24 h: dwie linie, celownik i dymek z wartościami, etykiety na końcach linii.
function lineChart(box,pts,now){box.textContent='';
if(!pts.length){box.innerHTML='<p class=hint>Zbieram dane – pierwszy punkt pojawi się w ciągu kilku minut (próbka co 5 min).</p>';return}
const W=widthOf(box,300),H=220,L=30,R=78,T=10,B=24,x0=now-86400;
const svg=el('svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Aktywność z ostatnich 24 godzin'},box);
const {max,step}=ticks(Math.max(...pts.map(p=>Math.max(p.sessions||0,p.bots||0))));
const X=(t)=>L+(t-x0)/86400*(W-L-R),Y=(v)=>T+(1-v/max)*(H-T-B);
for(let v=0;v<=max;v+=step){el('line',{x1:L,x2:W-R,y1:Y(v),y2:Y(v),stroke:'#1d2440','stroke-width':1},svg);txt(svg,L-6,Y(v)+4,Math.round(v),{'text-anchor':'end'})}
for(let h=0;h<=24;h+=6){const t=x0+h*3600;txt(svg,X(t),H-6,new Date(t*1000).toLocaleTimeString('pl-PL',{hour:'2-digit',minute:'2-digit'}),{'text-anchor':h===0?'start':h===24?'end':'middle'})}
for(const k of ['sessions','bots']){let d='',prev=null;
for(const p of pts){const gap=!prev||p.t-prev.t>900;d+=(gap?'M':'L')+X(p.t).toFixed(1)+' '+Y(p[k]||0).toFixed(1);prev=p}
el('path',{d,fill:'none',stroke:SER[k][0],'stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg)}
const last=pts[pts.length-1];
const ends=[['sessions',last.sessions||0],['bots',last.bots||0]].map(([k,v])=>({k,v,y:Y(v)}));
if(Math.abs(ends[0].y-ends[1].y)<13){const m=(ends[0].y+ends[1].y)/2;const up=ends[0].v>=ends[1].v?0:1;ends[up].y=m-7;ends[1-up].y=m+7}
for(const e of ends){el('circle',{cx:X(last.t),cy:Y(e.v),r:4,fill:SER[e.k][0],stroke:'#111526','stroke-width':2},svg);txt(svg,X(last.t)+8,e.y+4,`${e.v} ${e.k==='sessions'?'sesji':'botów'}`,{fill:'#d8c79a'})}
const cross=el('line',{y1:T,y2:H-B,stroke:'#7d8aa8','stroke-width':1,'stroke-dasharray':'3 3',visibility:'hidden'},svg);
const dots=['sessions','bots'].map(k=>el('circle',{r:4,fill:SER[k][0],stroke:'#111526','stroke-width':2,visibility:'hidden'},svg));
const hit=el('rect',{x:L,y:T,width:W-L-R,height:H-T-B,fill:'transparent'},svg);
hit.addEventListener('mousemove',(e)=>{const r=svg.getBoundingClientRect();const t=x0+((e.clientX-r.left)*W/r.width-L)/(W-L-R)*86400;
let best=pts[0];for(const p of pts)if(Math.abs(p.t-t)<Math.abs(best.t-t))best=p;
const x=X(best.t);cross.setAttribute('x1',x);cross.setAttribute('x2',x);cross.setAttribute('visibility','visible');
['sessions','bots'].forEach((k,i)=>{dots[i].setAttribute('cx',x);dots[i].setAttribute('cy',Y(best[k]||0));dots[i].setAttribute('visibility','visible')});
showTip(e,`<b>${new Date(best.t*1000).toLocaleString('pl-PL',{hour:'2-digit',minute:'2-digit',day:'2-digit',month:'2-digit'})}</b><br>`+['sessions','bots'].map(k=>`<span style="color:${SER[k][0]}">●</span> ${SER[k][1]}: <b>${best[k]||0}</b>`).join('<br>')+`<br><span class=hint>hosty online: ${best.hosts||0}</span>`)});
hit.addEventListener('mouseleave',()=>{hideTip();cross.setAttribute('visibility','hidden');dots.forEach(d=>d.setAttribute('visibility','hidden'))})}

// Poziome słupki (jedna seria): etykieta po lewej, wartość za końcem słupka, dymek po najechaniu.
function barChart(box,items,empty){box.textContent='';items=items.filter(i=>i.value>0);
if(!items.length){box.innerHTML=`<p class=hint>${esc(empty)}</p>`;return}
const W=widthOf(box,280),LW=Math.min(150,Math.round(W*0.32)),row=26,bh=12,H=items.length*row+6;
const svg=el('svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`,role:'img'},box);const max=Math.max(...items.map(i=>i.value));
items.forEach((it,i)=>{const y=i*row+4,w=Math.max(4,(W-LW-44)*it.value/max),r=4;
txt(svg,LW-8,y+bh-1,it.label.length>20?it.label.slice(0,19)+'…':it.label,{'text-anchor':'end',fill:'#d8c79a','font-size':12});
el('path',{d:`M${LW} ${y}h${w-r}a${r} ${r} 0 0 1 ${r} ${r}v${bh-2*r}a${r} ${r} 0 0 1 -${r} ${r}h-${w-r}z`,fill:BAR},svg);
txt(svg,LW+w+6,y+bh-1,String(it.value),{'font-size':12});
const hit=el('rect',{x:0,y:i*row,width:W,height:row,fill:'transparent'},svg);
hit.addEventListener('mousemove',(e)=>showTip(e,`<b>${esc(it.label)}</b><br>${esc(it.title||it.value)}`));hit.addEventListener('mouseleave',hideTip)})}

const LVL=[[1,19],[20,39],[40,59],[60,99],[100,149],[150,199],[200,999]];
const isOn=(s)=>s.state_key==='run'||s.state_key==='idle'||s.state_key==='start';
function charts(ov){const on=ov.sessions.filter(isOn);
lineChart($('c_act'),ov.history||[],ov.now);
const hs=(ov.hosts||[]).map(h=>({label:h.name,value:h.active,title:`sesje online: ${h.active} (w launcherze: ${h.sessions})`}));
const um=on.filter(s=>!s.managed);if(um.length)hs.push({label:'niezarządzany',value:um.length,title:`boty online poza launcherem: ${um.length}`});
barChart($('c_hosts'),hs,'Brak sesji online.');
const withLvl=on.filter(s=>+s.lvl>0);
barChart($('c_lvl'),LVL.map(([a,b])=>{const n=withLvl.filter(s=>s.lvl>=a&&s.lvl<=b);return{label:b>=999?`${a}+`:`${a}–${b}`,value:n.length,title:`postaci online: ${n.length}${n.length?' · '+n.slice(0,6).map(s=>s.char).join(', ')+(n.length>6?'…':''):''}`}}),'Brak sesji online z poziomem.');
const pc={};for(const s of on)if(s.prof)pc[s.prof]=(pc[s.prof]||0)+1;
barChart($('c_prof'),Object.entries(pc).sort((a,b)=>b[1]-a[1]).map(([k,v])=>({label:k,value:v,title:`postaci online: ${v}`})),'Brak sesji online z profesją.');
opsChart($('c_ops'),ov.ops)}

// Operacje botów z 24 h: słupek na typ, segmenty – udane, wolne (po ostrzeżeniu 120 s), nieudane (stała paleta statusów).
const OPN={travel:'Podróż',fight:'Walka',resupply:'Zaopatrzenie',prep:'Przygotowanie',sell:'Sprzedaż łupu',potions:'Mikstury',buy:'Zakup ekwipunku',equip:'Ekwipunek',skills:'Umiejętności',mail:'Poczta (Milioner)',auction:'Aukcje',quest:'Krok zadania',captcha:'Captcha',outfit:'Strój',rewards:'Nagrody'};
const OPS=[['ok','#0ca30c','✔ udane'],['slow','#fab219','⚠ wolne (po ostrzeżeniu)'],['fail','#d03b3b','✖ nieudane']];
// Słupki skumulowane (segmenty z odstępem 2 px, zaokrąglony koniec słupka): items [{label, c: {klucz: liczba}, tip}].
function stackBars(box,items,segs,empty,LWmax){box.textContent='';items=items.filter(i=>segs.some(([k])=>(i.c[k]||0)>0));
if(!items.length){box.innerHTML=`<p class=hint>${esc(empty)}</p>`;return}
items.forEach(i=>i.total=segs.reduce((a,[k])=>a+(i.c[k]||0),0));
const W=widthOf(box,300),LW=Math.min(LWmax||150,Math.round(W*0.4)),row=26,bh=12,H=items.length*row+6,max=Math.max(...items.map(i=>i.total)),scale=(W-LW-60)/max;
const svg=el('svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`,role:'img'},box);const maxCh=Math.max(8,Math.floor((LW-10)/6.6));
items.forEach((it,i)=>{const y=i*row+4;txt(svg,LW-8,y+bh-1,it.label.length>maxCh?it.label.slice(0,maxCh-1)+'…':it.label,{'text-anchor':'end',fill:'#d8c79a','font-size':12});
const parts=segs.map(([k,col])=>({k,col,v:it.c[k]||0})).filter(x=>x.v>0);let x=LW;
parts.forEach((sg,j)=>{const w=Math.max(2,sg.v*scale)-(j<parts.length-1?2:0),last=j===parts.length-1,r=last?Math.min(4,w/2):0;
el('path',{d:r?`M${x} ${y}h${w-r}a${r} ${r} 0 0 1 ${r} ${r}v${bh-2*r}a${r} ${r} 0 0 1 -${r} ${r}h-${w-r}z`:`M${x} ${y}h${w}v${bh}h-${w}z`,fill:sg.col},svg);x+=w+(last?0:2)});
txt(svg,x+6,y+bh-1,String(it.total),{'font-size':12});
const hit=el('rect',{x:0,y:i*row,width:W,height:row,fill:'transparent'},svg);
hit.addEventListener('mousemove',(e)=>showTip(e,`<b>${esc(it.label)}</b> – ${it.total}<br>`+segs.map(([k,col,l])=>`<span style="color:${col}">■</span> ${l}: <b>${it.c[k]||0}</b>`).join('<br>')+(it.tip?'<br>'+it.tip:'')));hit.addEventListener('mouseleave',hideTip)})}
function opsChart(box,ops){stackBars(box,Object.entries(ops||{}).map(([k,c])=>({label:OPN[k]||k,c})).sort((a,b)=>(b.c.ok+b.c.slow+b.c.fail)-(a.c.ok+a.c.slow+a.c.fail)),OPS,`Brak operacji w zakresie ${rangeLabel()} (bot 5.3+ wysyła je z sygnałem „żyję”).`)}
// Zakres pulpitu (operacje, ostrzeżenia i błędy) – zapamiętany w tej przeglądarce.
const RANGES=[[1,'1 h'],[8,'8 h'],[24,'24 h'],[72,'3 d'],[168,'7 d'],[336,'14 d'],[720,'30 d']];
let R=24;try{R=+localStorage.getItem('kraken:panel:range')||24}catch(e){}if(!RANGES.some(([h])=>h===R))R=24;
const rangeLabel=()=>(RANGES.find(([h])=>h===R)||[0,'24 h'])[1];
function rangeBar(){for(const bid of ['range','range2']){const b=$(bid);if(!b)continue;b.textContent='';for(const [h,l] of RANGES){const x=document.createElement('button');x.className='sm'+(h===R?' pri':'');x.textContent=l;
x.onclick=()=>{R=h;try{localStorage.setItem('kraken:panel:range',String(h))}catch(e){}rangeBar();chartSig='';load().catch(()=>{});issues().catch(()=>{})};b.appendChild(x)}}
for(const id of ['ops_range','iss_range'])$(id).textContent=rangeLabel();$('iss_dl').href=`/panel/api/issues?hours=${R}`}
// Ostrzeżenia i błędy: najczęstsze komunikaty (bez liczb) i lista ostatnich wpisów z filtrami.
const LV=[['warn','#fab219','⚠ ostrzeżenia'],['error','#d03b3b','✖ błędy']];let ISS=null;
async function issues(){const r=await fetch(`/panel/api/issues?format=json&hours=${R}`);if(!r.ok)return;ISS=await r.json();
$('iss_sum').innerHTML=`<span style="color:#fab219">⚠</span> ostrzeżeń: <b>${ISS.warn}</b> · <span style="color:#d03b3b">✖</span> błędów: <b>${ISS.error}</b>`;
stackBars($('c_iss'),(ISS.groups||[]).map(g=>({label:g.pattern,c:{warn:g.warn,error:g.error},tip:`postacie: ${esc(g.chars.join(', ')||'—')}<br>ostatnio: ${fmt(g.last)}`})),LV,`Brak ostrzeżeń i błędów w zakresie ${rangeLabel()}.`,420);
const chars=[...new Set((ISS.items||[]).map(i=>i.char).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pl'));const cs=$('if_char'),cur=cs.value;
cs.innerHTML='<option value="">wszystkie postacie</option>'+chars.map(c=>`<option${c===cur?' selected':''}>${esc(c)}</option>`).join('');issRows()}
function issRows(){if(!ISS)return;const lv=$('if_lvl').value,ch=$('if_char').value,q=$('if_q').value.trim().toLowerCase();
const list=(ISS.items||[]).filter(i=>(!lv||i.level===lv)&&(!ch||i.char===ch)&&(!q||`${i.msg} ${i.step} ${i.prog}`.toLowerCase().includes(q)));
const tb=$('irows');tb.textContent='';if(!list.length)tb.innerHTML=`<tr><td colspan=5 class=hint>Brak wpisów.</td></tr>`;
for(const i of list.slice(0,150)){const tr=document.createElement('tr');
tr.innerHTML=`<td style="white-space:nowrap">${new Date(i.ts*1000).toLocaleString('pl-PL',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'})}</td><td style="white-space:nowrap;color:${i.level==='error'?'#d03b3b':'#fab219'}">${i.level==='error'?'✖ błąd':'⚠ ostrzeżenie'}</td><td>${esc(i.char)}${i.source==='launcher'?' <span class=tag>launcher</span>':''}</td><td class=hint>${esc(i.step||'')}</td><td>${esc(i.msg)}</td>`;tb.appendChild(tr)}
$('icount').textContent=`pokazano ${Math.min(150,list.length)} z ${list.length}${ISS.items.length<ISS.total?` (ostatnie ${ISS.items.length} z ${ISS.total})`:''}`}
for(const id of ['if_lvl','if_char'])$(id).onchange=issRows;$('if_q').oninput=issRows;
function tiles(t){const T=[['Hosty online',t.hosts_online,'launchery z sygnałem'],['Sesje online',t.sessions_active,'działające teraz'],['Boty pracują',t.bots_running,'teraz'],['Niezarządzane online',t.unmanaged_active,'boty poza launcherem']];
$('tiles').innerHTML=T.map(([l,v,s])=>`<div class="tile"><div class="l">${l}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join('')}

function hostsTable(ov){const tb=$('hrows');tb.textContent='';
for(const h of ov.hosts){const tr=document.createElement('tr');
tr.innerHTML=`<td><span class="dot ${h.online?'on':''}"></span>${h.online?'online':'offline'}</td><td><a href="/host?id=${encodeURIComponent(h.host_id)}">${esc(h.name)}</a></td><td>${esc(h.platform||'')} ${h.version?'<span class=tag>'+esc(h.version)+'</span>':''}</td><td>${h.active} / ${h.sessions}</td><td>${fmt(h.last)}</td>`;tb.appendChild(tr)}
const t=ov.totals;const tr=document.createElement('tr');
tr.innerHTML=`<td><span class="dot ${t.unmanaged_active?'on':''}"></span>${t.unmanaged_active?'online':'—'}</td><td>niezarządzany</td><td class=hint>boty uruchomione poza launcherem</td><td>${t.unmanaged_active}</td><td>—</td>`;tb.appendChild(tr)}

// Lista sesji: kolumny i belka filtrów (lista wyboru dla kolumn o kilku wartościach, tekst dla reszty;
// poziom: „50”, „20-40”, „>100”, „<30”). Filtry zapamiętane w tej przeglądarce.
const COLS=[['state','Stan','sel'],['host','Host','sel'],['group','Grupa','sel'],['session','Sesja','txt'],['world','Świat','sel'],['char','Postać','txt'],['prof','Profesja','sel'],['lvl','Poziom','lvl'],['program','Program','txt'],['step','Krok','txt'],['last','Ostatnio','']];
let F={};try{F=JSON.parse(localStorage.getItem('kraken:panel:filters')||'{}')}catch(e){}
const saveF=()=>{try{localStorage.setItem('kraken:panel:filters',JSON.stringify(F))}catch(e){}};
function buildFilters(){const tr=$('frow');tr.textContent='';
for(const [k,,kind] of COLS){const td=document.createElement('td');td.className='flt';
if(kind==='sel'){const s=document.createElement('select');s.id='f_'+k;s.onchange=()=>{F[k]=s.value;saveF();rows()};td.appendChild(s)}
else if(kind){const i=document.createElement('input');i.type='text';i.id='f_'+k;i.placeholder=kind==='lvl'?'np. 20-40':'szukaj';i.value=F[k]||'';i.oninput=()=>{F[k]=i.value;saveF();rows()};td.appendChild(i)}
tr.appendChild(td)}}
const lvlOk=(v,f)=>{f=f.replace(/\s/g,'');if(!f)return true;const n=+v;if(!n)return false;let m;
if((m=/^(\d+)-(\d+)$/.exec(f)))return n>=+m[1]&&n<=+m[2];if((m=/^>=?(\d+)$/.exec(f)))return f[1]==='='?n>=+m[1]:n>+m[1];if((m=/^<=?(\d+)$/.exec(f)))return f[1]==='='?n<=+m[1]:n<+m[1];return String(n)===f};
const cell=(s,k)=>k==='lvl'?(s.lvl||''):String(s[k]??'');
let OV=null;
function rows(){if(!OV)return;const ss=OV.sessions;
for(const [k,,kind] of COLS){if(kind!=='sel')continue;const s=$('f_'+k);const vals=[...new Set(ss.map(x=>cell(x,k)).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pl'));
const cur=F[k]||'';s.innerHTML='<option value="">wszystkie</option>'+vals.map(v=>`<option${v===cur?' selected':''}>${esc(v)}</option>`).join('')+(cur&&!vals.includes(cur)?`<option selected>${esc(cur)}</option>`:'')}
const list=ss.filter(x=>COLS.every(([k,,kind])=>{const f=(F[k]||'').trim();if(!f||!kind)return true;if(kind==='sel')return cell(x,k)===f;if(kind==='lvl')return lvlOk(x.lvl,f);return cell(x,k).toLowerCase().includes(f.toLowerCase())}));
const tb=$('rows');tb.textContent='';
if(!list.length)tb.innerHTML=`<tr><td colspan=${COLS.length} class=hint>${ss.length?'Brak sesji pasujących do filtrów.':'Brak sesji – uruchom launcher albo wpisz token w bocie.'}</td></tr>`;
for(const s of list){const tr=document.createElement('tr');const u=`/session?world=${encodeURIComponent(s.world)}&char=${encodeURIComponent(s.log_char)}`;
tr.innerHTML=`<td class="st-${s.state_key}" style="white-space:nowrap">${esc(s.state)}</td><td>${s.managed?`<a href="/host?id=${encodeURIComponent(s.host_id)}">${esc(s.host)}</a>`:'<span class=hint>niezarządzany</span>'}</td><td>${esc(s.group)}</td><td>${esc(s.session)}</td><td>${esc(s.world)}</td><td>${s.log_char?`<a href="${u}">${esc(s.char)}</a>`:esc(s.char)}</td><td>${esc(s.prof)}</td><td>${s.lvl||''}</td><td>${esc(s.program)}</td><td>${esc(s.step)}</td><td style="white-space:nowrap">${fmt(s.last)}</td>`;tb.appendChild(tr)}
const act=Object.values(F).some(v=>String(v).trim());$('fcount').innerHTML=`pokazano ${list.length} z ${ss.length}`+(act?' · <a href="#" id="fclear">✕ wyczyść filtry</a>':'');
if(act)$('fclear').onclick=(e)=>{e.preventDefault();F={};saveF();buildFilters();rows()}}

let chartSig='';
async function load(){const r=await fetch(`/panel/api/overview?hours=${R}`);if(r.status===401){location='/login';return}OV=await r.json();
tiles(OV.totals);hostsTable(OV);rows();
const sig=JSON.stringify([OV.history,OV.ops,OV.hosts,OV.sessions.map(s=>[s.managed,s.lvl,s.prof,s.host_id,s.char,s.state_key])]);if(sig!==chartSig){chartSig=sig;charts(OV)}}
async function dstat(){const r=await fetch('/panel/api/data/status');if(!r.ok)return;const d=await r.json();
const N={map:'mapy',npc:'NPC',quest:'zadania',route:'trasy',set:'zestawy',playbook:'przebiegi',skill:'drzewka'};
$('dstat').textContent=d.ref?`Repo @${d.ref.slice(0,7)} · ${fmt(d.updated)} · `+Object.entries(d.counts).map(([k,v])=>`${N[k]||k} ${v}`).join(', ')+(d.world?'':' · brak grafu świata')+(d.error?' · błąd: '+d.error:''):(d.error?'Błąd: '+d.error:'Pierwsze pobieranie repo…')}
$('dsync').onclick=async()=>{await fetch('/panel/api/data/sync',{method:'POST'});$('dstat').textContent='Pobieram…';setTimeout(dstat,4000)};
buildFilters();rangeBar();issues().catch(()=>{});setInterval(()=>issues().catch(()=>{}),30000);
let rz=0;addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(()=>{OV&&charts(OV);issues().catch(()=>{})},200)});
const tick=()=>{load().catch(()=>{});dstat().catch(()=>{})};tick();setInterval(tick,5000);
"""

HOST_JS = """
const q=new URLSearchParams(location.search);const id=q.get('id');let H={},O={},editing=null,gediting=null;
const $=(i)=>document.getElementById(i);const esc=(s)=>String(s??'').replace(/[&<>"]/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PROFS=[['','🎲 losowa'],['w','wojownik'],['p','paladyn'],['b','tancerz ostrzy'],['h','łowca'],['t','tropiciel'],['m','mag']];
const ST={RUNNING:'▶ działa',STOPPING:'⏳ zatrzymuje',ERROR:'✖ błąd',OFFLINE:'○ wyłączona'};const BOT={running:'🤖 pracuje',stopped:'⏸ stoi',loading:'… wczytuje'};
async function cmd(action,s,name,params){const r=await fetch(`/panel/api/host/command?id=${encodeURIComponent(id)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,session:s||'',session_name:name||'',params:params||{}})});
let cid='';try{cid=(await r.json()).id||''}catch(e){}setTimeout(load,300);return cid}
// Akcje w toku na sesjach: uid → {action, cid, t}; koniec, gdy sesja/bot dojdzie do stanu docelowego, błąd albo 4 min.
const PEND={};const LIMIT=240000;
async function act(action,s){PEND[s.uid]={action,cid:'',t:Date.now(),err:''};sessions();PEND[s.uid].cid=await cmd(action,s.uid,s.name)}
function pendState(s){const p=PEND[s.uid];if(!p)return null;const c=(H.commands||[]).find(x=>x.id===p.cid);
if(c&&c.status==='error'){p.err=c.result||'błąd';p.done=Date.now()}
if(p.err){if(Date.now()-p.done>8000){delete PEND[s.uid];return null}return {err:p.err}}
const on=s.status==='RUNNING';let done=false,txt='';
if(p.action==='start'){done=on&&s.bot==='running';txt=!c||c.status==='queued'?'w kolejce…':!on?'uruchamiam przeglądarkę…':s.bot==='stopped'?'startuję bota…':'loguję i startuję bota…'}
else if(p.action==='stop'){done=s.status==='OFFLINE'||s.status==='ERROR';txt=!c||c.status==='queued'?'w kolejce…':'zatrzymuję sesję…'}
else if(p.action==='bot_start'){done=s.bot==='running';txt=!c||c.status==='queued'?'w kolejce…':'startuję bota…'}
else if(p.action==='refresh'){done=!!c&&(c.status==='done');txt=!c||c.status==='queued'?'w kolejce…':'odświeżam przeglądarkę…'}
else if(p.action==='bot_stop'){done=s.bot==='stopped'||!on;txt=!c||c.status==='queued'?'w kolejce…':'zatrzymuję bota…'}
if(c&&c.status==='done'&&(p.action==='start'||p.action==='stop')&&/już/.test(c.result||''))done=true;
if(done||Date.now()-p.t>LIMIT){delete PEND[s.uid];return null}
return {txt:txt+' '+Math.round((Date.now()-p.t)/1000)+' s'}}
const opt=(items,cur,first)=>(first!=null?`<option value="">${esc(first)}</option>`:'')+items.map(it=>{const v=typeof it==='string'?it:it.value,l=typeof it==='string'?it:it.label;return `<option value="${esc(v)}"${v===cur?' selected':''}>${esc(l)}</option>`}).join('');
const btn=(t,cls,fn,dis)=>{const b=document.createElement('button');b.className='sm '+(cls||'');b.textContent=t;b.disabled=!!dis;b.onclick=fn;return b};
const groupsOpt=()=>(O.groups||[]).map(g=>({value:g.name+'|'+g.world,label:`${g.name} (${g.world})`}));
function sessions(){const tb=$('rows');tb.textContent='';const ss=H.sessions||[];
if(!ss.length){tb.innerHTML=`<tr><td colspan=8 class=hint>${H.online?'Brak sesji.':'Host offline – sesje widać, gdy launcher jest uruchomiony.'}</td></tr>`;return}
for(const s of ss){const tr=document.createElement('tr');const on=s.status==='RUNNING'||s.status==='STOPPING';const ps=pendState(s);
tr.innerHTML=`<td>${ST[s.status]||esc(s.status)}</td><td>${on?(BOT[s.bot]||'…'):'—'}</td><td>${esc(s.name)}</td><td>${esc(s.group)}</td><td>${esc(s.config)}${s.banned?' <span class=err>(zablokowane)</span>':''}</td><td>${esc(s.prof||'—')}</td><td>${esc(s.program||'(z bota)')}${s.prog_override?' <span class=tag>własny</span>':''}</td><td></td>`;
const a=tr.lastChild;a.style.whiteSpace='nowrap';
if(ps&&!ps.err){tr.className='pending';const sp=document.createElement('span');sp.className='busy';sp.innerHTML='<span class="spin"></span>'+esc(ps.txt);a.appendChild(sp);tb.appendChild(tr);continue}
if(ps&&ps.err){const e=document.createElement('div');e.className='err';e.style.fontSize='12px';e.textContent='✖ '+ps.err;a.appendChild(e)}
a.appendChild(btn(on?'⏹ Sesja':'▶ Sesja',on?'':'pri',()=>act(on?'stop':'start',s),!H.online||(!on&&s.banned)));
a.appendChild(btn(s.bot==='running'?'⏸ Bot':'▶ Bot','',()=>act(s.bot==='running'?'bot_stop':'bot_start',s),!H.online||!on||s.bot==='loading'));
a.appendChild(btn('🔄','',()=>act('refresh',s),!H.online||s.status!=='RUNNING'));
a.appendChild(btn('✎','',()=>{editing=editing===s.uid?null:s.uid;edit()},!H.online));
a.appendChild(btn('🗑','',()=>{if(confirm(`Usunąć sesję „${s.name}”?`))cmd('delete_session',s.uid,s.name)},!H.online||on));tb.appendChild(tr)}}
function edit(){const box=$('edit');const s=(H.sessions||[]).find(x=>x.uid===editing);if(!s){box.style.display='none';return}
if(box.dataset.uid===editing&&box.style.display!=='none')return;box.dataset.uid=editing;box.style.display='';const on=s.status==='RUNNING'||s.status==='STOPPING';
box.innerHTML=`<h2>Edycja sesji „${esc(s.name)}”</h2><div class="grid2">
<label>Nazwa<input type="text" id="es_name" value="${esc(s.name)}"></label>
<label>Grupa<select id="es_group"${on?' disabled':''}>${opt(groupsOpt(),s.group+'|'+(s.group_world||''))}</select></label>
<label>Config<select id="es_config"${on?' disabled':''}>${opt(O.configs||[],s.config)}</select></label>
<label>Serwer<select id="es_server">${opt(O.servers||[],s.server)}</select></label>
<label>Przeglądarka<select id="es_browser"${on?' disabled':''}>${opt(O.browsers||[],s.browser)}</select></label>
<label>Szablon<select id="es_template"${on?' disabled':''}></select></label>
<label>Program<select id="es_program">${opt(O.programs||[],s.prog_override?s.own_program:'','(program grupy)')}</select></label>
<label><span><input type="checkbox" id="es_recreate"${s.recreate?' checked':''}> Recreate (nowy profil przy starcie)</span></label>
<label><span><input type="checkbox" id="es_rof"${s.restart_on_fail?' checked':''}> Restart on fail</span></label></div>
<div style="margin-top:10px"><button class="pri" id="es_save">Zapisz</button> <button id="es_cancel">Anuluj</button>${on?' <span class=hint>Sesja działa – config, grupę, przeglądarkę i szablon zmienisz po zatrzymaniu.</span>':''}</div>`;
const tpl=()=>{$('es_template').innerHTML=opt((O.templates||{})[$('es_browser').value]||[],s.template,'(brak)')};tpl();$('es_browser').onchange=tpl;
$('es_cancel').onclick=()=>{editing=null;box.style.display='none'};
$('es_save').onclick=()=>{const [group,gw]=$('es_group').value.split('|');const prog=$('es_program').value;const p={name:$('es_name').value,server:$('es_server').value,
recreate:$('es_recreate').checked,restart_on_fail:$('es_rof').checked,prog_override:!!prog,program:prog};
if(!on)Object.assign(p,{group,group_world:gw,config:$('es_config').value,browser:$('es_browser').value,template:$('es_template').value||'(brak)'});
cmd('update_session',s.uid,s.name,p);editing=null;box.style.display='none'}}
function groups(){const tb=$('grows');tb.textContent='';for(const g of O.groups||[]){const tr=document.createElement('tr');
const lay=g.layout_enabled===true||g.layout_enabled==='True'?`${g.layout_cols}×${g.layout_rows}, ekran ${(+g.layout_screen||0)+1}, zoom ${g.layout_zoom}`:'wyłączony';
const ram=g.ram_saver===true||g.ram_saver==='True';
tr.innerHTML=`<td>${esc(g.name)}${ram?' <span class=tag title="Oszczędzaj RAM">💾 RAM</span>':''}</td><td>${esc(g.world)}</td><td>${esc(g.program||'(bez zmiany)')}</td><td>${esc(lay)}</td><td></td>`;const a=tr.lastChild;
a.appendChild(btn('✎','',()=>{gediting=gediting===g.name+'|'+g.world?null:g.name+'|'+g.world;gedit()},!H.online));
a.appendChild(btn('🗑','',()=>{if(confirm(`Usunąć grupę „${g.name}”? Sesje trafią do innej grupy.`))cmd('delete_group','',g.name,{name:g.name,world:g.world})},!H.online));tb.appendChild(tr)}
if(!(O.groups||[]).length)tb.innerHTML='<tr><td colspan=5 class=hint>Brak grup.</td></tr>';$('ng_world').innerHTML=opt(O.worlds||['Gordion'],$('ng_world').value)}
function gedit(){const box=$('gedit');const g=(O.groups||[]).find(x=>x.name+'|'+x.world===gediting);if(!g){box.style.display='none';return}
if(box.dataset.g===gediting&&box.style.display!=='none')return;box.dataset.g=gediting;box.style.display='';const en=g.layout_enabled===true||g.layout_enabled==='True';
box.innerHTML=`<h2>Grupa „${esc(g.name)}”</h2><div class="grid2"><label>Nazwa<input type="text" id="eg_name" value="${esc(g.name)}"></label>
<label>Program grupy<select id="eg_program">${opt(O.programs||[],g.program||'','(bez zmiany – program z bota)')}</select></label>
<label><span><input type="checkbox" id="eg_en"${en?' checked':''}> Układaj okna przeglądarek</span></label>
<label><span><input type="checkbox" id="eg_ram"${g.ram_saver===true||g.ram_saver==='True'?' checked':''}> 💾 Oszczędzaj RAM (od następnego startu sesji)</span></label>
<label>Ekran<select id="eg_screen">${(O.screens||[]).map((x,i)=>`<option value="${i}"${i===(+g.layout_screen||0)?' selected':''}>${esc(x.name)}</option>`).join('')}</select></label>
<label>Kolumny<input type="text" id="eg_cols" value="${esc(g.layout_cols)}"></label><label>Wiersze<input type="text" id="eg_rows" value="${esc(g.layout_rows)}"></label>
<label>Skalowanie<select id="eg_zoom">${opt((O.zooms||[]).map(z=>({value:z,label:z==='auto'?'Auto':z+'%'})),String(g.layout_zoom))}</select></label></div>
<div style="margin-top:10px"><button class="pri" id="eg_save">Zapisz</button> <button id="eg_cancel">Anuluj</button></div>`;
$('eg_cancel').onclick=()=>{gediting=null;box.style.display='none'};
$('eg_save').onclick=async()=>{const nn=$('eg_name').value.trim();await cmd('update_group','',g.name,{name:g.name,world:g.world,program:$('eg_program').value,ram_saver:$('eg_ram').checked,layout_enabled:$('eg_en').checked,layout_screen:$('eg_screen').value,layout_cols:$('eg_cols').value,layout_rows:$('eg_rows').value,layout_zoom:$('eg_zoom').value});
if(nn&&nn!==g.name)await cmd('rename_group','',g.name,{name:g.name,new:nn,world:g.world});gediting=null;box.style.display='none'}}
function configs(){const tb=$('crows');tb.textContent='';for(const c of O.config_profs||[]){const tr=document.createElement('tr');tr.innerHTML=`<td>${esc(c.name)}${c.banned===true||c.banned==='True'?' <span class=err>(zablokowane)</span>':''}</td><td></td>`;
const sel=document.createElement('select');sel.innerHTML=opt(PROFS.map(([v,l])=>({value:v,label:l})),c.prof||'');sel.disabled=!H.online;
sel.onchange=()=>cmd('set_config_prof','',c.name,{config:c.name,prof:sel.value});tr.lastChild.appendChild(sel);tb.appendChild(tr)}
if(!(O.config_profs||[]).length)tb.innerHTML='<tr><td colspan=2 class=hint>Brak configów.</td></tr>'}
let optSig='';function forms(){const sig=JSON.stringify(O);if(sig===optSig)return;optSig=sig;
$('ns_group').innerHTML=opt(groupsOpt(),$('ns_group').value);$('ns_config').innerHTML=opt(O.configs||[],$('ns_config').value);
$('ns_server').innerHTML=opt(O.servers||[],$('ns_server').value);$('ns_browser').innerHTML=opt(O.browsers||[],$('ns_browser').value);
const tpl=()=>{$('ns_template').innerHTML=opt((O.templates||{})[$('ns_browser').value]||[],$('ns_template').value,'(brak)')};tpl();$('ns_browser').onchange=tpl;
$('ns_program').innerHTML=opt(O.programs||[],$('ns_program').value,'(program grupy)');$('nc_prof').innerHTML=opt(PROFS.map(([v,l])=>({value:v,label:l})),$('nc_prof').value);
groups();configs()}
$('ns_go').onclick=()=>{const v=(i)=>$(i).value;if(!v('ns_group')){$('ns_info').textContent='Brak grup – utwórz grupę.';return}const [group,world]=v('ns_group').split('|');
cmd('create_session','',v('ns_name')||'nowa sesja',{name:v('ns_name'),group,world,config:v('ns_config'),server:v('ns_server'),browser:v('ns_browser'),template:v('ns_template'),program:v('ns_program')});$('ns_info').textContent='Wysłano.'};
const man=()=>{const m=$('nc_mode').value==='manual';document.querySelectorAll('.nc-man').forEach(e=>e.style.display=m?'':'none')};$('nc_mode').onchange=man;man();
$('nc_go').onclick=()=>{const v=(i)=>$(i).value;const m=v('nc_mode');if(m==='manual'&&(!v('nc_login')||!v('nc_pw'))){$('nc_info').textContent='Podaj login i hasło.';return}
cmd('create_config','',m==='auto'?'nowe konto':v('nc_name')||v('nc_login'),m==='auto'?{mode:'auto',prof:v('nc_prof')}:{mode:'manual',name:v('nc_name'),login:v('nc_login'),password:v('nc_pw'),prof:v('nc_prof')});$('nc_pw').value='';$('nc_info').textContent='Wysłano.'};
$('ng_go').onclick=()=>{const n=$('ng_name').value.trim();if(!n)return;cmd('create_group','',n,{name:n,world:$('ng_world').value});$('ng_name').value=''};
const ACT={start:'▶ sesja',stop:'⏹ sesja',bot_start:'▶ bot',bot_stop:'⏸ bot',create_session:'＋ sesja',update_session:'✎ sesja',delete_session:'🗑 sesja',create_config:'＋ config',set_config_prof:'🎓 profesja',create_group:'＋ grupa',rename_group:'✎ nazwa grupy',delete_group:'🗑 grupa',update_group:'✎ grupa',delete_banned:'🗑 zablokowane sesje',refresh:'🔄 odświeżenie'};
async function load(){const r=await fetch(`/panel/api/host?id=${encodeURIComponent(id)}`);if(r.status===401){location='/login';return}H=await r.json();O=H.options||{};
$('hn').textContent=H.name||id;$('hs').innerHTML=`<span class="dot ${H.online?'on':''}"></span>${H.online?'online':'offline'} · ${esc(H.platform||'')} ${esc(H.version||'')}${H.saved?' · ustawienia zapisane '+new Date(H.saved*1000).toLocaleString('pl-PL'):''}`;
const none=!O.groups&&H.online;$('ns_info').textContent=none?'Launcher nie przesłał list – zaktualizuj launcher (git pull) i uruchom ponownie.':'';
for(const b of ['ns_go','nc_go','ng_go'])$(b).disabled=!H.online;
sessions();forms();edit();gedit();
const nb=(H.sessions||[]).filter(s=>s.banned&&s.status!=='RUNNING'&&s.status!=='STOPPING').length;const db=$('del_banned');db.style.display=nb?'':'none';db.textContent=`🗑 Usuń zablokowane sesje (${nb})`;db.disabled=!H.online;
db.onclick=()=>{if(confirm(`Usunąć ${nb} sesji z zablokowanym kontem? Configi zostaną (z oznaczeniem).`))cmd('delete_banned','','zablokowane')};
const cb=$('cmds');cb.textContent='';for(const c of (H.commands||[]).slice().reverse()){const d=document.createElement('div');d.className='hint';
d.textContent=`${new Date(c.created*1000).toLocaleTimeString('pl-PL')} · ${ACT[c.action]||c.action} „${c.session_name||c.session}” – ${({queued:'w kolejce',sent:'wysłane',done:'wykonane',error:'błąd'})[c.status]||c.status}${c.result?': '+c.result:''}`;cb.appendChild(d)}}
async function loop(){await load().catch(()=>{});setTimeout(loop,Object.keys(PEND).length?1500:3000)}
loop();setInterval(()=>{if(Object.keys(PEND).length)sessions()},1000);
"""

LIVE_JS = """
const q=new URLSearchParams(location.search);let off=-1;const box=document.getElementById('log');let follow=true;
box.addEventListener('scroll',()=>{follow=box.scrollTop+box.clientHeight>=box.scrollHeight-30});
const cls=(l)=>l.includes('[launcher]')?'l-launcher':l.includes('][błąd]')?'l-blad':l.includes('][ostrzeżenie]')?'l-ostrzezenie':l.includes('][sukces]')?'l-sukces':'';
async function pull(){try{const r=await fetch(`/panel/api/tail?world=${encodeURIComponent(q.get('world'))}&char=${encodeURIComponent(q.get('char'))}&offset=${off}`);
if(r.status===401){location='/login';return}const d=await r.json();
document.getElementById('st').innerHTML=`<span class="dot ${d.online?'on':''}"></span>${d.online?'online':'offline'}${d.info?' · '+d.info:''}`;
if(d.data){const frag=document.createDocumentFragment();for(const line of d.data.split('\\n')){if(!line)continue;const el=document.createElement('div');el.className=cls(line);el.textContent=line;frag.appendChild(el)}
box.appendChild(frag);while(box.childNodes.length>5000)box.removeChild(box.firstChild);if(follow)box.scrollTop=box.scrollHeight}
off=d.offset}catch(e){}setTimeout(pull,1500)}
pull();
"""


# ───────────────────────── serwer ─────────────────────────

def make_handler(cfg, users, store, presence, hosts, repo, history, opstats, issues, locks):
    sessions = {}                       # sid → {"user", "exp"}
    fails = {}                          # ip → (liczba, od kiedy)
    slock = threading.Lock()
    online_s = int(cfg["online_seconds"])

    class Handler(BaseHTTPRequestHandler):
        server_version = f"KrakenAPI/{VERSION}"
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            log.debug("%s %s", self.client_ip(), fmt % args)

        def client_ip(self):
            return (self.headers.get("X-Forwarded-For", "").split(",")[0].strip() or self.client_address[0])

        # ── odpowiedzi ──
        def _send(self, code, body, ctype="application/json; charset=utf-8", headers=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False)
            raw = body.encode("utf-8") if isinstance(body, str) else body
            gz = len(raw) > 2048 and "gzip" in self.headers.get("Accept-Encoding", "") and self.path.startswith("/api/v1/data")
            if gz:
                raw = gzip.compress(raw, 6)
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            if gz:
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Vary", "Accept-Encoding")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            if self.path.startswith("/api/"):
                self._cors()
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(raw)

        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Content-Encoding")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Max-Age", "86400")

        def _html(self, code, title, body, user=None, headers=None):
            self._send(code, page(title, body, user), "text/html; charset=utf-8", headers)

        def _redirect(self, to, headers=None):
            h = {"Location": to}
            h.update(headers or {})
            self._send(303, "", "text/plain", h)

        def _body(self):
            self._body_done = True
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length > cfg["max_body_bytes"]:
                self.close_connection = True      # nieprzeczytana treść – połączenie do zamknięcia
                return None
            if length <= 0:
                return None
            raw = self.rfile.read(length)
            if self.headers.get("Content-Encoding", "").lower() == "gzip":
                raw = gzip.decompress(raw)[: cfg["max_body_bytes"] * 8]
            return raw

        def _form(self):
            raw = self._body() or b""
            return {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace")).items()}

        # ── autoryzacja ──
        def token_user(self):
            auth = self.headers.get("Authorization", "")
            return users.by_token(auth[7:].strip() if auth.lower().startswith("bearer ") else "")

        def panel_user(self):
            m = re.search(r"(?:^|;\s*)kraken_sid=([A-Za-z0-9_\-]+)", self.headers.get("Cookie", ""))
            if not m:
                return None
            with slock:
                s = sessions.get(m.group(1))
                if not s or s["exp"] < time.time():
                    sessions.pop(m.group(1), None)
                    return None
                return s["user"]

        def _require_panel(self):
            user = self.panel_user()
            if not user:
                self._redirect("/login")
                return None
            if users.get(user).get("must_change") and urlparse(self.path).path not in ("/password", "/logout"):
                self._redirect("/password")
                return None
            return user

        # ── metody ──
        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            p = url.path
            if p == "/api/v1/health":
                return self._send(200, {"ok": True, "version": VERSION})
            if p == "/api/v1/me":
                auth = self.headers.get("Authorization", "")
                name, expired = users.lookup(auth[7:].strip() if auth.lower().startswith("bearer ") else "")
                if not name or expired:
                    return self._send(401, {"ok": False, "error": "token wygasł" if expired else "nieznany token (zrolowany?)"})
                return self._send(200, {"ok": True, "user": name, "expires": users.get(name).get("token_expires")})
            if p.startswith("/api/v1/data/"):
                return self._data_get(p, q)
            if p == "/panel/api/overview":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                ov = build_overview(user, store, presence, hosts, online_s)
                ov["locks"] = locks.of(user)
                return self._send(200, dict(ov, ok=True, history=history.get(user, 24), ops=opstats.last(user, range_hours(q)),
                                            hours=range_hours(q), now=int(time.time())))
            if p == "/panel/api/issues":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                try:
                    hours = range_hours(q) if "hours" in q else 24 * max(1, min(30, int(q.get("days", "1") or 1)))
                except ValueError:
                    hours = 24
                if q.get("format") == "json":
                    return self._send(200, dict(issues.summary(user, hours), ok=True, hours=hours))
                name = f"kraken-ostrzezenia-bledy-{time.strftime('%Y-%m-%d')}-{hours}h.jsonl"
                return self._send(200, issues.read(user, hours), "application/x-ndjson; charset=utf-8",
                                  {"Content-Disposition": f'attachment; filename="{name}"'})
            if p == "/panel/api/data/status":
                if not self.panel_user():
                    return self._send(401, {"ok": False})
                return self._send(200, dict({"ok": True}, **repo.status()))
            if p == "/api/v1/host/state":
                user = self.token_user()
                if not user:
                    return self._send(401, {"ok": False, "error": "unauthorized"})
                if q.get("list"):
                    return self._send(200, {"ok": True, "hosts": hosts.saved(user)})
                d = hosts.load(user, q.get("host_id", ""))
                return self._send(200 if d else 404, {"ok": bool(d), **(d or {})})
            if p == "/login":
                return self._login_page()
            if p == "/logout":
                m = re.search(r"kraken_sid=([A-Za-z0-9_\-]+)", self.headers.get("Cookie", ""))
                if m:
                    with slock:
                        sessions.pop(m.group(1), None)
                return self._redirect("/login", {"Set-Cookie": "kraken_sid=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"})
            if p == "/password":
                user = self._require_panel()
                return user and self._password_page(user)
            if p == "/":
                user = self._require_panel()
                return user and self._dashboard(user)
            if p == "/session":
                user = self._require_panel()
                return user and self._session_page(user, q.get("world", ""), q.get("char", ""))
            if p == "/host":
                user = self._require_panel()
                return user and self._host_page(user)
            if p == "/panel/api/hosts":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                return self._send(200, [{k: v for k, v in h.items() if k != "commands"} for h in hosts.of(user, online_s)])
            if p == "/panel/api/host":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                h = next((x for x in hosts.of(user, online_s) if x["host_id"] == q.get("id")), None)
                return self._send(200 if h else 404, h or {"ok": False})
            if p == "/panel/api/sessions":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                return self._send(200, self._sessions(user))
            if p == "/panel/api/tail":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                try:
                    off = int(q.get("offset", "-1"))
                except ValueError:
                    off = -1
                world, char = q.get("world", ""), q.get("char", "")
                new_off, data = store.read_from(user, world, char, off)
                pr = presence.of(user).get((safe_name(world, "unknown"), safe_name(char, "unknown")))
                online = bool(pr and time.time() - pr["ts"] < online_s)
                info = " · ".join(x for x in [pr and pr.get("version") and f"Kraken {pr['version']}",
                                              pr and pr.get("step")] if x) if pr else ""
                return self._send(200, {"offset": new_off, "data": data, "online": online, "info": info})
            self._send(404, {"ok": False, "error": "not found"})

        def do_POST(self):
            # Odpowiedź bez odczytania treści (np. 401 przy złym tokenie) zostawiłaby ją w połączeniu keep-alive –
            # następne żądanie na tym połączeniu byłoby z niej odczytane (501). Treść dobieramy po obsłudze.
            self._body_done = False
            try:
                self._do_post()
            finally:
                if not self._body_done:
                    try:
                        self._body()
                    except Exception:
                        self.close_connection = True

        def _do_post(self):
            p = urlparse(self.path).path
            if p == "/api/v1/data/batch":
                return self._data_batch()
            if p == "/panel/api/data/sync":
                if not self.panel_user():
                    return self._send(401, {"ok": False})
                repo.request_sync()
                return self._send(200, {"ok": True})
            if p == "/api/v1/logs":
                user = self.token_user()
                if not user:
                    return self._send(401, {"ok": False, "error": "unauthorized"})
                try:
                    body = json.loads((self._body() or b"").decode("utf-8"))
                    entries = body.get("entries") or []
                    assert isinstance(entries, list)
                except Exception:
                    return self._send(400, {"ok": False, "error": "bad json"})
                n = 0
                for e in entries:
                    if isinstance(e, dict) and isinstance(e.get("lines"), list):
                        n += store.append(user, e.get("world", ""), e.get("char", ""), e["lines"])
                        try:
                            issues.append(user, e.get("world", ""), e.get("char", ""), e["lines"][:5000])
                        except Exception as ex:
                            log.warning("ostrzeżenia/błędy: %s", ex)
                log.info("logi: %d linii (%s, %s, %s)", n, user, str(body.get("source", ""))[:40], self.client_ip())
                return self._send(200, {"ok": True, "written": n})
            if p == "/api/v1/locks":
                user = self.token_user()
                if not user:
                    return self._send(401, {"ok": False, "error": "unauthorized"})
                try:
                    b = json.loads((self._body() or b"").decode("utf-8"))
                    assert isinstance(b, dict)
                except Exception:
                    return self._send(400, {"ok": False, "error": "bad json"})
                return self._send(200, dict(locks.call(user, b.get("world", ""), b.get("char", ""), b.get("acquire"), b.get("release")), ok=True))
            if p == "/api/v1/heartbeat":
                user = self.token_user()
                if not user:
                    return self._send(401, {"ok": False, "error": "unauthorized"})
                try:
                    info = json.loads((self._body() or b"").decode("utf-8"))
                    assert isinstance(info, dict) and info.get("char")
                except Exception:
                    return self._send(400, {"ok": False, "error": "bad json"})
                keep = {k: (str(info[k])[:200] if isinstance(info[k], str) else info[k])
                        for k in ("char", "world", "version", "running", "map", "lvl", "step", "source", "prof", "host_id", "session") if k in info}
                presence.beat(user, keep)
                if isinstance(info.get("ops"), dict) and info["ops"]:
                    opstats.add(user, info["ops"])
                return self._send(200, {"ok": True})
            if p in ("/api/v1/host/heartbeat", "/api/v1/host/state"):
                user = self.token_user()
                if not user:
                    return self._send(401, {"ok": False, "error": "unauthorized"})
                try:
                    body = json.loads((self._body() or b"").decode("utf-8"))
                    hid = safe_name(body.get("host_id"), "")
                    assert hid
                except Exception:
                    return self._send(400, {"ok": False, "error": "bad json"})
                name = str(body.get("name", ""))[:64]
                if p.endswith("state"):
                    updated = hosts.save_state(user, hid, name, body.get("state") or {}, body.get("configs") or {})
                    log.info("ustawienia launchera: %s / %s (%s)", user, name or hid, self.client_ip())
                    return self._send(200, {"ok": True, "updated": updated})
                sess = []
                val = lambda v: v if isinstance(v, (bool, int, float)) else str(v if v is not None else "")[:100]
                for x in (body.get("sessions") or [])[:200]:
                    if isinstance(x, dict):
                        sess.append({str(k)[:32]: val(v) for k, v in list(x.items())[:30]})
                opts = body.get("options") if isinstance(body.get("options"), dict) else {}
                clean_opts = {}
                for k in ("groups", "configs", "config_profs", "servers", "browsers", "programs", "screens", "zooms", "worlds"):
                    v = opts.get(k)
                    if isinstance(v, list):
                        clean_opts[k] = [({str(kk)[:32]: val(vv) for kk, vv in list(x.items())[:20]} if isinstance(x, dict) else val(x)) for x in v[:300]]
                if isinstance(opts.get("templates"), dict):
                    clean_opts["templates"] = {str(b)[:20]: [str(t)[:64] for t in (ts or [])[:100]] for b, ts in list(opts["templates"].items())[:5]}
                info = {"host_id": hid, "name": name, "platform": str(body.get("platform", ""))[:40], "options": clean_opts,
                        "version": str(body.get("version", ""))[:20], "sessions": sess, "results": body.get("results") or []}
                return self._send(200, {"ok": True, "commands": hosts.beat(user, info)})
            if p == "/panel/api/host/command":
                user = self.panel_user()
                if not user:
                    return self._send(401, {"ok": False})
                if "application/json" not in self.headers.get("Content-Type", ""):
                    return self._send(400, {"ok": False})
                try:
                    body = json.loads((self._body() or b"").decode("utf-8"))
                    action = body.get("action")
                    assert action in ("start", "stop", "bot_start", "bot_stop", "create_session", "update_session",
                                      "delete_session", "create_config", "set_config_prof",
                                      "create_group", "rename_group", "delete_group", "update_group", "delete_banned", "refresh")
                    assert action not in ("start", "stop", "bot_start", "bot_stop", "refresh", "update_session", "delete_session") or body.get("session")
                    params = body.get("params") if isinstance(body.get("params"), dict) else {}
                    params = {str(k)[:32]: (v if isinstance(v, bool) else str(v)[:120]) for k, v in list(params.items())[:20]}
                except Exception:
                    return self._send(400, {"ok": False, "error": "bad request"})
                hid = safe_name(parse_qs(urlparse(self.path).query).get("id", [""])[0], "")
                if not hid:
                    return self._send(400, {"ok": False, "error": "no host"})
                cid = hosts.command(user, hid, action, str(body.get("session", ""))[:64], str(body.get("session_name", ""))[:64], params)
                log.info("polecenie %s %s → %s (%s)", action, body.get("session_name"), hid, user)
                return self._send(200, {"ok": True, "id": cid})
            if p == "/login":
                return self._login_post()
            if p == "/password":
                user = self.panel_user()
                if not user:
                    return self._redirect("/login")
                return self._password_post(user)
            if p == "/token":
                user = self._require_panel()
                if user:
                    users.new_token(user)
                    self._redirect("/")
                return
            self._send(404, {"ok": False, "error": "not found"})

        # ── strony ──
        def _login_page(self, err=""):
            self._html(200, "Logowanie", f"""<div class="login card"><h2>🐙 Kraken – logowanie</h2>
<form method="post" action="/login"><input type="text" name="user" placeholder="Użytkownik" autofocus autocomplete="username">
<input type="password" name="pw" placeholder="Hasło" autocomplete="current-password">
<button class="pri" type="submit">Zaloguj</button>{f'<div class="err">{html.escape(err)}</div>' if err else ''}</form></div>""")

        def _login_post(self):
            ip = self.client_ip()
            n, since = fails.get(ip, (0, 0))
            if n >= 5 and time.time() - since < 60:
                return self._login_page("Za dużo prób – odczekaj minutę")
            f = self._form()
            name, pw = f.get("user", "").strip(), f.get("pw", "")
            u = users.get(name)
            if not u or not check_password(pw, u["pw"]):
                fails[ip] = (n + 1 if time.time() - since < 600 else 1, since if n else time.time())
                time.sleep(1)
                log.warning("nieudane logowanie do panelu: %r z %s", name, ip)
                return self._login_page("Zły użytkownik lub hasło")
            fails.pop(ip, None)
            sid = secrets.token_urlsafe(32)
            with slock:
                sessions[sid] = {"user": name, "exp": time.time() + cfg["panel_session_hours"] * 3600}
            cookie = f"kraken_sid={sid}; Path=/; Max-Age={cfg['panel_session_hours'] * 3600}; HttpOnly; Secure; SameSite=Strict"
            log.info("logowanie do panelu: %s z %s", name, ip)
            self._redirect("/password" if u.get("must_change") else "/", {"Set-Cookie": cookie})

        def _password_page(self, user, err="", ok=""):
            must = users.get(user).get("must_change")
            self._html(200, "Hasło", f"""<main><div class="card" style="max-width:420px">
<h2>{'Ustaw nowe hasło (wymagane przy pierwszym logowaniu)' if must else 'Zmiana hasła'}</h2>
<form method="post" action="/password" style="display:grid;gap:10px">
<input type="password" name="old" placeholder="Obecne hasło" autocomplete="current-password">
<input type="password" name="new" placeholder="Nowe hasło (min. 8 znaków)" autocomplete="new-password">
<input type="password" name="new2" placeholder="Powtórz nowe hasło" autocomplete="new-password">
<button class="pri" type="submit">Zapisz</button>
{f'<div class="err">{html.escape(err)}</div>' if err else ''}{f'<div style="color:var(--ok)">{html.escape(ok)}</div>' if ok else ''}
</form></div></main>""", user)

        def _password_post(self, user):
            f = self._form()
            u = users.get(user)
            if not check_password(f.get("old", ""), u["pw"]):
                return self._password_page(user, "Złe obecne hasło")
            new = f.get("new", "")
            if len(new) < 8:
                return self._password_page(user, "Nowe hasło musi mieć co najmniej 8 znaków")
            if new != f.get("new2", ""):
                return self._password_page(user, "Hasła się różnią")
            if new == "admin" or check_password(new, u["pw"]):
                return self._password_page(user, "Nowe hasło musi być inne niż obecne")
            users.set_password(user, new)
            log.info("zmiana hasła: %s", user)
            self._redirect("/")

        # ── dane bota (tylko z tokenem) ──
        def _data_json(self, raw):
            return b'{"ok":true,"ref":"' + repo.ref.encode() + b'","data":' + raw + b"}"

        def _data_get(self, p, q):
            if not self.token_user():
                return self._send(401, {"ok": False, "error": "unauthorized"})
            if p == "/api/v1/data/status":
                return self._send(200, dict({"ok": True}, **repo.status()))
            if p == "/api/v1/data/world":
                if not repo.world:
                    return self._send(503, {"ok": False, "error": "dane jeszcze się wczytują"})
                return self._send(200, self._data_json(repo.world))
            if not repo.ref:
                return self._send(503, {"ok": False, "error": "dane jeszcze się wczytują"})
            kind = q.get("kind", "")
            if kind not in KINDS:
                return self._send(400, {"ok": False, "error": "kind"})
            if p == "/api/v1/data/pack":
                if kind not in repo.PACK_KINDS:
                    return self._send(400, {"ok": False, "error": "kind"})
                return self._send(200, b'{"ok":true,"ref":"' + repo.ref.encode() + b'","items":' + repo.pack(kind, q.get("prof", "")) + b"}")
            if p == "/api/v1/data/list":
                ref, items = repo.list(kind, q.get("prof", ""))
                return self._send(200, {"ok": True, "ref": ref, "items": items})
            if p == "/api/v1/data/get":
                raw = repo.get(kind, q.get("key", ""))
                if raw is None:
                    return self._send(404, {"ok": False, "error": "brak", "ref": repo.ref})
                return self._send(200, self._data_json(raw))
            return self._send(404, {"ok": False, "error": "not found"})

        def _data_batch(self):
            if not self.token_user():
                return self._send(401, {"ok": False, "error": "unauthorized"})
            try:
                items = json.loads((self._body() or b"").decode("utf-8")).get("items") or []
                assert isinstance(items, list) and len(items) <= 100
            except Exception:
                return self._send(400, {"ok": False, "error": "bad request"})
            if not repo.ref:
                return self._send(503, {"ok": False, "error": "dane jeszcze się wczytują"})
            parts = []
            for it in items:
                kind, key = str((it or {}).get("kind", "")), str((it or {}).get("key", ""))[:200]
                raw = repo.get(kind, key) if kind in KINDS else None
                parts.append(b'{"kind":' + json.dumps(kind).encode() + b',"key":' + json.dumps(key, ensure_ascii=False).encode()
                             + b',"data":' + (raw if raw is not None else b"null") + b"}")
            return self._send(200, b'{"ok":true,"ref":"' + repo.ref.encode() + b'","items":[' + b",".join(parts) + b"]}")

        def _dashboard(self, user):
            tok = html.escape(users.get(user)["token"])
            exp = users.get(user).get("token_expires") or 0
            exp_txt = time.strftime("%d.%m.%Y %H:%M", time.localtime(exp)) if exp else "bez terminu"
            left = int((exp - time.time()) // 86400) if exp else 0
            self._html(200, "Pulpit", f"""<main class="wide">
<div class="tiles" id="tiles"></div>
<div class="charts">
<div class="card chart"><h2>Aktywność – ostatnie 24 h</h2><div class="legend"><span><i style="background:#3987e5"></i>Sesje aktywne</span><span><i style="background:#d95926"></i>Boty pracują</span></div><div id="c_act"></div></div>
<div class="card chart"><h2>Sesje online na hostach</h2><div id="c_hosts"></div></div>
<div class="card chart"><h2>Poziomy postaci online</h2><div id="c_lvl"></div></div>
<div class="card chart"><h2>Profesje online</h2><div id="c_prof"></div></div>
<div class="card" style="grid-column:1/-1;display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="color:var(--acc)">Zakres</b><span id="range" style="display:flex;gap:4px;flex-wrap:wrap"></span><span class="hint">operacje botów (tu) oraz ostrzeżenia i błędy (na dole strony)</span></div>
<div class="card chart" style="grid-column:1/-1"><h2>Operacje botów – <span id="ops_range">24 h</span></h2><div class="legend"><span><i style="background:#0ca30c"></i>✔ udane</span><span><i style="background:#fab219"></i>⚠ wolne (po ostrzeżeniu 120 s)</span><span><i style="background:#d03b3b"></i>✖ nieudane (błąd albo 5 min bez zakończenia)</span></div><div id="c_ops"></div></div>
</div>
<div class="card"><h2>Hosty</h2><p class="hint">Maszyny z działającym launcherem; „niezarządzany” – boty uruchomione poza launcherem.</p>
<div class="tbl-wrap"><table><thead><tr><th>Stan</th><th>Host</th><th>System</th><th>Sesje (online / w launcherze)</th><th>Ostatnio</th></tr></thead><tbody id="hrows"><tr><td colspan=5 class=hint>Wczytuję…</td></tr></tbody></table></div></div>
<div class="card"><h2>Sesje <span class="hint" id="fcount" style="font-size:12.5px;font-weight:400;margin-left:8px"></span></h2><div class="tbl-wrap"><table>
<thead><tr><th>Stan</th><th>Host</th><th>Grupa</th><th>Sesja</th><th>Świat</th><th>Postać</th><th>Profesja</th><th>Poziom</th><th>Program</th><th>Krok</th><th>Ostatnio</th></tr><tr id="frow"></tr></thead>
<tbody id="rows"><tr><td colspan=11 class=hint>Wczytuję…</td></tr></tbody></table></div></div>
<div class="card"><h2>Token użytkownika</h2>
<div class="tok" id="tok">{tok}</div>
<p class="hint">Ważny do <b>{exp_txt}</b>{f" (jeszcze {left} dni)" if exp else ""}. Wpisz go w bocie Kraken (pierwszy ekran bota: adres tej strony i token)
i w launcherze (pierwszy ekran po uruchomieniu). Bez ważnego tokenu bot i launcher nie działają.</p>
<form method="post" action="/token" onsubmit="return confirm('Zrolować token? Obecny przestanie działać od razu: wszystkie boty i launchery na nim stracą autoryzację (boty się zatrzymają) – trzeba będzie wpisać nowy token. Kontynuować?')">
<button type="button" onclick="navigator.clipboard.writeText(document.getElementById('tok').textContent)">Kopiuj</button>
<button type="submit">🔄 Zroluj token</button></form></div>
<div class="card"><h2>Dane bota <button class="sm" id="dsync" style="float:right">⟳ Pobierz z repo</button></h2><div class="hint" id="dstat">Wczytuję…</div></div>
<div class="card chart"><h2>Ostrzeżenia i błędy – <span id="iss_range">24 h</span> <span style="float:right;font-size:12.5px;font-weight:400"><a id="iss_dl" href="/panel/api/issues?hours=24">⬇ pobierz (JSONL)</a></span></h2>
<div style="display:flex;gap:4px;flex-wrap:wrap;margin:2px 0 8px" id="range2"></div>
<div class="hint" id="iss_sum" style="margin-bottom:6px"></div>
<h3 style="font-size:13px;color:var(--dim);font-weight:500;margin:8px 0 4px">Najczęstsze komunikaty (liczby zastąpione przez N)</h3>
<div class="legend"><span><i style="background:#fab219"></i>⚠ ostrzeżenia</span><span><i style="background:#d03b3b"></i>✖ błędy</span></div><div id="c_iss"></div>
<div class="grid2" style="margin-top:12px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))"><select id="if_lvl"><option value="">ostrzeżenia i błędy</option><option value="warn">tylko ostrzeżenia</option><option value="error">tylko błędy</option></select>
<select id="if_char"><option value="">wszystkie postacie</option></select><input type="text" id="if_q" placeholder="szukaj w komunikacie / kroku"></div>
<div class="hint" id="icount" style="margin:6px 0"></div>
<div class="tbl-wrap"><table><thead><tr><th>Czas</th><th>Poziom</th><th>Postać</th><th>Krok</th><th>Komunikat</th></tr></thead><tbody id="irows"></tbody></table></div></div>
<div id="tip"></div></main><script>{DASH_JS}</script>""", user)

        def _host_page(self, user):
            self._html(200, "Host", f"""<main><div class="card"><h2 id="hn">Host</h2><div class="hint" id="hs"></div></div>
<div class="card"><h2>Sesje <button class="sm" id="del_banned" style="float:right;display:none"></button></h2><table><thead><tr><th>Sesja</th><th>Bot</th><th>Nazwa</th><th>Grupa</th><th>Config</th><th>Profesja</th><th>Program</th><th></th></tr></thead>
<tbody id="rows"><tr><td colspan=8 class=hint>Wczytuję…</td></tr></tbody></table>
<div id="edit" class="card" style="display:none;margin-top:12px"></div>
<p class="hint">Polecenia trafiają do launchera przy jego następnym sygnale (do 10 s). ⏸ Bot zatrzymuje samego bota – przeglądarka i gra zostają.</p></div>
<div class="card"><h2>Grupy</h2><table><thead><tr><th>Grupa</th><th>Świat</th><th>Program grupy</th><th>Układ okien</th><th></th></tr></thead>
<tbody id="grows"></tbody></table><div id="gedit" class="card" style="display:none;margin-top:12px"></div>
<div class="grid2" style="margin-top:10px"><label>Nowa grupa<input type="text" id="ng_name" placeholder="nazwa"></label><label>Świat<select id="ng_world"></select></label></div>
<div style="margin-top:8px"><button class="pri" id="ng_go">＋ Utwórz grupę</button></div></div>
<div class="card"><h2>Nowa sesja</h2>
<div class="grid2"><label>Nazwa<input type="text" id="ns_name" placeholder="puste = automatyczna"></label>
<label>Grupa<select id="ns_group"></select></label><label>Config<select id="ns_config"></select></label>
<label>Serwer<select id="ns_server"></select></label><label>Przeglądarka<select id="ns_browser"></select></label>
<label>Szablon profilu<select id="ns_template"></select></label><label>Program (opcjonalnie)<select id="ns_program"></select></label></div>
<div style="margin-top:10px"><button class="pri" id="ns_go">＋ Utwórz sesję</button> <span class="hint" id="ns_info"></span></div></div>
<div class="card"><h2>Configi</h2><table><thead><tr><th>Config</th><th>Profesja</th></tr></thead><tbody id="crows"></tbody></table>
<h2 style="margin-top:14px">Nowy config</h2>
<div class="grid2"><label>Rodzaj<select id="nc_mode"><option value="auto">Nowe konto – login, hasło i nick generowane (konto zakłada START sesji)</option><option value="manual">Istniejące konto – podaję login i hasło</option></select></label>
<label class="nc-man">Nazwa pliku<input type="text" id="nc_name" placeholder="np. MojaPostac"></label>
<label class="nc-man">Login<input type="text" id="nc_login" autocomplete="off"></label>
<label class="nc-man">Hasło<input type="password" id="nc_pw" autocomplete="new-password"></label>
<label>Profesja<select id="nc_prof"></select></label></div>
<div style="margin-top:10px"><button class="pri" id="nc_go">＋ Utwórz config</button> <span class="hint" id="nc_info"></span></div></div>
<div class="card"><h2>Ostatnie polecenia</h2><div id="cmds"></div></div></main><script>{HOST_JS}</script>""", user)

        def _session_page(self, user, world, char):
            self._html(200, char or "Sesja", f"""<main><div class="card">
<h2>{html.escape(char)} <span class="hint">@ {html.escape(world)}</span></h2>
<div class="hint" id="st"></div></div><div id="log"></div></main><script>{LIVE_JS}</script>""", user)

        def _sessions(self, user):
            now = time.time()
            pres = presence.of(user)
            rows = {}
            for c in store.chars(user):
                rows[(c["world"], c["char"])] = {"world": c["world"], "char": display_name(c["char"]), "last": c["mtime"]}
            for (w, c), v in pres.items():
                r = rows.setdefault((w, c), {"world": w, "char": display_name(c), "last": None})
                if v.get("char"):
                    r["char"] = str(v["char"])          # nick z gry (bot) – dokładna pisownia
                r.update({k: v.get(k) for k in ("version", "running", "map", "lvl", "step")})
                r["last"] = max(r["last"] or 0, int(v["ts"]))
                r["online"] = now - v["ts"] < online_s
            host_of = {}
            for h in hosts.of(user, online_s):
                for x in h.get("sessions") or []:
                    if h.get("online") and x.get("char"):
                        host_of[(safe_name(x.get("world"), "unknown").lower(), safe_name(x["char"], "unknown"))] = h.get("name") or h["host_id"]
            out = list(rows.values())
            for r in out:
                r.setdefault("online", False)
                r["host"] = host_of.get((str(r["world"]).lower(), safe_name(r["char"], "unknown")), "")
            out.sort(key=lambda r: (not r["online"], -(r["last"] or 0)))
            return out

    return Handler


def load_config(path):
    cfg = dict(DEFAULTS)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    for env, key, cast in (("KRAKEN_API_HOST", "host", str), ("KRAKEN_API_PORT", "port", int), ("KRAKEN_API_DATA", "data_dir", str)):
        if os.environ.get(env):
            cfg[key] = cast(os.environ[env])
    return cfg


def main():
    ap = argparse.ArgumentParser(description="Kraken API – logi postaci i panel")
    ap.add_argument("--config", default=os.environ.get("KRAKEN_API_CONFIG", "/etc/kraken-api/config.json"))
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    cfg = load_config(args.config)
    os.makedirs(cfg["data_dir"], exist_ok=True)
    users = Users(cfg["data_dir"], cfg.get("tokens", []))
    store = Store(cfg)
    presence = Presence()
    ThreadingHTTPServer.request_queue_size = 128     # domyślne 5 – za mało przy wielu postaciach naraz
    hosts = Hosts(cfg)
    repo = DataRepo(cfg)
    repo.start()
    history = History(store.root)
    opstats = OpStats(store.root)
    issues = Issues(store.root)
    locks = RouteLocks()
    threading.Thread(target=history_sampler, args=(users, store, presence, hosts, history, int(cfg["online_seconds"]), 300, opstats),
                     daemon=True, name="history").start()
    httpd = ThreadingHTTPServer((cfg["host"], int(cfg["port"])), make_handler(cfg, users, store, presence, hosts, repo, history, opstats, issues, locks))
    httpd.daemon_threads = True

    def stop(*_):
        log.info("zatrzymuję serwer")
        try:
            opstats.flush()
        except Exception:
            pass
        threading.Thread(target=httpd.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    log.info("Kraken API %s na %s:%s, dane: %s", VERSION, cfg["host"], cfg["port"], cfg["data_dir"])
    httpd.serve_forever()
    httpd.server_close()


if __name__ == "__main__":
    main()
