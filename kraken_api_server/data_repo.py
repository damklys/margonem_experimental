"""Dane bota Kraken z checkoutu repo na serwerze (git clone/fetch co kilka minut) – bot pobiera je z API z tokenem,
na żądanie bieżącego kroku, zamiast ściągać wszystko z publicznego GitHuba.

Rodzaje (katalogi w kraken_user_client/) i klucze, po których bot o nie pyta:
  map      maps/*.json       nazwa mapy ("name")
  npc      npc/**.json       ścieżka względem npc/ bez .json (np. "healer/Ithan")
  quest    quests/*.json     nazwa zadania ("name")
  route    routes/*.json     id trasy ("route.id"); nazwa trasy też działa
  set      sets/<prof>/*.json  "<prof>/<nazwa zestawu>" (np. "m/20lvl")
  playbook playbooks/*.json  nazwa przebiegu ("name")
  skill    skills/*.json     profesja ("prof")
Graf świata (DATA: world, heros, e2) – z kodu bota (const DATA = … w kraken-bot.user.js).
"""
import json
import logging
import os
import subprocess
import threading
import time

log = logging.getLogger("kraken-api")

KINDS = {"map": "maps", "npc": "npc", "quest": "quests", "route": "routes", "set": "sets",
         "playbook": "playbooks", "skill": "skills"}
CLIENT_DIR = "kraken_user_client"
BOT_FILE = "kraken-bot.user.js"


def _keys(kind, rel, d):
    """Klucze wpisu (pierwszy główny) i krótki opis do listy – dla bota, bez pobierania całych plików."""
    stem = os.path.splitext(os.path.basename(rel))[0]
    meta = {}
    if kind == "route":
        r = d.get("route") or {}
        meta = {"name": r.get("name", ""), "lvlMin": r.get("lvlMin"), "lvlMax": r.get("lvlMax")}
        return [str(r.get("id") or stem)] + ([r["name"]] if r.get("name") else []), meta
    if kind == "set":
        s = d.get("set") or {}
        prof = str(d.get("prof") or rel.split("/")[0])
        meta = {"prof": prof, "lvl": s.get("lvl")}
        return [f"{prof}/{s.get('name') or stem}"], meta
    if kind == "quest":
        meta = {"lvl": d.get("lvl"), "questId": d.get("questId")}
        return [str(d.get("name") or stem)], meta
    if kind == "playbook":
        return [str(d.get("name") or stem)], {"tiles": len(d.get("tiles") or [])}
    if kind == "map":
        return [str(d.get("name") or stem)], {"id": d.get("id")}
    if kind == "skill":
        return [str(d.get("prof") or stem)], {"profName": d.get("profName", "")}
    return [os.path.splitext(rel)[0]], {}


class DataRepo:
    def __init__(self, cfg):
        self.dir = cfg.get("repo_dir") or os.path.join(cfg["data_dir"], "repo")
        self.url = cfg.get("repo_url") or "https://github.com/damklys/margonem_experimental.git"
        self.branch = cfg.get("repo_branch") or "main"
        self.every = max(60, int(cfg.get("repo_sync_seconds") or 600))
        self.lock = threading.Lock()
        self.ref = ""
        self.updated = 0
        self.error = ""
        self.index = {k: {} for k in KINDS}     # rodzaj → klucz → ścieżka pliku
        self.meta = {k: {} for k in KINDS}      # rodzaj → klucz główny → opis
        self.world = None                        # bajty JSON grafu świata (DATA)
        self._wake = threading.Event()

    # ── synchronizacja ──
    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="data-repo").start()

    def request_sync(self):
        self._wake.set()

    def _loop(self):
        while True:
            try:
                self.sync()
            except Exception as e:
                self.error = str(e)[:300]
                log.warning("dane repo: %s", e)
            self._wake.wait(self.every)
            self._wake.clear()

    def _git(self, *args, timeout=300):
        r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=timeout,
                           env=dict(os.environ, GIT_TERMINAL_PROMPT="0", HOME=os.path.dirname(self.dir)))
        if r.returncode:
            raise RuntimeError(f"git {args[0]}: {(r.stderr or r.stdout).strip()[:200]}")
        return r.stdout.strip()

    def sync(self):
        # Po restarcie serwera: indeks od razu z istniejącego checkoutu (fetch z GitHuba może chwilę potrwać).
        if not self.ref and os.path.isdir(os.path.join(self.dir, ".git")):
            self._rebuild(self._git("-C", self.dir, "rev-parse", "HEAD"))
        if not os.path.isdir(os.path.join(self.dir, ".git")):
            log.info("dane repo: klonuję %s (%s) → %s", self.url, self.branch, self.dir)
            self._git("clone", "--depth", "1", "--branch", self.branch, self.url, self.dir, timeout=900)
        else:
            self._git("-C", self.dir, "fetch", "--depth", "1", "origin", self.branch)
            self._git("-C", self.dir, "reset", "--hard", "FETCH_HEAD")
        ref = self._git("-C", self.dir, "rev-parse", "HEAD")
        if ref != self.ref:
            self._rebuild(ref)
        self.error = ""

    def _rebuild(self, ref):
        t0 = time.time()
        base = os.path.join(self.dir, CLIENT_DIR)
        index = {k: {} for k in KINDS}
        meta = {k: {} for k in KINDS}
        bad = 0
        for kind, sub in KINDS.items():
            root = os.path.join(base, sub)
            for dirpath, _dirs, files in os.walk(root):
                for fn in files:
                    if not fn.endswith(".json"):
                        continue
                    path = os.path.join(dirpath, fn)
                    rel = os.path.relpath(path, root).replace(os.sep, "/")
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            d = json.load(f)
                        keys, m = _keys(kind, rel, d)
                    except Exception:
                        bad += 1
                        continue
                    # klucz główny, aliasy i ścieżka pliku (np. „gra/10160 …” – zadania o tej samej nazwie)
                    for k in keys + [os.path.splitext(rel)[0]]:
                        index[kind].setdefault(k, path)
                    meta[kind][keys[0]] = m
        world = self._extract_world(os.path.join(base, BOT_FILE))
        with self.lock:
            self.index, self.meta, self.world, self.ref, self.updated = index, meta, world, ref, time.time()
        log.info("dane repo @%s: %s%s (%.1f s)", ref[:7], ", ".join(f"{k} {len(v)}" for k, v in meta.items()),
                 f", błędnych plików {bad}" if bad else "", time.time() - t0)

    @staticmethod
    def _extract_world(path):
        """const DATA = {...}; z kodu bota → bajty JSON (graf świata, herosi, E2)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("const DATA = "):
                        raw = s[len("const DATA = "):].rstrip(";")
                        json.loads(raw)
                        return raw.encode("utf-8")
        except Exception as e:
            log.warning("dane repo: graf świata z %s – %s", path, e)
        return None

    # ── odczyt ──
    def status(self):
        with self.lock:
            return {"ref": self.ref, "updated": int(self.updated), "error": self.error,
                    "counts": {k: len(v) for k, v in self.meta.items()}, "world": bool(self.world)}

    def list(self, kind, prof=""):
        with self.lock:
            items = self.meta.get(kind) or {}
            out = [dict({"key": k}, **m) for k, m in items.items() if not prof or kind != "set" or m.get("prof") == prof]
            return self.ref, sorted(out, key=lambda x: x["key"])

    PACK_KINDS = ("map", "npc", "route", "playbook", "set", "skill")

    def pack(self, kind, prof=""):
        """Cały rodzaj jedną odpowiedzią (bajty JSON listy plików; mapy – zwięzły słownik nazwa → {id, gw, zones},
        jak MapData w bocie). Budowane raz na commit repo."""
        with self.lock:
            ref, cache = self.ref, self.__dict__.setdefault("_packs", {})
            hit = cache.get((ref, kind, prof))
            files = sorted(set(self.index.get(kind, {}).values()))
        if hit is not None:
            return hit
        if kind == "set" and prof:
            files = [f for f in files if os.path.basename(os.path.dirname(f)) == prof]
        if kind == "map":
            out = {}
            for path in files:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        rec = json.load(f)
                except Exception:
                    continue
                if rec.get("kraken") != "mapa" or not rec.get("name"):
                    continue
                zones = rec.get("zones")
                out[rec["name"]] = {"id": rec.get("id"),
                                    "gw": [[g["to"], g.get("x"), g.get("y"), g.get("req") or ""]
                                           for g in rec.get("gateways") or [] if g and g.get("to")],
                                    "zones": zones if isinstance(zones, list) and len(zones) > 1 else None}
            raw = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        else:
            parts = []
            for path in files:
                try:
                    with open(path, "rb") as f:
                        b = f.read()
                    json.loads(b)
                    parts.append(b)
                except Exception:
                    continue
            raw = b"[" + b",".join(parts) + b"]"
        with self.lock:
            if self.ref == ref:
                cache = {k: v for k, v in cache.items() if k[0] == ref}
                cache[(ref, kind, prof)] = raw
                self._packs = cache
        return raw

    def get(self, kind, key):
        """Surowe bajty pliku albo None."""
        with self.lock:
            path = (self.index.get(kind) or {}).get(key)
        if not path:
            return None
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            return None
