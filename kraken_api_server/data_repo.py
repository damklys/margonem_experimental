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

Nadpisania (edytor przebiegów w panelu): <data_dir>/overrides/<katalog rodzaju>/*.json – mają pierwszeństwo przed repo
i przetrwają aktualizację checkoutu. Wersja danych (ref) = commit repo + skrót nadpisań, więc boty widzą zmianę.
"""
import hashlib
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
        self.over_dir = os.path.join(cfg["data_dir"], "overrides")
        self.repo_ref = ""
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
        if not self.repo_ref and os.path.isdir(os.path.join(self.dir, ".git")):
            self._rebuild(self._git("-C", self.dir, "rev-parse", "HEAD"))
        if not os.path.isdir(os.path.join(self.dir, ".git")):
            log.info("dane repo: klonuję %s (%s) → %s", self.url, self.branch, self.dir)
            self._git("clone", "--depth", "1", "--branch", self.branch, self.url, self.dir, timeout=900)
        else:
            self._git("-C", self.dir, "fetch", "--depth", "1", "origin", self.branch)
            self._git("-C", self.dir, "reset", "--hard", "FETCH_HEAD")
        ref = self._git("-C", self.dir, "rev-parse", "HEAD")
        if ref != self.repo_ref:
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
        e2_keys = self._extract_e2(os.path.join(base, BOT_FILE), world)
        # Nadpisania z panelu (wygrywają z repo) i ich skrót w wersji danych.
        sig = hashlib.sha1()
        overrides = {}
        for kind, sub in KINDS.items():
            od = os.path.join(self.over_dir, sub)
            if not os.path.isdir(od):
                continue
            for fn in sorted(os.listdir(od)):
                if not fn.endswith(".json"):
                    continue
                path = os.path.join(od, fn)
                try:
                    with open(path, "rb") as fh:
                        raw = fh.read()
                    d = json.loads(raw)
                    keys, m = _keys(kind, fn, d)
                except Exception:
                    bad += 1
                    continue
                sig.update(fn.encode() + raw)
                # plik z repo o tym kluczu znika z indeksu (także jego aliasy) – nadpisanie zamiast niego
                repo_file = index[kind].get(keys[0])
                if repo_file:
                    for k in [k for k, v in index[kind].items() if v == repo_file]:
                        del index[kind][k]
                for k in keys:
                    index[kind][k] = path
                meta[kind][keys[0]] = dict(m, override=True)
                overrides.setdefault(kind, []).append(keys[0])
        full = ref + ("+" + sig.hexdigest()[:8] if overrides else "")
        with self.lock:
            self.index, self.meta, self.world, self.ref, self.updated = index, meta, world, full, time.time()
            self.repo_ref, self.overrides, self.e2_keys = ref, overrides, e2_keys
        log.info("dane repo @%s: %s%s (%.1f s)", ref[:7], ", ".join(f"{k} {len(v)}" for k, v in meta.items()),
                 f", błędnych plików {bad}" if bad else "", time.time() - t0)

    @staticmethod
    def _extract_e2(path, world):
        """Konfiguracje E2 jak w bocie: DATA.e2 + E2_SPAWNS („(lvl) nazwa”, kilka respów – „ – mapa”)."""
        import re as _re
        keys = set()
        try:
            known = json.loads(world or b"{}").get("e2", {})
            keys.update(known)
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            block = src[src.index("const E2_SPAWNS = ["):]
            block = block[:block.index("];")]
            multi = set(_re.findall(r'"([^"]+)"', src[src.index("const E2_MULTI = new Set(["):].split("]", 1)[0]))
            have = {(c.get("name"), c.get("location")) for c in known.values()}
            for name, lvl, mp in _re.findall(r'\["([^"]+)",\s*(\d+),\s*"([^"]+)",', block):
                if (name, mp) in have:
                    continue
                keys.add(f"({lvl}lvl) {name}" + (f" – {mp}" if name in multi else ""))
        except Exception as e:
            log.warning("dane repo: konfiguracje E2 z %s – %s", path, e)
        def lvl(k):
            m = _re.match(r"^\((\d+)lvl\)", k)
            return (int(m.group(1)) if m else 0, k)
        return sorted(keys, key=lvl)

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
            return {"ref": self.ref, "repo_ref": self.repo_ref, "overrides": {k: len(v) for k, v in getattr(self, "overrides", {}).items()},
                    "updated": int(self.updated), "error": self.error,
                    "counts": {k: len(v) for k, v in self.meta.items()}, "world": bool(self.world)}

    def list(self, kind, prof=""):
        with self.lock:
            items = self.meta.get(kind) or {}
            out = [dict({"key": k}, **m) for k, m in items.items() if not prof or kind != "set" or m.get("prof") == prof]
            return self.ref, sorted(out, key=lambda x: x["key"])

    # ── nadpisania (edytor przebiegów) ──
    def override_path(self, kind, key):
        safe = "".join(c if c.isalnum() or c in " -_[]().,+" else "_" for c in key).strip() or "bez_nazwy"
        return os.path.join(self.over_dir, KINDS[kind], safe[:120] + ".json")

    def is_override(self, kind, key):
        with self.lock:
            p = (self.index.get(kind) or {}).get(key, "")
        return p.startswith(self.over_dir + os.sep)

    def repo_has(self, kind, key):
        """Czy wpis jest w samym repo (bez nadpisań) – do „Przywróć z repo”."""
        root = os.path.join(self.dir, CLIENT_DIR, KINDS[kind])
        for dirpath, _d, files in os.walk(root):
            for fn in files:
                if fn.endswith(".json"):
                    try:
                        with open(os.path.join(dirpath, fn), "r", encoding="utf-8") as fh:
                            if key in _keys(kind, fn, json.load(fh))[0]:
                                return True
                    except Exception:
                        pass
        return False

    def save_override(self, kind, key, data):
        path = self.override_path(kind, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # inna nazwa pliku dla tego samego klucza (zmiana pisowni) – stary plik nadpisania znika
        with self.lock:
            old = (self.index.get(kind) or {}).get(key, "")
        if old.startswith(self.over_dir + os.sep) and old != path:
            try:
                os.remove(old)
            except OSError:
                pass
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        os.replace(tmp, path)
        self._rebuild(self.repo_ref)

    def remove_override(self, kind, key):
        with self.lock:
            p = (self.index.get(kind) or {}).get(key, "")
        if not p.startswith(self.over_dir + os.sep):
            return False
        os.remove(p)
        self._rebuild(self.repo_ref)
        return True

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
