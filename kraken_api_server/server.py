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
API launchera (host):
  POST /api/v1/host/heartbeat – {"host_id", "name", "platform", "version", "sessions": [...], "results": [...]}
                                → {"ok", "commands": [{"id", "action", "session", "session_name"}]}
  POST /api/v1/host/state     – {"host_id", "name", "state": {...}, "configs": {"plik.json": {...}}} – ustawienia launchera
  GET  /api/v1/host/state?host_id=…   – zapisane ustawienia (odtworzenie); ?list=1 – hosty z zapisanymi ustawieniami
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

VERSION = "4.1.0"
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


DASH_JS = """
const esc=(s)=>String(s??'').replace(/[&<>"]/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function hosts(){const r=await fetch('/panel/api/hosts');if(r.status===401)return;const list=await r.json();const tb=document.getElementById('hrows');tb.textContent='';
if(!list.length){tb.innerHTML='<tr><td colspan=5 class=hint>Brak hostów – w launcherze: ⚙️ Ustawienia › adres i token.</td></tr>';return}
for(const h of list){const tr=document.createElement('tr');const run=(h.sessions||[]).filter(s=>s.status==='RUNNING').length;
tr.innerHTML=`<td><span class="dot ${h.online?'on':''}"></span>${h.online?'online':'offline'}</td><td><a href="/host?id=${encodeURIComponent(h.host_id)}">${esc(h.name||h.host_id)}</a></td>
<td>${esc(h.platform||'')} ${h.version?'<span class=tag>'+esc(h.version)+'</span>':''}</td><td>${h.online?run+' / '+(h.sessions||[]).length+' uruchomionych':'—'}</td><td>${fmt(h.last)}</td>`;tb.appendChild(tr)}}
const fmt=(s)=>{if(s==null)return'—';const d=Math.round(Date.now()/1000-s);return d<60?d+' s temu':d<3600?Math.round(d/60)+' min temu':new Date(s*1000).toLocaleString('pl-PL')};
async function load(){const r=await fetch('/panel/api/sessions');if(r.status===401){location='/login';return}
const list=await r.json();const tb=document.getElementById('rows');tb.textContent='';
if(!list.length){tb.innerHTML='<tr><td colspan=7 class=hint>Brak sesji – wpisz token w bocie (Ustawienia › Serwer) albo w launcherze (api.json).</td></tr>';return}
for(const s of list){const tr=document.createElement('tr');const u=`/session?world=${encodeURIComponent(s.world)}&char=${encodeURIComponent(s.char)}`;
tr.innerHTML=`<td><span class="dot ${s.online?'on':''}"></span>${s.online?'online':'offline'}</td><td><a></a></td><td></td><td></td><td></td><td></td><td></td>`;
const a=tr.children[1].firstChild;a.href=u;a.textContent=s.char;tr.children[2].textContent=s.world;
tr.children[3].textContent=[s.lvl?('lvl '+s.lvl):'',s.map||''].filter(Boolean).join(' · ');tr.children[4].textContent=s.step||(s.running===false?'zatrzymany':'');
tr.children[5].textContent=s.host||'poza launcherem';tr.children[6].textContent=fmt(s.last);tb.appendChild(tr)}}
const tick=()=>{hosts();load()};tick();setInterval(tick,5000);
"""

HOST_JS = """
const q=new URLSearchParams(location.search);const id=q.get('id');let H={},O={},editing=null,gediting=null;
const $=(i)=>document.getElementById(i);const esc=(s)=>String(s??'').replace(/[&<>"]/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const PROFS=[['','(wybór w bocie)'],['w','wojownik'],['p','paladyn'],['b','tancerz ostrzy'],['h','łowca'],['t','tropiciel'],['m','mag']];
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
tr.innerHTML=`<td>${ST[s.status]||esc(s.status)}</td><td>${on?(BOT[s.bot]||'…'):'—'}</td><td>${esc(s.name)}</td><td>${esc(s.group)}</td><td>${esc(s.config)}</td><td>${esc(s.prof||'—')}</td><td>${esc(s.program||'(z bota)')}${s.prog_override?' <span class=tag>własny</span>':''}</td><td></td>`;
const a=tr.lastChild;a.style.whiteSpace='nowrap';
if(ps&&!ps.err){tr.className='pending';const sp=document.createElement('span');sp.className='busy';sp.innerHTML='<span class="spin"></span>'+esc(ps.txt);a.appendChild(sp);tb.appendChild(tr);continue}
if(ps&&ps.err){const e=document.createElement('div');e.className='err';e.style.fontSize='12px';e.textContent='✖ '+ps.err;a.appendChild(e)}
a.appendChild(btn(on?'⏹ Sesja':'▶ Sesja',on?'':'pri',()=>act(on?'stop':'start',s),!H.online));
a.appendChild(btn(s.bot==='running'?'⏸ Bot':'▶ Bot','',()=>act(s.bot==='running'?'bot_stop':'bot_start',s),!H.online||!on||s.bot==='loading'));
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
tr.innerHTML=`<td>${esc(g.name)}</td><td>${esc(g.world)}</td><td>${esc(g.program||'(bez zmiany)')}</td><td>${esc(lay)}</td><td></td>`;const a=tr.lastChild;
a.appendChild(btn('✎','',()=>{gediting=gediting===g.name+'|'+g.world?null:g.name+'|'+g.world;gedit()},!H.online));
a.appendChild(btn('🗑','',()=>{if(confirm(`Usunąć grupę „${g.name}”? Sesje trafią do innej grupy.`))cmd('delete_group','',g.name,{name:g.name,world:g.world})},!H.online));tb.appendChild(tr)}
if(!(O.groups||[]).length)tb.innerHTML='<tr><td colspan=5 class=hint>Brak grup.</td></tr>';$('ng_world').innerHTML=opt(O.worlds||['Gordion'],$('ng_world').value)}
function gedit(){const box=$('gedit');const g=(O.groups||[]).find(x=>x.name+'|'+x.world===gediting);if(!g){box.style.display='none';return}
if(box.dataset.g===gediting&&box.style.display!=='none')return;box.dataset.g=gediting;box.style.display='';const en=g.layout_enabled===true||g.layout_enabled==='True';
box.innerHTML=`<h2>Grupa „${esc(g.name)}”</h2><div class="grid2"><label>Nazwa<input type="text" id="eg_name" value="${esc(g.name)}"></label>
<label>Program grupy<select id="eg_program">${opt(O.programs||[],g.program||'','(bez zmiany – program z bota)')}</select></label>
<label><span><input type="checkbox" id="eg_en"${en?' checked':''}> Układaj okna przeglądarek</span></label>
<label>Ekran<select id="eg_screen">${(O.screens||[]).map((x,i)=>`<option value="${i}"${i===(+g.layout_screen||0)?' selected':''}>${esc(x.name)}</option>`).join('')}</select></label>
<label>Kolumny<input type="text" id="eg_cols" value="${esc(g.layout_cols)}"></label><label>Wiersze<input type="text" id="eg_rows" value="${esc(g.layout_rows)}"></label>
<label>Skalowanie<select id="eg_zoom">${opt((O.zooms||[]).map(z=>({value:z,label:z==='auto'?'Auto':z+'%'})),String(g.layout_zoom))}</select></label></div>
<div style="margin-top:10px"><button class="pri" id="eg_save">Zapisz</button> <button id="eg_cancel">Anuluj</button></div>`;
$('eg_cancel').onclick=()=>{gediting=null;box.style.display='none'};
$('eg_save').onclick=async()=>{const nn=$('eg_name').value.trim();await cmd('update_group','',g.name,{name:g.name,world:g.world,program:$('eg_program').value,layout_enabled:$('eg_en').checked,layout_screen:$('eg_screen').value,layout_cols:$('eg_cols').value,layout_rows:$('eg_rows').value,layout_zoom:$('eg_zoom').value});
if(nn&&nn!==g.name)await cmd('rename_group','',g.name,{name:g.name,new:nn,world:g.world});gediting=null;box.style.display='none'}}
function configs(){const tb=$('crows');tb.textContent='';for(const c of O.config_profs||[]){const tr=document.createElement('tr');tr.innerHTML=`<td>${esc(c.name)}</td><td></td>`;
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
const ACT={start:'▶ sesja',stop:'⏹ sesja',bot_start:'▶ bot',bot_stop:'⏸ bot',create_session:'＋ sesja',update_session:'✎ sesja',delete_session:'🗑 sesja',create_config:'＋ config',set_config_prof:'🎓 profesja',create_group:'＋ grupa',rename_group:'✎ nazwa grupy',delete_group:'🗑 grupa',update_group:'✎ grupa'};
async function load(){const r=await fetch(`/panel/api/host?id=${encodeURIComponent(id)}`);if(r.status===401){location='/login';return}H=await r.json();O=H.options||{};
$('hn').textContent=H.name||id;$('hs').innerHTML=`<span class="dot ${H.online?'on':''}"></span>${H.online?'online':'offline'} · ${esc(H.platform||'')} ${esc(H.version||'')}${H.saved?' · ustawienia zapisane '+new Date(H.saved*1000).toLocaleString('pl-PL'):''}`;
const none=!O.groups&&H.online;$('ns_info').textContent=none?'Launcher nie przesłał list – zaktualizuj launcher (git pull) i uruchom ponownie.':'';
for(const b of ['ns_go','nc_go','ng_go'])$(b).disabled=!H.online;
sessions();forms();edit();gedit();
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

def make_handler(cfg, users, store, presence, hosts):
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
                                      "create_group", "rename_group", "delete_group", "update_group")
                    assert action not in ("start", "stop", "bot_start", "bot_stop", "update_session", "delete_session") or body.get("session")
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
<div class="card"><h2>Hosty</h2><p class="hint">Launchery z tym tokenem. Kliknij host, żeby zobaczyć jego sesje i uruchomić je z przeglądarki.</p>
<table><thead><tr><th>Stan</th><th>Host</th><th>System</th><th>Sesje</th><th>Ostatnio</th></tr></thead><tbody id="hrows"><tr><td colspan=5 class=hint>Wczytuję…</td></tr></tbody></table></div>
<div class="card"><h2>Sesje bota</h2><p class="hint">Postacie wysyłające logi – z launchera albo uruchomione poza nim.</p>
<table><thead><tr><th>Stan</th><th>Postać</th><th>Świat</th><th>Postęp</th><th>Krok</th><th>Host</th><th>Ostatnio</th></tr></thead>
<tbody id="rows"><tr><td colspan=6 class=hint>Wczytuję…</td></tr></tbody></table></div></main><script>{DASH_JS}</script>""", user)

        def _host_page(self, user):
            self._html(200, "Host", f"""<main><div class="card"><h2 id="hn">Host</h2><div class="hint" id="hs"></div></div>
<div class="card"><h2>Sesje</h2><table><thead><tr><th>Sesja</th><th>Bot</th><th>Nazwa</th><th>Grupa</th><th>Config</th><th>Profesja</th><th>Program</th><th></th></tr></thead>
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
    httpd = ThreadingHTTPServer((cfg["host"], int(cfg["port"])), make_handler(cfg, users, store, presence, hosts))
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
