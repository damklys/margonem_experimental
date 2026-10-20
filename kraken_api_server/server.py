#!/usr/bin/env python3
"""Kraken API – serwer logów i panel WWW (demon systemd, sama biblioteka standardowa, Python 3.8+).

Użytkownicy panelu mają token. Bot Kraken (przeglądarka) i launcher wysyłają z tym tokenem logi postaci i sygnał
„żyję” – serwer odkłada logi danego użytkownika w <data_dir>/users/<użytkownik>/logs/<świat>/<postać>.log,
a panel pokazuje, które sesje są online, i log sesji na żywo.

Pierwsze uruchomienie: użytkownik admin / hasło admin – panel wymusza zmianę hasła po zalogowaniu.

API bota / launchera (nagłówek Authorization: Bearer <token użytkownika>, CORS dla stron gry):
  GET  /api/v1/health      – bez tokenu
  GET  /api/v1/me          – czy token jest poprawny: {"ok", "user"}
  POST /api/v1/logs        – {"source", "entries": [{"char", "world", "lines": [...]}]} (opcjonalnie gzip)
  POST /api/v1/heartbeat   – {"char", "world", "version", "running", "map", "lvl", "step", "source"}
Panel: /  (sesje użytkownika i token), /session?world=&char=  (log na żywo), /password, /login, /logout
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

VERSION = "2.0.0"
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
        self.legacy = [t for t in legacy_tokens if t]

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.path)

    def get(self, name):
        return self.data["users"].get(name)

    def by_token(self, token):
        if not token:
            return None
        for name, u in self.data["users"].items():
            if hmac.compare_digest(token, u.get("token", "")):
                return name
        if any(hmac.compare_digest(token, t) for t in self.legacy):
            return "admin"
        return None

    def set_password(self, name, pw):
        with self.lock:
            u = self.data["users"][name]
            u["pw"] = hash_password(pw)
            u["must_change"] = False
            self.save()

    def new_token(self, name):
        with self.lock:
            self.data["users"][name]["token"] = secrets.token_urlsafe(32)
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


# ───────────────────────── HTML panelu ─────────────────────────

CSS = """
:root{--bg:#0b0e1a;--bg2:#111526;--bg3:#1a2038;--fg:#d8c79a;--dim:#7d8aa8;--acc:#c8921e;--ok:#3fb26b;--off:#6b7280;--bad:#d55}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--acc)}header{display:flex;align-items:center;gap:12px;padding:10px 18px;background:var(--bg2);border-bottom:1px solid #222a44}
header b{font-size:16px}header .sp{flex:1}main{max-width:1100px;margin:0 auto;padding:18px}
.card{background:var(--bg2);border:1px solid #222a44;border-radius:8px;padding:14px 16px;margin-bottom:14px}
h2{margin:0 0 10px;font-size:15px;color:var(--acc)}input,button{font:inherit}
input[type=text],input[type=password]{background:var(--bg3);color:var(--fg);border:1px solid #2c3656;border-radius:5px;padding:7px 9px;width:100%}
button,.btn{background:var(--bg3);color:var(--fg);border:1px solid #2c3656;border-radius:5px;padding:6px 12px;cursor:pointer;text-decoration:none;display:inline-block}
button.pri{background:var(--acc);color:#111;border-color:var(--acc);font-weight:600}
table{width:100%;border-collapse:collapse}td,th{padding:6px 8px;border-bottom:1px solid #1d2440;text-align:left}th{color:var(--dim);font-weight:500}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:var(--off)}.dot.on{background:var(--ok)}
.tok{font-family:ui-monospace,Menlo,Consolas,monospace;background:var(--bg3);padding:6px 9px;border-radius:5px;word-break:break-all}
.err{color:var(--bad)}.hint{color:var(--dim);font-size:12.5px}
.login{max-width:360px;margin:12vh auto}.login form>*{margin-bottom:10px}
#log{font:12.5px/1.4 ui-monospace,Menlo,Consolas,monospace;background:#070912;border:1px solid #1d2440;border-radius:6px;padding:10px;height:70vh;overflow:auto;white-space:pre-wrap;word-break:break-word}
.l-blad{color:#e06c6c}.l-ostrzezenie{color:#e0b44c}.l-sukces{color:#5fc77f}.l-launcher{color:#7d8aa8}
"""


def page(title, body, user=None):
    nav = (f'<header><b>🐙 Kraken</b><span class="sp"></span><span class="hint">{html.escape(user)}</span>'
           f'<a class="btn" href="/">Sesje</a><a class="btn" href="/password">Hasło</a><a class="btn" href="/logout">Wyloguj</a></header>'
           if user else "")
    return (f'<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)} – Kraken</title><style>{CSS}</style></head><body>{nav}{body}</body></html>')


DASH_JS = """
const fmt=(s)=>{if(s==null)return'—';const d=Math.round(Date.now()/1000-s);return d<60?d+' s temu':d<3600?Math.round(d/60)+' min temu':new Date(s*1000).toLocaleString('pl-PL')};
async function load(){const r=await fetch('/panel/api/sessions');if(r.status===401){location='/login';return}
const list=await r.json();const tb=document.getElementById('rows');tb.textContent='';
if(!list.length){tb.innerHTML='<tr><td colspan=6 class=hint>Brak sesji – wpisz token w bocie (Ustawienia › Serwer) albo w launcherze (api.json).</td></tr>';return}
for(const s of list){const tr=document.createElement('tr');const u=`/session?world=${encodeURIComponent(s.world)}&char=${encodeURIComponent(s.char)}`;
tr.innerHTML=`<td><span class="dot ${s.online?'on':''}"></span>${s.online?'online':'offline'}</td><td><a></a></td><td></td><td></td><td></td><td></td>`;
const a=tr.children[1].firstChild;a.href=u;a.textContent=s.char;tr.children[2].textContent=s.world;
tr.children[3].textContent=[s.lvl?('lvl '+s.lvl):'',s.map||''].filter(Boolean).join(' · ');tr.children[4].textContent=s.step||(s.running===false?'zatrzymany':'');
tr.children[5].textContent=fmt(s.last);tb.appendChild(tr)}}
load();setInterval(load,5000);
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

def make_handler(cfg, users, store, presence):
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
            self.send_response(code)
            self.send_header("Content-Type", ctype)
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
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > cfg["max_body_bytes"]:
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
                u = self.token_user()
                return self._send(200 if u else 401, {"ok": bool(u), "user": u})
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
            p = urlparse(self.path).path
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
                log.info("logi: %d linii (%s, %s, %s)", n, user, str(body.get("source", ""))[:40], self.client_ip())
                return self._send(200, {"ok": True, "written": n})
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
                        for k in ("char", "world", "version", "running", "map", "lvl", "step", "source") if k in info}
                presence.beat(user, keep)
                return self._send(200, {"ok": True})
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

        def _dashboard(self, user):
            tok = html.escape(users.get(user)["token"])
            self._html(200, "Sesje", f"""<main>
<div class="card"><h2>Token użytkownika</h2>
<div class="tok" id="tok">{tok}</div>
<p class="hint">Wpisz go w bocie Kraken (⚙️ Ustawienia › Serwer, razem z adresem tej strony) i/lub w launcherze
(<code>api.json</code>). Logi i stan sesji trafią na to konto.</p>
<form method="post" action="/token" onsubmit="return confirm('Nowy token unieważni obecny – trzeba go będzie wpisać ponownie w botach. Kontynuować?')">
<button type="button" onclick="navigator.clipboard.writeText(document.getElementById('tok').textContent)">Kopiuj</button>
<button type="submit">Wygeneruj nowy</button></form></div>
<div class="card"><h2>Sesje</h2><table><thead><tr><th>Stan</th><th>Postać</th><th>Świat</th><th>Postęp</th><th>Krok</th><th>Ostatnio</th></tr></thead>
<tbody id="rows"><tr><td colspan=6 class=hint>Wczytuję…</td></tr></tbody></table></div></main><script>{DASH_JS}</script>""", user)

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
            out = list(rows.values())
            for r in out:
                r.setdefault("online", False)
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
    httpd = ThreadingHTTPServer((cfg["host"], int(cfg["port"])), make_handler(cfg, users, store, presence))
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
