import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import time
import os
import re
import shutil
import json
import glob
import subprocess
import sys as _sys

# ============================================
# THREAD-LOCAL STREAM
# Jedno stałe zastąpienie sys.stdout/stderr.
# Każdy wątek sesji ustawia własny logger przez set_logger().
# Wszystkie print() w modułach trafiają tylko do loggera
# swojego wątku — nigdy do terminala VSCode.
# ============================================
class _ThreadLocalStream:
    def __init__(self):
        self._local = threading.local()

    def set_logger(self, logger):
        self._local.logger = logger

    def clear_logger(self):
        self._local.logger = None

    def write(self, msg: str):
        logger = getattr(self._local, "logger", None)
        if logger is not None:
            try:
                logger.write(msg)
            except Exception:
                pass

    def flush(self):
        logger = getattr(self._local, "logger", None)
        if logger is not None:
            try:
                logger.flush()
            except Exception:
                pass

    def fileno(self):
        raise AttributeError("_ThreadLocalStream has no fileno")


_THREAD_STREAM = _ThreadLocalStream()
_sys.stdout    = _THREAD_STREAM
_sys.stderr    = _THREAD_STREAM

# ============================================
# KOLORY / STAŁE  — piracki motyw (Kraken)
# ============================================
BG        = "#0b0e1a"   # głębokie morze
BG2       = "#111526"   # ciemna nawigacja
BG3       = "#1a2038"   # deska okrętowa
ACCENT    = "#c8921e"   # piraci złoto
GREEN     = "#1d7a48"   # morska zieleń
VIOLET    = "#4a3580"   # atrament
RED       = "#9b2222"   # krew / ogień
FG        = "#c4ae78"   # pergamin
FG_DIM    = "#5a6a88"   # mgła oceaniczna
BORDER    = "#1e2a48"   # ciemna rama

# System: Windows / macOS / Linux – ścieżki przeglądarek, czcionki, procesy.
IS_WIN   = _sys.platform.startswith("win")
IS_MAC   = _sys.platform == "darwin"
IS_LINUX = not IS_WIN and not IS_MAC

# Czcionki dostępne na danym systemie (Segoe UI jest tylko na Windows).
UI_FONT   = "Segoe UI" if IS_WIN else ("Helvetica Neue" if IS_MAC else "DejaVu Sans")
MONO_FONT = "Consolas" if IS_WIN else ("Menlo" if IS_MAC else "DejaVu Sans Mono")

FONT_MONO  = (MONO_FONT, 10)
FONT_SMALL = (UI_FONT, 9)
FONT_BOLD  = (UI_FONT, 10, "bold")
FONT_TITLE = (UI_FONT, 14, "bold")
FONT_GRP   = (UI_FONT, 9, "bold")

STATUS_COLORS = {
    "OFFLINE":  FG_DIM,
    "RUNNING":  GREEN,
    "STOPPING": ACCENT,
    "ERROR":    RED,
}

# Paleta kolorów dla grup (piracka tonacja)
GROUP_PALETTE = [
    "#c8921e",  # piraci złoto
    "#2a8a52",  # morska zieleń
    "#9b2222",  # szkarłat
    "#2e6db4",  # głęboki błękit
    "#7a5c2e",  # drewno
    "#4a9080",  # teal / ocean
    "#8b4a2a",  # miedź / rdza
    "#6a3a8a",  # atrament
    "#3a7a50",  # zieleń
    "#b87333",  # brąz
]

HEADER_H = 90   # stała wysokość belki z grafiką

BROWSERS = ["Chrome", "Brave"]

SERVERS = ["Gordion", "Luvia"]
SERVER_URL = {
    "Gordion": "https://gordion.margonem.pl",
    "Luvia":   "https://luvia.margonem.pl",
}
WORLDS = SERVERS

def _browser_candidates(browser: str) -> list:
    """Typowe miejsca instalacji Chrome / Brave na Windows, macOS i Linuksie."""
    if IS_WIN:
        roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        rel = {
            "Chrome": r"Google\Chrome\Application\chrome.exe",
            "Brave":  r"BraveSoftware\Brave-Browser\Application\brave.exe",
        }.get(browser)
        return [os.path.join(r, rel) for r in roots if r and rel]
    if IS_MAC:
        return {
            "Chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                       os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")],
            "Brave":  ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                       os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")],
        }.get(browser, [])
    names = {
        "Chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"],
        "Brave":  ["brave-browser", "brave", "brave-browser-stable"],
    }.get(browser, [])
    found = [shutil.which(n) for n in names]
    return [p for p in found if p] + {
        "Chrome": ["/opt/google/chrome/chrome", "/usr/bin/google-chrome"],
        "Brave":  ["/opt/brave.com/brave/brave", "/usr/bin/brave-browser"],
    }.get(browser, [])


_BROWSER_BINARY_CACHE = {}

def _browser_binary(browser: str) -> "str | None":
    """Ścieżka do pliku przeglądarki na tym systemie albo None (wtedy ChromeDriver szuka Chrome sam)."""
    if browser not in _BROWSER_BINARY_CACHE:
        _BROWSER_BINARY_CACHE[browser] = next((p for p in _browser_candidates(browser) if p and os.path.isfile(p)), None)
    return _BROWSER_BINARY_CACHE[browser]


def _win_file_major(path: str) -> "int | None":
    """Wersja główna z metadanych pliku .exe (GetFileVersionInfo) – zawsze ta, która się uruchomi."""
    try:
        import ctypes
        from ctypes import wintypes
        ver = ctypes.WinDLL("version")
        size = ver.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        if not ver.GetFileVersionInfoW(path, 0, size, buf):
            return None
        ptr, ln = ctypes.c_void_p(), wintypes.UINT()
        if not ver.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(ln)):
            return None
        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [("sig", wintypes.DWORD), ("struc", wintypes.DWORD), ("msHi", wintypes.DWORD), ("msLo", wintypes.DWORD)]
        info = ctypes.cast(ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        return info.msHi >> 16 or None
    except Exception:
        return None


def _win_browser_version(browser: str, binary: "str | None") -> "int | None":
    """Windows: najwyższa wersja z pliku .exe, rejestru (HKCU i HKLM – wpis użytkownika bywa stary po aktualizacji
    systemowej) i katalogów wersji obok .exe. (chrome.exe --version na Windows nie wypisuje wersji.)"""
    found = []
    if binary:
        found.append(_win_file_major(binary))
    keys = {
        "Chrome": [r"Software\Google\Chrome\BLBeacon", r"Software\WOW6432Node\Google\Chrome\BLBeacon"],
        "Brave":  [r"Software\BraveSoftware\Brave-Browser\BLBeacon", r"Software\WOW6432Node\BraveSoftware\Brave-Browser\BLBeacon"],
    }.get(browser, [])
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key in keys:
                try:
                    with winreg.OpenKey(hive, key) as k:
                        v, _ = winreg.QueryValueEx(k, "version")
                        m = re.match(r"(\d+)\.", str(v))
                        if m:
                            found.append(int(m.group(1)))
                except OSError:
                    continue
    except ImportError:
        pass
    if binary:
        try:
            for d in os.listdir(os.path.dirname(binary)):
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", d):
                    found.append(int(d.split(".")[0]))
        except OSError:
            pass
    found = [v for v in found if v]
    return max(found) if found else None


_DETECTED_BROWSER_VERSION_CACHE = {}

def _detect_browser_major_version(browser: str) -> int | None:
    """Odczytuje aktualną wersję główną (major) zainstalowanej przeglądarki.

    Chrome/Brave aktualizują się automatycznie w tle, więc wersja nie może
    być na sztywno wpisana w kodzie (patrz: BROWSER_VERSION niżej) - robiła
    się nieaktualna i powodowała błąd "session not created" w ChromeDriverze.
    """
    if browser in _DETECTED_BROWSER_VERSION_CACHE:
        return _DETECTED_BROWSER_VERSION_CACHE[browser]

    binary = _browser_binary(browser)
    if not binary:
        try:
            import undetected_chromedriver as uc
            binary = uc.find_chrome_executable()
        except Exception:
            binary = None

    version = None
    if IS_WIN:
        version = _win_browser_version(browser, binary)
    elif binary and os.path.exists(binary):
        try:
            out = subprocess.run(
                [binary, "--version"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            m = re.search(r"(\d+)\.\d+\.\d+\.\d+", out)
            if m:
                version = int(m.group(1))
        except Exception:
            version = None

    _DETECTED_BROWSER_VERSION_CACHE[browser] = version
    return version

# Wartości poniżej to tylko ostatnia deska ratunku, gdyby wykrycie wersji
# (patrz _detect_browser_major_version) się nie powiodło.
BROWSER_VERSION = {
    "Chrome": 149,
    "Brave":  149,
}

def _pid_alive(pid: int) -> bool:
    """Czy proces żyje. Na Windows os.kill(pid, 0) ZABIJA proces – tam pytamy WinAPI."""
    if IS_WIN:
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            h = k32.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
            k32.CloseHandle(h)
            return bool(ok) and code.value == 259          # STILL_ACTIVE
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_pid(pid: int) -> None:
    """Wymuszone zamknięcie procesu (z procesami potomnymi przeglądarki na Windows)."""
    if IS_WIN:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=15,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        import signal as _signal
        os.kill(pid, _signal.SIGKILL)


def _safe_group(group: str) -> str:
    """Nazwa katalogu grupy (ta sama przy tworzeniu profilu i przy starcie sesji)."""
    return re.sub(r'[\\/:*?"<>|\s]+', "_", group or "default").strip("_") or "default"


# ============================================
# PROGRAMY BOTA (przebiegi z kraken_user_client/playbooks)
# ============================================
DEFAULT_PROGRAM = "[1-300] Zero to hero"
_PLAYBOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kraken_user_client", "playbooks")


def _list_programs() -> list:
    """Nazwy programów predefiniowanych (pliki przebiegów w repo), w kolejności jak w bocie:
    [1-300] Zero to hero, przedziały Zero to hero wg poziomu, reszta alfabetycznie."""
    names = []
    try:
        for fn in os.listdir(_PLAYBOOKS_DIR):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(_PLAYBOOKS_DIR, fn), "r", encoding="utf-8") as f:
                        n = json.load(f).get("name")
                except Exception:
                    n = None
                names.append(n or fn[:-5])
    except OSError:
        pass
    def key(n):
        if n == DEFAULT_PROGRAM:
            return (0, 0, 0, n)
        m = re.match(r"^\[(\d+)-(\d+)\] Zero to hero$", n)
        if m:
            return (1, int(m.group(1)), -int(m.group(2)), n)
        return (2, 0, 0, n.lower())
    return sorted(set(names), key=key)


# ============================================
# UKŁAD OKIEN GRUPY (siatka na wybranym ekranie + zoom przeglądarki)
# ============================================
LAYOUT_DEFAULT = {"enabled": False, "screen": 0, "cols": 5, "rows": 2, "zoom": "auto"}
ZOOM_CHOICES = ["auto", "25", "33", "40", "50", "67", "75", "80", "90", "100"]


def _screens() -> list:
    """Ekrany: [{x, y, w, h, name}] – obszar roboczy (bez paska menu / zadań), współrzędne od lewego górnego rogu."""
    out = []
    try:
        if IS_MAC:
            from AppKit import NSScreen
            scr = list(NSScreen.screens())
            main_h = scr[0].frame().size.height
            for i, sc in enumerate(scr):
                vf = sc.visibleFrame()
                out.append({"x": int(vf.origin.x), "y": int(main_h - (vf.origin.y + vf.size.height)),
                            "w": int(vf.size.width), "h": int(vf.size.height),
                            "name": str(sc.localizedName()) if hasattr(sc, "localizedName") else f"Ekran {i + 1}"})
        elif IS_WIN:
            import ctypes
            from ctypes import wintypes
            class MONITORINFOEXW(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT),
                            ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]
            mons = []
            proc = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
            def cb(hmon, _hdc, _rc, _lp):
                mi = MONITORINFOEXW()
                mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
                if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                    r = mi.rcWork
                    mons.append((not (mi.dwFlags & 1), {"x": r.left, "y": r.top, "w": r.right - r.left,
                                                        "h": r.bottom - r.top, "name": mi.szDevice.replace("\\\\.\\", "")}))
                return 1
            ctypes.windll.user32.EnumDisplayMonitors(None, None, proc(cb), 0)
            out = [m for _, m in sorted(mons, key=lambda t: t[0])]   # główny monitor pierwszy
        else:
            r = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True, timeout=5).stdout
            for line in r.splitlines()[1:]:
                m = re.search(r"(\d+)/\d+x(\d+)/\d+\+(-?\d+)\+(-?\d+)\s+(\S+)$", line.strip())
                if m:
                    item = {"x": int(m.group(3)), "y": int(m.group(4)), "w": int(m.group(1)), "h": int(m.group(2)), "name": m.group(5)}
                    (out.insert(0, item) if "*" in line else out.append(item))
    except Exception:
        out = []
    if not out:
        try:
            r = tk._default_root
            out = [{"x": 0, "y": 0, "w": r.winfo_screenwidth(), "h": r.winfo_screenheight(), "name": "Ekran główny"}]
        except Exception:
            out = [{"x": 0, "y": 0, "w": 1920, "h": 1080, "name": "Ekran główny"}]
    return out


def _auto_zoom(screen: dict) -> int:
    """Skalowanie wg ekranu: MacBook (węższy niż 1920 punktów, np. 1512×982) – 50%, od 1920×1080 – 67%."""
    return 50 if screen["w"] < 1900 else 67


def _window_slot(layout: dict, index: int) -> "dict | None":
    """Okno sesji nr index (kolejność w grupie): kolumny od lewej, wiersze od góry; po zapełnieniu siatki – od nowa."""
    if not layout or not layout.get("enabled"):
        return None
    scr = _screens()
    sc = scr[min(max(int(layout.get("screen", 0)), 0), len(scr) - 1)]
    cols = max(1, int(layout.get("cols", 5)))
    rows = max(1, int(layout.get("rows", 2)))
    i = index % (cols * rows)
    w, h = sc["w"] // cols, sc["h"] // rows
    z = layout.get("zoom", "auto")
    zoom = _auto_zoom(sc) if z == "auto" else int(z)
    return {"x": sc["x"] + (i % cols) * w, "y": sc["y"] + (i // cols) * h, "w": w, "h": h, "zoom": zoom,
            "slot": i + 1, "screen": sc["name"]}


ZOOM_HOSTS = ["margonem.pl", "www.margonem.pl", "gordion.margonem.pl", "luvia.margonem.pl"]


def _apply_profile_zoom(profile_path: str, zoom: int, extra_hosts: tuple = ()) -> None:
    """Zoom przeglądarki w profilu (jak Ctrl −) – zapis do Default/Preferences przed startem przeglądarki.
    Chrome/Brave zapamiętują powiększenie osobno dla każdej domeny (per_host_zoom_levels) i ono wygrywa z domyślnym,
    więc ustawiamy je wprost dla domen margonem.pl, a do tego domyślny poziom. Poziom = log(zoom) / log(1.2)."""
    import math
    pref_dir = os.path.join(profile_path, "Default")
    os.makedirs(pref_dir, exist_ok=True)
    path = os.path.join(pref_dir, "Preferences")
    try:
        with open(path, "r", encoding="utf-8") as f:
            prefs = json.load(f)
    except Exception:
        prefs = {}
    level = 0.0 if zoom == 100 else math.log(zoom / 100) / math.log(1.2)
    part = prefs.setdefault("partition", {})
    part.setdefault("default_zoom_level", {})["x"] = level
    per_host = part.setdefault("per_host_zoom_levels", {})
    if not isinstance(per_host, dict):
        per_host = part["per_host_zoom_levels"] = {}
    stamp = str(int((time.time() + 11644473600) * 1_000_000))   # czas Chrome (µs od 1601)
    for key in set(per_host) | {"x"}:
        hosts = per_host.setdefault(key, {})
        if not isinstance(hosts, dict):
            continue
        for host in set(ZOOM_HOSTS) | {h for h in hosts if "margonem" in h} | set(extra_hosts):
            hosts[host] = {"last_modified": stamp, "zoom_level": level}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(prefs, f)


# undetected_chromedriver dopisuje na sztywno --window-size=1920,1080 i --start-maximized – przy układzie okien grupy
# każde okno startowałoby zmaksymalizowane na głównym ekranie. Takie opcje pomijają te dwa argumenty.
_UC_FORCED_WINDOW_ARGS = ("--window-size=1920,1080", "--start-maximized")


def _keep_window_args(o):
    orig = o.add_argument
    def add_argument(arg):
        if arg in _UC_FORCED_WINDOW_ARGS:
            return
        return orig(arg)
    o.add_argument = add_argument
    o._kraken_keep_window = True
    return o


def _clone_uc_options(o):
    """Kopia ChromeOptions (undetected_chromedriver nie pozwala użyć tego samego obiektu drugi raz)."""
    import undetected_chromedriver as uc
    n = uc.ChromeOptions()
    if getattr(o, "_kraken_keep_window", False):
        _keep_window_args(n)
    for a in o.arguments:
        n.add_argument(a)
    for k, v in (o.experimental_options or {}).items():
        n.add_experimental_option(k, v)
    if o.binary_location:
        n.binary_location = o.binary_location
    n.page_load_strategy = o.page_load_strategy
    return n


def _start_uc(options, browser: str, log=None):
    """uc.Chrome z wersją ChromeDrivera = wersja przeglądarki. Gdy mimo to ChromeDriver zgłosi
    „Current browser version is X” (np. przeglądarka zaktualizowała się w tle), ponawia z wersją X."""
    import undetected_chromedriver as uc
    version = _detect_browser_major_version(browser) or BROWSER_VERSION.get(browser, 148)
    backup = _clone_uc_options(options)
    try:
        return uc.Chrome(options=options, version_main=version, driver_executable_path=None)
    except Exception as e:
        m = re.search(r"[Cc]urrent browser version is (\d+)", str(e))
        if not m or int(m.group(1)) == version:
            raise
        real = int(m.group(1))
        _DETECTED_BROWSER_VERSION_CACHE[browser] = real
        if log:
            log(f"🔁 ChromeDriver {version} ≠ przeglądarka {real} – pobieram ChromeDriver {real}")
        return uc.Chrome(options=backup, version_main=real, driver_executable_path=None)


def _get_templates_dir(browser: str = "Chrome") -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "profiles", "templates", browser.lower())
    os.makedirs(d, exist_ok=True)
    return d

def _list_templates(browser: str = "Chrome") -> list:
    """Zwraca listę nazw szablonów profili dla danej przeglądarki."""
    d = _get_templates_dir(browser)
    return sorted([
        name for name in os.listdir(d)
        if os.path.isdir(os.path.join(d, name))
    ])

def _list_all_templates() -> list:
    """Zwraca listę (browser, name) dla wszystkich przeglądarek."""
    result = []
    for b in BROWSERS:
        for name in _list_templates(b):
            result.append((b, name))
    return result

def _get_group_profile_path(group: str, profile_name: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "profiles", "groups", _safe_group(group), profile_name)
    return d


# ============================================
# LOGGER
# ============================================
class SessionLogger:
    _LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

    def __init__(self, text_widget: tk.Text, profile_name: str = "session"):
        self.widget       = text_widget
        self._profile     = profile_name
        self._file        = None
        self._ship        = None    # (świat, postać) – wysyłka na serwer Kraken API (log_shipper)
        self._open_file()

    def ship_to(self, char: str, world: str):
        """Od teraz linie tej sesji idą też na serwer logów (gdy skonfigurowany w api.json)."""
        self._ship = (str(world or "").lower(), char)

    def _open_file(self):
        try:
            os.makedirs(self._LOGS_DIR, exist_ok=True)
            safe = re.sub(r'[\\/:*?"<>|]', '_', self._profile)
            path = os.path.join(self._LOGS_DIR, f"{safe}.log")
            self._file = open(path, "a", encoding="utf-8", buffering=1)
        except Exception:
            self._file = None

    def set_profile(self, profile_name: str):
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
        self._profile = profile_name
        self._open_file()

    def write(self, msg: str):
        if not msg.strip():
            return
        ts   = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        if not line.endswith("\n"):
            line += "\n"
        if self._file:
            try:
                self._file.write(line)
            except Exception:
                pass
        if self._ship:
            try:
                from log_shipper import SHIPPER
                SHIPPER.add(self._ship[0], self._ship[1], f"[launcher] {line.strip()}")
            except Exception:
                pass
        self.widget.after(0, self._append, line)

    def _append(self, line: str):
        self.widget.configure(state="normal")
        self.widget.insert(tk.END, line)
        self.widget.see(tk.END)
        self.widget.configure(state="disabled")

    def flush(self):
        if self._file:
            try:
                self._file.flush()
            except Exception:
                pass

    def close(self):
        if self._file:
            try:
                self._file.close()
            except Exception:
                pass
            self._file = None


# ============================================
# BOT RUNNER
# ============================================
def _write_config(path: str, data: dict) -> None:
    """Zapis configu od razu na dysk (plik tymczasowy + podmiana – bez pustego/uciętego pliku przy przerwaniu)."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# Profesje postaci (zapis w configu: "prof"); '' = wybór w panelu bota.
PROFESSIONS = [("", "(wybór w bocie)"), ("w", "wojownik"), ("p", "paladyn"), ("b", "tancerz ostrzy"),
               ("h", "łowca"), ("t", "tropiciel"), ("m", "mag")]
PROF_LABEL = dict(PROFESSIONS)
PROF_RANDOM = "random"            # harmonogram: profesja losowana przy tworzeniu każdej nowej sesji
PROF_RANDOM_LABEL = "🎲 losowa"


def config_prof(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return str(json.load(f).get("prof", "") or "")
    except Exception:
        return ""


def set_config_prof(path: str, prof: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if prof:
        data["prof"] = prof
    else:
        data.pop("prof", None)
    _write_config(path, data)


BANNED_SUFFIX = " (zablokowane)"   # dopisek przy nazwie configu zablokowanego konta (lista configów)


def config_banned(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return bool(json.load(f).get("banned"))
    except Exception:
        return False


def mark_config_banned(path: str) -> None:
    """Konto zablokowane na margonem.pl → "banned": true w configu (START takiego configu jest odrzucany)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["banned"] = True
    data["banned_at"] = time.strftime("%Y-%m-%d %H:%M")
    _write_config(path, data)


def _config_dir() -> str:
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    os.makedirs(d, exist_ok=True)
    return d


def _free_config_name(stem: str) -> str:
    stem = re.sub(r"[^\w\-]+", "_", stem or "", flags=re.UNICODE).strip("_") or "konto"
    name, i = f"{stem}.json", 2
    while os.path.exists(os.path.join(_config_dir(), name)):
        name, i = f"{stem}_{i}.json", i + 1
    return name


def create_auto_config(prof: str = ""):
    """Nowe konto: plik configu z wygenerowanym loginem, hasłem i nickiem ("provisioned": false) – konto i postać
    zakłada START sesji. Zwraca (nazwa pliku, ścieżka, dane)."""
    from create_account import generate_login, generate_password, generate_nick
    nick = generate_nick()
    name = _free_config_name(nick)
    path = os.path.join(_config_dir(), name)
    data = {"login": [{"username": generate_login(), "password": generate_password()}], "nick": nick, "provisioned": False}
    if prof in PROF_LABEL and prof:
        data["prof"] = prof
    _write_config(path, data)
    return name, path, data


def create_manual_config(name: str, login: str, password: str, prof: str = ""):
    """Config istniejącego konta (login i hasło podane). Zwraca (nazwa pliku, ścieżka)."""
    fname = _free_config_name(name or login)
    path = os.path.join(_config_dir(), fname)
    data = {"login": [{"username": login.strip(), "password": password}]}
    if prof in PROF_LABEL and prof:
        data["prof"] = prof
    _write_config(path, data)
    return fname, path


class BotRunner:
    """Sesja przeglądarki: profil (z szablonu), logowanie na margonem.pl, jednorazowa captcha zaraz po wejściu do gry.
    Całą grą steruje bot Kraken w przeglądarce (Tampermonkey) – tu tylko trzymamy przeglądarkę do STOP."""

    CAPTCHA_WINDOW = 20   # s po wczytaniu gry, w których szukamy captchy (przed startem bota w przeglądarce)

    def __init__(self, config: dict,
                 stop_event: threading.Event,
                 logger: SessionLogger):
        self.config          = config
        self.stop_event      = stop_event
        self.logger          = logger
        self.driver          = None
        self.browser_pid: "int | None" = None
        self._config_lock_path = None
        self.login_done_event  = threading.Event()   # sygnał: logowanie zakończone
        self.bot_state         = ""                  # running / stopped / loading – odczyt z przeglądarki co 5 s
        self.program           = config.get("program", "")
        self.prof              = ""
        self.banned            = False               # konto zablokowane (wykryte przy logowaniu)

    def log(self, msg):
        self.logger.write(msg)

    def stop_check(self):
        if self.stop_event.is_set():
            raise StopIteration("Sesja zatrzymana.")

    def run(self):
        self.crashed = False
        _THREAD_STREAM.set_logger(self.logger)
        from login import AccountBanned
        try:
            self._run_bot()
        except StopIteration as e:
            self.log(f"⛔ {e}")
        except AccountBanned:
            self.banned = True
            self.log("⛔ Konto zostało zablokowane – oznaczam config jako zablokowany i kończę sesję")
            try:
                mark_config_banned(self.config["config_path"])
                self.log(f"💾 Config {os.path.basename(self.config['config_path'])}: zablokowane")
            except Exception as e:
                self.log(f"⚠️  Zapis blokady w configu: {e}")
        except Exception as e:
            self.log(f"❌ Błąd: {e}")
            self.crashed = True
        finally:
            self.login_done_event.set()   # odblokuj strumień nawet przy błędzie przed loginem
            _THREAD_STREAM.clear_logger()
            if self._config_lock_path and os.path.exists(self._config_lock_path):
                try:
                    os.remove(self._config_lock_path)
                    self.log("🔓 Zwolniono lock configa.")
                except Exception:
                    pass
            if self.driver:
                try:
                    self.driver.quit()
                    self.log("🔒 Przeglądarka zamknięta.")
                except Exception:
                    pass

    def _read_bot_state(self) -> str:
        try:
            return self.driver.execute_script(
                "return !window.Kraken || !Kraken.isRunning ? 'loading' : (Kraken.isRunning() ? 'running' : 'stopped');") or ""
        except Exception:
            return ""

    def bot_command(self, action: str, program: str = None, done=None):
        """Bot w działającej sesji (przeglądarka zostaje): start z programem/profesją albo zatrzymanie. W tle."""
        def run():
            ok, msg = False, ""
            try:
                if not self.driver:
                    msg = "sesja nie działa"
                elif action == "bot_stop":
                    if self.driver.execute_script("return !!(window.Kraken && Kraken.isRunning && Kraken.isRunning());"):
                        self.driver.execute_script("Kraken.stop('Zatrzymano z launchera');")
                        self.log("⏸ Bot zatrzymany (sesja działa dalej)")
                        ok, msg = True, "bot zatrzymany"
                    else:
                        ok, msg = True, "bot już stoi"
                else:
                    if program is not None:
                        self.program = program
                    self._prof_done = False
                    self._start_bot(self.program, self.prof)
                    ok = self._read_bot_state() == "running"
                    msg = "bot uruchomiony" if ok else "bot nie wystartował (log sesji)"
            except Exception as e:
                msg = str(e)[:200]
            self.bot_state = self._read_bot_state()
            if done:
                done(ok, msg)
        threading.Thread(target=run, daemon=True).start()

    def _start_bot(self, program: str, prof: str = ""):
        """START sesji = start bota: autoryzacja tokenu na serwerze (gdy skonfigurowany), program grupy/sesji, start."""
        from log_shipper import SHIPPER, check
        if SHIPPER.enabled:
            res = check(SHIPPER.url, SHIPPER.token)
            if not res.startswith("✅"):
                self.log(f"⛔ Autoryzacja na serwerze nieudana ({res}) – bot nie wystartuje (⚙️ Ustawienia launchera)")
                return
            self.log(f"🔐 Serwer: {res[2:].strip()}")
        js_ready = "return !!(window.Kraken && Kraken.setProgram && Kraken.getConfig && Object.keys(Kraken.getConfig()).length);"
        t0 = time.time()
        while time.time() - t0 < 180 and not self.stop_event.is_set():
            try:
                if not self.driver.execute_script(js_ready):
                    time.sleep(2)
                    continue
                if prof and not getattr(self, "_prof_done", False):
                    rp = self.driver.execute_script("return Kraken.setProf ? Kraken.setProf(arguments[0]) : null;", prof) or {}
                    self._prof_done = True
                    if rp.get("locked"):
                        self.log(f"🎓 Profesja z gry: {PROF_LABEL.get(rp.get('prof'), rp.get('prof'))} (config: {PROF_LABEL.get(prof, prof)})")
                    elif rp.get("ok"):
                        self.log(f"🎓 Profesja: {PROF_LABEL.get(prof, prof)}")
                if program:
                    r = self.driver.execute_script("return Kraken.setProgram(arguments[0]);", program) or {}
                    if not r.get("ok"):
                        # program jeszcze nie pobrany z repo (nowa postać) – czekamy
                        if time.time() - t0 > 170:
                            self.log(f"⚠️  Program „{program}”: {r.get('error', '?')} – startuję z programem z bota")
                        else:
                            time.sleep(3)
                            continue
                    elif r.get("changed"):
                        self.log(f"📋 Program bota: „{program}”")
                        for _ in range(60):          # bot zatrzymuje poprzedni program
                            if not self.driver.execute_script("return Kraken.isRunning();"):
                                break
                            time.sleep(1)
                if self.driver.execute_script("return Kraken.isRunning();"):
                    self.log("▶ Bot już pracuje")
                else:
                    self.driver.execute_script("Kraken.start();")
                    self.log("▶ Bot uruchomiony")
                return
            except Exception:
                time.sleep(2)
        self.log("⚠️  Bot nie odpowiedział w 3 min – nie uruchomiono")

    def _push_api_to_bot(self):
        """Adres i token serwera z Ustawień launchera → bot Kraken w tej przeglądarce (Ustawienia › Serwer)."""
        from log_shipper import SHIPPER
        if not SHIPPER.enabled:
            return
        t0 = time.time()
        while time.time() - t0 < 60 and not self.stop_event.is_set():
            try:
                ok = self.driver.execute_script(
                    "if (!window.Kraken || !Kraken.setApi) return false; Kraken.setApi(arguments[0], arguments[1]); return true;",
                    SHIPPER.url, SHIPPER.token)
                if ok:
                    self.log("📡 Bot: adres i token serwera ustawione")
                    return
            except Exception:
                pass
            time.sleep(2)
        self.log("⚠️  Bot nie wystartował w 60 s – adres i token serwera nieprzekazane")

    _JS_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')

    def _ship_browser_logs(self, shipper, char: str, world: str):
        """Linie bota Kraken z konsoli przeglądarki („[Kraken] [godz][postać]…”) → serwer logów."""
        try:
            entries = self.driver.get_log("browser")
            # Bot z tokenem w Ustawieniach › Serwer wysyła logi sam – launcher ich nie dubluje.
            if self.driver.execute_script("return !!(window.Kraken && Kraken.apiLinked && Kraken.apiLinked())"):
                return
        except Exception:
            return
        for e in entries:
            msg = str(e.get("message", ""))
            if "[Kraken]" not in msg:
                continue
            parts = []
            for m in self._JS_STR.finditer(msg):
                try:
                    parts.append(json.loads(f'"{m.group(1)}"'))
                except ValueError:
                    parts.append(m.group(1))
            text = " ".join(parts) if parts else msg
            text = text.split("[Kraken]", 1)[-1].strip()
            if text:
                shipper.add(str(world or "").lower(), char, text)

    def _browser_alive(self) -> bool:
        try:
            _ = self.driver.window_handles
            return True
        except Exception:
            return False

    def _captcha_once(self, check_and_solve_captcha, By):
        """Captcha zaraz po wejściu do gry (zanim ruszy bot w przeglądarce) – jedno rozwiązanie i koniec."""
        t0 = time.time()
        while time.time() - t0 < self.CAPTCHA_WINDOW:
            self.stop_check()
            try:
                present = bool(self.driver.find_elements(By.CSS_SELECTOR, ".captcha__buttons")) or bool(
                    self.driver.find_elements(By.XPATH, "//div[@class='label' and text()='Rozwiąż teraz']"))
            except Exception:
                present = False
            if present:
                self.log("🔐 Captcha po wejściu do gry – rozwiązuję")
                ok = check_and_solve_captcha(self.driver)
                self.log("✅ Captcha rozwiązana" if ok else "⚠️  Captcha: nie udało się rozwiązać")
                return
            time.sleep(0.5)

    def _provision(self, data: dict, path: str, server: str, login_fn):
        """Zakłada konto (gdy jeszcze nie: "registered") i postać na wybranym świecie; po każdym etapie zapis configu."""
        from selenium.webdriver.common.by import By
        from create_account import step_register, step_create_character
        cred = data["login"][0]
        nick = data.get("nick") or cred["username"]
        if not data.get("registered"):
            self.log(f"🆕 Rejestruję konto {cred['username']} (nick postaci: {nick})")
            self.driver.get("https://www.margonem.pl/intro/")
            step_register(self.driver, self.log, cred["username"], cred["password"])
            data["registered"] = True
            _write_config(path, data)
            self.log("💾 Config: konto zarejestrowane")
        else:
            self.log("🔑 Konto już zarejestrowane – loguję i zakładam postać")
            self.driver.get("https://margonem.pl")
            time.sleep(3)
            if self.driver.find_elements(By.ID, "login-input"):
                login_fn(driver=self.driver, username=cred["username"], password=cred["password"])
        self.stop_check()
        # Formularz postaci: po rejestracji pojawia się sam; przy istniejącej postaci go nie ma – konto gotowe.
        t0 = time.time()
        while time.time() - t0 < 45 and not self.driver.find_elements(By.ID, "add-character-form"):
            self.stop_check()
            if self.driver.find_elements(By.ID, "chnick") or self.driver.find_elements(By.CSS_SELECTOR, "div.c-btn.enter-game"):
                break
            time.sleep(0.5)
        if self.driver.find_elements(By.ID, "add-character-form"):
            step_create_character(self.driver, self.log, nick, server=(server or "gordion").lower())
            time.sleep(4)
        else:
            self.log("ℹ️  Brak formularza postaci – konto ma już postać")
        data["provisioned"] = True
        _write_config(path, data)
        self.log(f"💾 Config: konto i postać gotowe ({nick} @ {server})")

    def _run_bot(self):
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from login import login, is_banned, AccountBanned
        from create_profile import create_profile
        from captcha import check_and_solve_captcha

        cfg              = self.config
        config_path      = cfg["config_path"]

        base_dir      = os.path.dirname(os.path.abspath(__file__))
        browser       = cfg.get("browser", "Chrome")
        group         = cfg.get("group", "default")
        recreate      = cfg.get("recreate", False)
        config_name   = os.path.splitext(os.path.basename(config_path))[0]
        _cfg_lock = os.path.join(os.path.dirname(config_path), f"{config_name}.lock")
        self._config_lock_path = _cfg_lock
        try:
            with open(_cfg_lock, "w") as _lf:
                _lf.write(str(os.getpid()))
            self.log(f"🔒 Config lock: {config_name}")
        except Exception as _le:
            self.log(f"⚠️  Nie można utworzyć config lock: {_le}")

        profile_name  = f"{browser.lower()}_{config_name}"
        profile_path  = _get_group_profile_path(group, profile_name)
        self.logger.set_profile(profile_name)
        self.logger.ship_to(config_name, cfg.get("server", ""))

        profile_existed = os.path.exists(profile_path)  # przed create/delete

        if recreate and profile_existed:
            self.log(f"🗑️  Recreate: usuwam profil {profile_name}")
            shutil.rmtree(profile_path, ignore_errors=True)
            profile_existed = False

        template_name = cfg.get("template")
        if not os.path.exists(profile_path):
            self.log(f"📋 Tworzę profil{'  z szablonu: ' + template_name if template_name else ': ' + profile_name}")
            create_profile(profile_name, template_name, browser=browser, group=group)
            self.log(f"✅ Profil: {profile_name}")
        else:
            self.log(f"♻️  Używam istniejącego profilu: {profile_name}")

        win = cfg.get("window")
        options = uc.ChromeOptions()
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir={profile_path}")
        if win:
            # Okno aplikacji (bez kart i paska adresu): zwykłe okno Chrome nie zejdzie poniżej ~500 px szerokości,
            # a w siatce 5×2 na MacBooku komórka ma ~300 px.
            _keep_window_args(options)
            srv_host = (SERVER_URL.get(cfg.get("server", ""), "") or "").replace("https://", "").strip("/")
            _apply_profile_zoom(profile_path, win["zoom"], (srv_host,) if srv_host else ())
            options.add_argument("--app=https://margonem.pl")
            options.add_argument(f"--window-position={win['x']},{win['y']}")
            options.add_argument(f"--window-size={win['w']},{win['h']}")
            self.log(f"🪟 Okno {win['slot']}: {win['w']}×{win['h']} na ({win['x']},{win['y']}), {win['screen']}, zoom {win['zoom']}%")
        else:
            self.log("🪟 Układ okien grupy wyłączony – okno zmaksymalizowane (prawy klik na grupie → Układ okien…)")
            options.add_argument("--start-maximized")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        })
        options.add_argument("--disable-save-password-bubble")
        # Konsola przeglądarki (logi bota Kraken) czytana przez launcher i wysyłana na serwer logów.
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        # "none": driver.get() wraca natychmiast, ChromeDriver nie blokuje
        # find_element z powodu trwającej nawigacji
        options.page_load_strategy = "none"
        if _browser_binary(browser):
            options.binary_location = _browser_binary(browser)

        server     = cfg.get("server", "")
        server_url = SERVER_URL.get(server, "")

        self.driver = _start_uc(options, browser, self.log)
        if win:
            try:
                self.driver.set_window_rect(win["x"], win["y"], win["w"], win["h"])
            except Exception as e:
                self.log(f"⚠️  Ustawienie okna: {e}")
        try:
            self.browser_pid = self.driver.service.process.pid
            self.log(f"🔢 PID: {self.browser_pid}")
        except Exception:
            self.browser_pid = None

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        credentials = config_data["login"][0]

        self.stop_check()

        # Nowe konto z ＋ ("provisioned": false): rejestracja i postać w tej przeglądarce, stan zapisywany od razu.
        if config_data.get("provisioned") is False:
            self._provision(config_data, config_path, server, login)

        # Zawsze najpierw margonem.pl: zalogowane konto (wybór postaci / „Wejdź do gry”, bez formularza) – od razu
        # {server}.margonem.pl; niezalogowane – zwykłe logowanie, a potem też na wybrany serwer.
        self.log("🌐 Wchodzę na margonem.pl – sprawdzam, czy konto jest zalogowane")
        self.driver.get("https://margonem.pl")

        def _first(checks, timeout):
            t0 = time.time()
            while time.time() - t0 < timeout:
                self.stop_check()
                if is_banned(self.driver):
                    raise AccountBanned("Konto zostało zablokowane")
                for name, sel in checks:
                    try:
                        if self.driver.find_elements(*sel):
                            return name
                    except Exception:
                        pass
                time.sleep(0.3)
            return None

        def _on_server():
            try:
                return bool(server_url) and self.driver.current_url.startswith(server_url)
            except Exception:
                return False

        def _go_server():
            self.log(f"⚡ Przechodzę na {server_url}")
            self.driver.get(server_url)
            if _first([("canvas", (By.CSS_SELECTOR, "canvas#GAME_CANVAS"))], 60):
                self.log("✅ Gra załadowana")
                return True
            return False

        state = _first([
            ("form",   (By.ID, "login-input")),
            ("link",   (By.LINK_TEXT, "Zaloguj się na Stronie Głównej")),
            ("logged", (By.ID, "chnick")),
            ("logged", (By.CSS_SELECTOR, "div.c-btn.enter-game")),
        ], 45)
        entered = False
        if state == "logged" and server_url:
            self.log("✅ Konto zalogowane")
            entered = _go_server()
            if not entered:
                self.log("⚠️  Serwer się nie wczytał – loguję od nowa")
                self.driver.get("https://margonem.pl")
        if not entered:
            if state != "logged":
                self.log("🔑 Konto niezalogowane – loguję")
            login(driver=self.driver,
                  username=credentials["username"],
                  password=credentials["password"])
            # „Wejdź do gry” prowadzi na świat ostatniej postaci – gdy to inny serwer, przechodzimy na wybrany.
            if server_url and not _on_server():
                _go_server()

        self.login_done_event.set()   # sygnał dla stream_worker: logowanie skończone
        self._captcha_once(check_and_solve_captcha, By)
        self._push_api_to_bot()
        self.prof = str(config_data.get("prof", "") or "")
        self._start_bot(cfg.get("program", ""), self.prof)
        self.log("✅ Zalogowano – grą steruje bot Kraken w przeglądarce. STOP zamyka przeglądarkę.")
        from log_shipper import SHIPPER
        if SHIPPER.enabled:
            self.log(f"📡 Logi postaci → {SHIPPER.url}")
        last_pull = 0.0
        last_state = 0.0
        while not self.stop_event.is_set():
            if not self._browser_alive():
                self.log("🔒 Przeglądarka została zamknięta.")
                self.driver = None
                return
            if time.time() - last_state > 5:
                last_state = time.time()
                self.bot_state = self._read_bot_state()
            if SHIPPER.enabled and time.time() - last_pull > 5:
                last_pull = time.time()
                self._ship_browser_logs(SHIPPER, config_name, cfg.get("server", ""))
            time.sleep(1)
        raise StopIteration("Sesja zatrzymana.")

# ============================================
# MODEL GRUP
# ============================================
class GroupManager:
    """
    Przechowuje grupy i przypisania sesji.
    Klucz wewnętrzny: (world, name) — nazwy grup są unikalne w obrębie świata.
    """
    def __init__(self):
        # {(world, name): {"color": hex, "sessions": [session_id, ...]}}
        self._groups: dict[tuple, dict] = {}
        self._callbacks: list = []
        self._favorites: set[tuple] = set()   # {(world, name)}

    # ---- zarządzanie grupami ----
    def _add_group(self, name: str, color: str, world: str = "Gordion"):
        key = (world, name)
        self._groups[key] = {"color": color, "sessions": [], "layout": dict(LAYOUT_DEFAULT), "program": ""}
        self._notify()

    def add_group(self, name: str, world: str = "Gordion") -> bool:
        name = name.strip()
        if not name or (world, name) in self._groups:
            return False
        color = GROUP_PALETTE[len(self._groups) % len(GROUP_PALETTE)]
        self._add_group(name, color, world)
        return True

    def remove_group(self, name: str, world: str) -> bool:
        key = (world, name)
        if key not in self._groups:
            return False
        other = next((k for k in self._groups if k != key and k[0] == world), None)
        for sid in list(self._groups[key]["sessions"]):
            if other:
                self._groups[other]["sessions"].append(sid)
        self._favorites.discard(key)
        del self._groups[key]
        self._notify()
        return True

    def rename_group(self, old: str, new: str, world: str) -> bool:
        new = new.strip()
        old_key = (world, old)
        new_key = (world, new)
        if not new or new_key in self._groups or old_key not in self._groups:
            return False
        data = self._groups.pop(old_key)
        self._groups[new_key] = data
        if old_key in self._favorites:
            self._favorites.discard(old_key)
            self._favorites.add(new_key)
        self._notify()
        return True

    # ---- przypisanie sesji ----
    def assign(self, session_id: int, group_name: str, world: str = "Gordion"):
        """Przypisz sesję do grupy (usuwa z poprzedniej)."""
        for g in self._groups.values():
            if session_id in g["sessions"]:
                g["sessions"].remove(session_id)
        key = (world, group_name)
        if key in self._groups:
            self._groups[key]["sessions"].append(session_id)
        self._notify()

    def remove_session(self, session_id: int):
        for g in self._groups.values():
            if session_id in g["sessions"]:
                g["sessions"].remove(session_id)
        self._notify()

    # ---- odczyt ----
    def groups_in_world(self, world: str) -> dict:
        """Zwraca {name: data} dla danego świata."""
        return {n: d for (w, n), d in self._groups.items() if w == world}

    def group_names(self, world: str = None) -> list:
        if world is None:
            return [n for (w, n) in self._groups]
        return [n for (w, n) in self._groups if w == world]

    def color_of(self, name: str, world: str = "Gordion") -> str:
        return self._groups.get((world, name), {}).get("color", FG_DIM)

    def sessions_in(self, name: str, world: str = "Gordion") -> list:
        return list(self._groups.get((world, name), {}).get("sessions", []))

    def first_group(self, world: str = "Gordion") -> str:
        """Zwraca nazwę pierwszej grupy w świecie lub '' jeśli brak."""
        return next((n for (w, n) in self._groups if w == world), "")

    def group_of(self, session_id: int) -> str:
        """Zwraca nazwę grupy sesji (bez świata)."""
        for (w, n), data in self._groups.items():
            if session_id in data["sessions"]:
                return n
        return ""

    def world_of_session(self, session_id: int) -> str:
        """Zwraca świat grupy sesji."""
        for (w, n), data in self._groups.items():
            if session_id in data["sessions"]:
                return w
        return WORLDS[0]

    def toggle_favorite(self, name: str, world: str = "Gordion"):
        key = (world, name)
        if key in self._favorites:
            self._favorites.discard(key)
        else:
            self._favorites.add(key)
        self._notify()

    def is_favorite(self, name: str, world: str = "Gordion") -> bool:
        return (world, name) in self._favorites

    def layout_of(self, name: str, world: str = "Gordion") -> dict:
        return dict(LAYOUT_DEFAULT, **(self._groups.get((world, name), {}).get("layout") or {}))

    def set_layout(self, name: str, world: str, layout: dict):
        if (world, name) in self._groups:
            self._groups[(world, name)]["layout"] = dict(LAYOUT_DEFAULT, **layout)
            self._notify()

    def program_of(self, name: str, world: str = "Gordion") -> str:
        """Program bota ustawiany każdej sesji grupy ('' = bez zmiany – bot zostaje przy swoim)."""
        return self._groups.get((world, name), {}).get("program", "") or ""

    def set_program(self, name: str, world: str, program: str):
        if (world, name) in self._groups:
            self._groups[(world, name)]["program"] = program or ""
            self._notify()

    def slot_of(self, session_id: int) -> int:
        """Miejsce sesji w kolejności jej grupy (0 = pierwsza)."""
        for data in self._groups.values():
            if session_id in data["sessions"]:
                return data["sessions"].index(session_id)
        return 0

    def to_dict(self) -> list:
        return [{"name": n, "world": w, "color": d["color"],
                 "favorite": (w, n) in self._favorites,
                 "layout": d.get("layout") or dict(LAYOUT_DEFAULT),
                 "program": d.get("program", "")}
                for (w, n), d in self._groups.items()]

    # ---- obserwatorzy ----
    def subscribe(self, fn):
        self._callbacks.append(fn)

    def _notify(self):
        for fn in self._callbacks:
            fn()


# ============================================
# PANEL GRUP (lewy sidebar)
# ============================================

# ============================================
# DIALOG: NOWY TEMPLATE PROFILU
# ============================================
class AddTemplateDialog(tk.Toplevel):
    """Tworzy nowy pusty profil Chrome jako szablon."""

    def __init__(self, parent, on_created=None):
        super().__init__(parent)
        self.on_created = on_created
        self.title("Nowy template profilu")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self._build()
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"340x230+{px-170}+{py-115}")
        self.name_entry.focus_set()

    def _build(self):
        tk.Label(self, text="Nowy template profilu", font=FONT_BOLD,
                 bg=BG, fg=ACCENT).pack(pady=(18, 4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 14))

        form = tk.Frame(self, bg=BG)
        form.pack(fill="x", padx=24)

        tk.Label(form, text="Przeglądarka:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM, anchor="w").pack(fill="x", pady=(0, 2))
        self.browser_var = tk.StringVar(value=BROWSERS[0])
        ttk.Combobox(form, textvariable=self.browser_var,
                     font=FONT_SMALL, state="readonly",
                     values=BROWSERS).pack(fill="x", pady=(0, 8))

        tk.Label(form, text="Nazwa szablonu:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM, anchor="w").pack(fill="x", pady=(0, 2))
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(form, textvariable=self.name_var,
                                    font=FONT_SMALL, bg=BG3, fg=FG,
                                    insertbackground=FG, relief="flat")
        self.name_entry.pack(fill="x", ipady=5)

        self.error_lbl = tk.Label(self, text="", font=FONT_SMALL, bg=BG, fg=RED)
        self.error_lbl.pack(pady=(8, 0))

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=(8, 18))
        tk.Button(btn_row, text="Anuluj", command=self.destroy,
                  bg=BG3, fg=FG_DIM, relief="flat", cursor="hand2",
                  font=FONT_SMALL, padx=14, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="✅ Utwórz", command=self._create,
                  bg=GREEN, fg="#000", relief="flat", cursor="hand2",
                  font=FONT_BOLD, padx=14, pady=5).pack(side="left")

        self.bind("<Return>", lambda e: self._create())
        self.bind("<Escape>", lambda e: self.destroy())

    def _create(self):
        name = self.name_var.get().strip()
        if not name:
            self.error_lbl.configure(text="⚠️  Podaj nazwę szablonu!")
            return
        safe = "".join(c for c in name if c.isalnum() or c in "-_")
        if not safe:
            self.error_lbl.configure(text="⚠️  Niedozwolone znaki!")
            return

        browser = self.browser_var.get()
        tpl_path = os.path.join(_get_templates_dir(browser), safe)
        if os.path.exists(tpl_path):
            self.error_lbl.configure(text=f"⚠️  Szablon '{safe}' już istnieje!")
            return

        try:
            default_dir = os.path.join(tpl_path, "Default")
            os.makedirs(default_dir, exist_ok=True)
            prefs_path = os.path.join(default_dir, "Preferences")
            with open(prefs_path, "w") as f:
                json.dump({}, f)
        except Exception as e:
            self.error_lbl.configure(text=f"❌ Błąd: {e}")
            return

        if self.on_created:
            self.on_created(safe)
        self.destroy()


class CreateAccountDialog(tk.Toplevel):
    """
    Dialog automatycznej rejestracji konta Margonem:
    otwiera Brave z wybranym templatem, rejestruje konto,
    tworzy postać, przechodzi tutorial i zapisuje config.
    """

    def __init__(self, parent, on_created=None, browser: str = None, template: str = None,
                 server: str = None, auto_start: bool = False):
        super().__init__(parent)
        self.on_created = on_created   # callback(filename, path)
        self._stop      = threading.Event()
        self._driver    = None
        self._preset    = {"browser": browser, "template": template, "server": server}
        self._auto      = auto_start

        self.title("Nowe konto — Kraken")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()
        self.transient(parent)
        self._build()
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"560x480+{px-280}+{py-240}")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Ustawienia z sesji (przycisk ＋ przy configu) i start bez pytań: login, hasło, nick i plik – generowane.
        p = self._preset
        if p["browser"] in BROWSERS:
            self.browser_var.set(p["browser"])
            self._refresh_tpl_cb()
        if p["template"] and p["template"] in (self.tpl_cb["values"] or ()):
            self.tpl_var.set(p["template"])
        if p["server"] in SERVERS:
            self.server_var.set(p["server"])
        if self._auto:
            self.after(400, self._on_start)

    def _build(self):
        tk.Label(self, text="Nowe konto Margonem (Kraken)", font=FONT_BOLD,
                 bg=BG, fg=ACCENT).pack(pady=(14, 4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 8))

        form = tk.Frame(self, bg=BG)
        form.pack(fill="x", padx=20)

        def _row(label_text):
            r = tk.Frame(form, bg=BG)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label_text, width=14, anchor="w",
                     font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left")
            return r

        # Przeglądarka
        r1 = _row("Przeglądarka:")
        self.browser_var = tk.StringVar(value="Brave")
        browser_cb = ttk.Combobox(r1, textvariable=self.browser_var,
                                   font=FONT_SMALL, state="readonly", width=12)
        browser_cb["values"] = BROWSERS
        browser_cb.pack(side="left")
        browser_cb.bind("<<ComboboxSelected>>", self._refresh_tpl_cb)

        # Template
        r2 = _row("Template:")
        self.tpl_var = tk.StringVar()
        self.tpl_cb  = ttk.Combobox(r2, textvariable=self.tpl_var,
                                     font=FONT_SMALL, state="readonly", width=20)
        self.tpl_cb.pack(side="left")
        self._refresh_tpl_cb()

        # Serwer
        r3 = _row("Serwer:")
        self.server_var = tk.StringVar(value=SERVERS[0])
        srv_cb = ttk.Combobox(r3, textvariable=self.server_var,
                               font=FONT_SMALL, state="readonly", width=12)
        srv_cb["values"] = SERVERS
        srv_cb.pack(side="left")

        # Nazwa własna (opcjonalna)
        r4 = _row("Nazwa (opcjon.):")
        self.custom_name_var = tk.StringVar()
        name_entry = tk.Entry(r4, textvariable=self.custom_name_var,
                              font=FONT_SMALL, bg=BG3, fg=FG,
                              insertbackground=FG, relief="flat", width=22)
        name_entry.pack(side="left")
        tk.Label(r4, text="  (zostawi puste = nick postaci)",
                 font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left")

        # Przyciski
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(8, 4))
        self.start_btn = tk.Button(btn_row, text="▶ Start", command=self._on_start,
                                    bg=GREEN, fg="#000", font=FONT_BOLD,
                                    relief="flat", cursor="hand2", padx=12, pady=4)
        self.start_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = tk.Button(btn_row, text="⏹ Stop", command=self._on_stop,
                                   bg=RED, fg="#fff", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", padx=12, pady=4,
                                   state="disabled")
        self.stop_btn.pack(side="left")
        self.status_lbl = tk.Label(btn_row, text="", font=FONT_SMALL, bg=BG, fg=FG_DIM)
        self.status_lbl.pack(side="left", padx=(10, 0))

        # Log
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(4, 0))
        self.log_txt = tk.Text(self, font=FONT_MONO, bg="#0b0d14", fg="#94a3b8",
                                relief="flat", bd=0, wrap="word", state="disabled")
        self.log_txt.pack(fill="both", expand=True, padx=16, pady=(4, 12))

    def _refresh_tpl_cb(self, _=None):
        browser = self.browser_var.get()
        templates = _list_templates(browser)
        self.tpl_cb["values"] = templates
        self.tpl_var.set(templates[0] if templates else "")

    def _log(self, msg: str):
        self.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        self.log_txt.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_txt.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_txt.see(tk.END)
        self.log_txt.configure(state="disabled")

    def _on_start(self):
        tpl = self.tpl_var.get()
        if not tpl:
            self._log("⚠️  Wybierz template!")
            return
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_lbl.configure(text="⏳ Działa...", fg=ACCENT)
        self._stop.clear()
        threading.Thread(target=self._run, daemon=True).start()

    def _on_stop(self):
        self._stop.set()
        self.after(0, lambda: self.stop_btn.configure(state="disabled"))
        self._log("⏹ Zatrzymuję...")
        drv = self._driver
        if drv:
            try:
                drv.quit()
            except Exception:
                pass

    def _on_close(self):
        self._on_stop()
        self.destroy()

    def _run(self):
        import undetected_chromedriver as uc
        from create_account import generate_login, generate_password, run_full
        from create_profile import create_profile

        browser     = self.browser_var.get()
        tpl         = self.tpl_var.get()
        server      = self.server_var.get()
        custom_name = self.custom_name_var.get().strip()[:20]
        login       = generate_login()
        password    = generate_password()
        progress    = {}

        self._log(f"🔑 Generuję dane: {login} / {password}")
        if custom_name:
            self._log(f"🏷️  Nazwa własna: {custom_name}")

        # Utwórz tymczasowy profil z szablonu (nazwa temp_ — przemianowany po uzyskaniu nicka)
        profile_name = f"temp_{login}"
        profile_path = _get_group_profile_path("default", profile_name)
        try:
            create_profile(profile_name, tpl, browser=browser, group="default")
            self._log(f"📁 Profil tymczasowy: {profile_name}")
        except Exception as e:
            self._log(f"❌ Błąd profilu: {e}")
            self.after(0, self._reset_buttons)
            return

        # Otwórz przeglądarkę
        opts = uc.ChromeOptions()
        opts.add_argument("--password-store=basic")
        opts.add_argument("--use-mock-keychain")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(f"--user-data-dir={profile_path}")
        opts.add_argument("--start-maximized")
        opts.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        })
        opts.page_load_strategy = "none"
        if _browser_binary(browser):
            opts.binary_location = _browser_binary(browser)

        try:
            self._driver = _start_uc(opts, browser, self._log)
        except Exception as e:
            self._log(f"❌ Błąd uruchomienia przeglądarki: {e}")
            self.after(0, self._reset_buttons)
            return

        self._log("🌐 Otwieram margonem.pl/intro...")
        self._driver.get("https://www.margonem.pl/intro/")

        server_world = server.lower()   # "gordion"
        nick = ""
        try:
            nick = run_full(
                self._driver, self._log, login, password,
                server=server_world,
                stop_flag=lambda: self._stop.is_set(),
                nick=custom_name if custom_name else None,
                progress=progress,
            )
        except Exception as e:
            self._log(f"❌ Błąd: {e}")
        finally:
            drv = self._driver
            self._driver = None
            if drv:
                try:
                    drv.quit()
                except Exception:
                    pass

        # Konto założone (nawet gdy postać/tutorial się nie udały) – zapisujemy dane logowania, żeby nie przepadły.
        if not nick and progress.get("registered"):
            nick = progress.get("nick") or login
            self._log("⚠️  Proces nie dokończony – zapisuję config z danymi konta")
        if nick and progress.get("registered"):
            # Jeśli użytkownik podał własną nazwę — użyj jej, inaczej nick postaci
            nick_safe = (
                custom_name.replace(" ", "_")
                if custom_name
                else nick.replace(" ", "_")
            )

            # Przemianuj profil tymczasowy
            new_profile_name = f"{browser.lower()}_{nick_safe}"
            new_profile_path = _get_group_profile_path("default", new_profile_name)
            try:
                os.rename(profile_path, new_profile_path)
                self._log(f"📁 Profil: {new_profile_name}")
            except Exception as e:
                self._log(f"⚠️  Rename profilu: {e}")
                nick_safe = login  # fallback na login

            # Zapisz config z wygenerowanymi danymi
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cfg_path = os.path.join(base_dir, "config", f"{nick_safe}.json")
            try:
                os.makedirs(os.path.join(base_dir, "config"), exist_ok=True)
                with open(cfg_path, "w", encoding="utf-8") as _cf:
                    json.dump({"login": [{"username": login, "password": password}]},
                              _cf, indent=2, ensure_ascii=False)
                self._log(f"💾 Config zapisany: {nick_safe}.json")
                self._log(f"═══════════════════════════════════")
                self._log(f"Login:  {login}")
                self._log(f"Hasło:  {password}")
                self._log(f"Nick:   {nick}")
                if custom_name:
                    self._log(f"Nazwa:  {custom_name}")
                self._log(f"═══════════════════════════════════")
                if self.on_created:
                    self.after(0, lambda fn=f"{nick_safe}.json", p=cfg_path:
                               self.on_created(fn, p))
            except Exception as e:
                self._log(f"❌ Błąd zapisu config: {e}")

            self.after(0, lambda: self.status_lbl.configure(text="✅ Gotowe", fg=GREEN))
        else:
            self.after(0, lambda: self.status_lbl.configure(text="⏹ Zatrzymano", fg=FG_DIM))

        self.after(0, self._reset_buttons)

    def _reset_buttons(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")


class GroupPanel(tk.Frame):
    """
    Lewy sidebar: lista grup z kolorowymi kropkami,
    licznikami sesji i przyciskami zarządzania.
    """
    WIDTH = 220

    def __init__(self, parent, group_manager: GroupManager,
                 on_select_group=None, on_add_template=None, get_sessions_fn=None,
                 on_account_created=None, on_world_changed=None):
        super().__init__(parent, bg=BG2, width=self.WIDTH)
        self.pack_propagate(False)
        self.gm                 = group_manager
        self.on_select_group    = on_select_group
        self.on_add_template    = on_add_template
        self._get_sessions_fn   = get_sessions_fn
        self.on_account_created = on_account_created
        self.on_world_changed   = on_world_changed
        self.selected           = None
        self._selected_world    = WORLDS[0]
        self._session_statuses: dict[int, str] = {}

        self._build()
        self.gm.subscribe(self._refresh)

    _FAV_ROW_H   = 28   # przybliżona wysokość wiersza w px
    _FAV_MAX_ROW = 5    # ile wierszy ulubionych widać bez suwaka

    def _build(self):
        # ---- sekcja ŚWIAT ----
        world_hdr = tk.Frame(self, bg=BG2, pady=6)
        world_hdr.pack(fill="x", padx=10)
        tk.Label(world_hdr, text="ŚWIAT", font=(UI_FONT, 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")

        self._world_btn_frame = tk.Frame(self, bg=BG2)
        self._world_btn_frame.pack(fill="x", padx=8, pady=(0, 4))
        self._world_btns: dict[str, tk.Button] = {}
        for w in WORLDS:
            btn = tk.Button(
                self._world_btn_frame, text=w,
                command=lambda _w=w: self._select_world(_w),
                bg=ACCENT if w == self._selected_world else BG3,
                fg="#000" if w == self._selected_world else FG,
                relief="flat", cursor="hand2",
                font=(UI_FONT, 8, "bold"), padx=8, pady=2,
            )
            btn.pack(side="left", padx=(0, 4))
            self._world_btns[w] = btn

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ---- nagłówek grup ----
        hdr = tk.Frame(self, bg=BG2, pady=8)
        hdr.pack(fill="x", padx=10)
        tk.Label(hdr, text="GRUPY", font=(UI_FONT, 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")
        tk.Button(hdr, text="＋", command=self._new_group,
                  bg=BG2, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(UI_FONT, 11, "bold")).pack(side="right")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # === ULUBIONE (stała wysokość, max 5 wierszy) ===
        self.fav_outer = tk.Frame(self, bg=BG2)
        self.fav_outer.pack(fill="x")
        # zawartość budowana dynamicznie w _refresh()

        # === WSZYSTKIE GRUPY (scrollowalne, wypełnia resztę) ===
        all_lbl_row = tk.Frame(self, bg=BG2, pady=3)
        all_lbl_row.pack(fill="x", padx=10)
        tk.Label(all_lbl_row, text="WSZYSTKIE", font=(UI_FONT, 7, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")

        all_outer = tk.Frame(self, bg=BG2)
        all_outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(all_outer, bg=BG2, highlightthickness=0, bd=0)
        self._vscroll = ttk.Scrollbar(all_outer, orient="vertical",
                                      command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vscroll.set)
        self._vscroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.list_frame = tk.Frame(self._canvas, bg=BG2)
        self._list_win = self._canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>",
                             lambda e: self._canvas.configure(
                                 scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._list_win, width=e.width))
        self._canvas.bind("<Enter>", lambda e: self._bind_scroll(self._canvas))
        self._canvas.bind("<Leave>", lambda e: self._unbind_scroll())

        self._group_rows: dict[str, list] = {}   # name → [row, ...]  (może być w obu sekcjach)
        self._fav_canvas = None
        self._refresh()

        # ---- sekcja Templates ----
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
        tpl_hdr = tk.Frame(self, bg=BG2, pady=6)
        tpl_hdr.pack(fill="x", padx=10)
        tk.Label(tpl_hdr, text="PROFILE", font=(UI_FONT, 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")

        tk.Button(tpl_hdr, text="＋ Template", command=self._add_template_dialog,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(UI_FONT, 8, "bold"), padx=6, pady=2).pack(side="right")

        self.tpl_list_frame = tk.Frame(self, bg=BG2)
        self.tpl_list_frame.pack(fill="x", padx=8, pady=(0, 8))
        self._refresh_templates()

    def _make_group_row(self, parent, name, color, is_all=False) -> tk.Frame:
        row = tk.Frame(parent, bg=BG2, cursor="hand2")
        row.pack(fill="x", padx=6, pady=2)

        row._name       = name
        row._star_lbl   = None
        row._dot        = None
        row._lbl        = None
        row._count_lbl  = None
        row._ctrl_frame = None

        if not is_all:
            # Gwiazdka ulubionych
            is_fav = self.gm.is_favorite(name, self._selected_world)
            star = tk.Label(row, text="★" if is_fav else "☆",
                            font=(UI_FONT, 9), bg=BG2,
                            fg="#FFD700" if is_fav else FG_DIM, cursor="hand2")
            star.pack(side="left", padx=(2, 0))
            row._star_lbl = star
            def _star_click(e, n=name):
                self._toggle_favorite(n)
                return "break"
            star.bind("<Button-1>", _star_click)

        dot = tk.Label(row, text="●", font=(UI_FONT, 10), bg=BG2, fg=color)
        dot.pack(side="left", padx=(4, 4))
        row._dot = dot

        lbl = tk.Label(row, text=name, font=FONT_GRP, bg=BG2, fg=FG, anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        row._lbl = lbl

        if not is_all:
            # Przyciski sterowania grupą: ▶ ⏸ ⏹
            ctrl = tk.Frame(row, bg=BG2)
            ctrl.pack(side="right", padx=(0, 6))
            row._ctrl_frame = ctrl

            _btn_cfg = dict(bg=BG2, fg=FG_DIM, relief="flat", cursor="hand2",
                            font=(UI_FONT, 8), padx=0, pady=0, width=1,
                            bd=0, highlightthickness=0)
            tk.Button(ctrl, text="⏹", command=lambda n=name: self._stop_group(n),
                      **_btn_cfg).pack(side="right")
            tk.Button(ctrl, text="▶", command=lambda n=name: self._start_group(n),
                      **_btn_cfg).pack(side="right")

            count_lbl = tk.Label(row, text="", font=(UI_FONT, 8),
                                  bg=BG2, fg=FG_DIM, width=6, anchor="e")
            count_lbl.pack(side="right")
            row._count_lbl = count_lbl

            def on_right(event, n=name):
                self._context_menu(event, n)
            row.bind("<Button-2>", on_right)
            row.bind("<Button-3>", on_right)
            for w in (dot, lbl, count_lbl):
                w.bind("<Button-2>", on_right)
                w.bind("<Button-3>", on_right)

        def on_click(event, n=name if not is_all else None):
            self._select(n)
        widgets = [row, dot, lbl]
        if row._count_lbl:
            widgets.append(row._count_lbl)
        for w in widgets:
            w.bind("<Button-1>", on_click)

        return row

    def _add_template_dialog(self):
        """Dialog tworzenia nowego szablonu profilu przeglądarki."""
        AddTemplateDialog(
            self.winfo_toplevel(),
            on_created=self._on_template_created,
        )

    def _on_template_created(self, name: str):
        self._refresh_templates()
        if self.on_add_template:
            self.on_add_template()

    def _refresh_templates(self):
        for w in self.tpl_list_frame.winfo_children():
            w.destroy()
        templates = _list_all_templates()
        if not templates:
            tk.Label(self.tpl_list_frame, text="Brak szablonów", font=(UI_FONT, 8),
                     bg=BG2, fg=FG_DIM).pack(anchor="w", padx=4)
        for browser, t in templates:
            row = tk.Frame(self.tpl_list_frame, bg=BG2)
            row.pack(fill="x", pady=1)
            tk.Label(row, text="🗂", font=(UI_FONT, 9),
                     bg=BG2, fg=FG_DIM).pack(side="left", padx=(2, 4))
            tk.Label(row, text=f"[{browser}] {t}", font=(UI_FONT, 8),
                     bg=BG2, fg=FG, anchor="w").pack(side="left", fill="x", expand=True)
            tk.Button(row, text="🗑",
                      command=lambda b=browser, n=t: self._delete_template(b, n),
                      bg=BG2, fg=FG_DIM, relief="flat", cursor="hand2",
                      font=(UI_FONT, 8)).pack(side="right")

    def _delete_template(self, browser: str, name: str):
        from tkinter import messagebox
        if messagebox.askyesno("Usuń template", f"Usunąć szablon '{name}' ({browser})?", parent=self):
            import shutil as _sh
            tpl_path = os.path.join(_get_templates_dir(browser), name)
            _sh.rmtree(tpl_path, ignore_errors=True)
            self._refresh_templates()
            if self.on_add_template:
                self.on_add_template()

    def _create_account_dialog(self):
        CreateAccountDialog(
            self.winfo_toplevel(),
            on_created=self.on_account_created,
        )

    @staticmethod
    def _nk(s: str) -> list:
        """Klucz sortowania naturalnego: 'gordion_9' < 'gordion_10' < 'gordion_114'."""
        return [int(p) if p.isdigit() else p.lower()
                for p in re.split(r'(\d+)', s)]

    def _refresh(self):
        # ---- wyczyść sekcję ULUBIONE ----
        for w in self.fav_outer.winfo_children():
            w.destroy()
        self._fav_canvas = None

        # ---- wyczyść główną listę ----
        for rows in self._group_rows.values():
            for r in rows:
                try:
                    r.destroy()
                except Exception:
                    pass
        self._group_rows.clear()

        groups    = self.gm.groups_in_world(self._selected_world)   # {name: data}
        fav_names = sorted([n for n in groups if self.gm.is_favorite(n, self._selected_world)], key=self._nk)
        all_names = sorted(groups.keys(), key=self._nk)

        def _count_text(data):
            cnt     = len(data["sessions"])
            running = sum(1 for sid in data["sessions"]
                          if self._session_statuses.get(sid) == "RUNNING")
            return f"▶{running}/{cnt}" if running else (str(cnt) if cnt else "")

        def _add_row(parent, name):
            data = groups[name]
            row  = self._make_group_row(parent, name, data["color"])
            row._count_lbl.configure(text=_count_text(data))
            self._group_rows.setdefault(name, []).append(row)

        # ---- sekcja ULUBIONE ----
        if fav_names:
            fhdr = tk.Frame(self.fav_outer, bg=BG2, pady=4)
            fhdr.pack(fill="x", padx=10)
            tk.Label(fhdr, text="ULUBIONE", font=(UI_FONT, 8, "bold"),
                     bg=BG2, fg="#FFD700").pack(side="left")

            n_fav = len(fav_names)
            fav_h = min(n_fav, self._FAV_MAX_ROW) * self._FAV_ROW_H
            fav_wrap = tk.Frame(self.fav_outer, bg=BG2)
            fav_wrap.pack(fill="x")

            self._fav_canvas = tk.Canvas(fav_wrap, bg=BG2, height=fav_h,
                                          highlightthickness=0, bd=0)
            if n_fav > self._FAV_MAX_ROW:
                fav_sb = ttk.Scrollbar(fav_wrap, orient="vertical",
                                        command=self._fav_canvas.yview)
                self._fav_canvas.configure(yscrollcommand=fav_sb.set)
                fav_sb.pack(side="right", fill="y")
            self._fav_canvas.pack(side="left", fill="x", expand=True)

            fav_inner = tk.Frame(self._fav_canvas, bg=BG2)
            fav_win   = self._fav_canvas.create_window((0, 0), window=fav_inner, anchor="nw")
            fav_inner.bind("<Configure>",
                           lambda e: self._fav_canvas.configure(
                               scrollregion=self._fav_canvas.bbox("all")))
            self._fav_canvas.bind("<Configure>",
                                  lambda e: self._fav_canvas.itemconfig(fav_win, width=e.width))
            self._fav_canvas.bind("<Enter>",
                                  lambda e: self._bind_scroll(self._fav_canvas))
            self._fav_canvas.bind("<Leave>", lambda e: self._unbind_scroll())

            for name in fav_names:
                _add_row(fav_inner, name)

            tk.Frame(self.fav_outer, bg=BORDER, height=1).pack(fill="x", pady=(4, 0))

        # ---- sekcja WSZYSTKIE GRUPY ----
        for name in all_names:
            _add_row(self.list_frame, name)

        self.list_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        # jeśli nic nie zaznaczone lub wybrana grupa zniknęła – wybierz pierwszą
        if self.selected is None or self.selected not in self._group_rows:
            first = all_names[0] if all_names else None
            if first and first != self.selected:
                self.after(0, lambda n=first: self._select(n))

        self._highlight()

    def _select(self, name):
        if name == self.selected:
            return
        self.selected = name
        self._highlight()
        if self.on_select_group:
            self.on_select_group(name)

    def _highlight(self):
        def set_row(row, active):
            bg = BG3 if active else BG2
            row.configure(bg=bg)
            for attr in ("_dot", "_lbl", "_count_lbl", "_star_lbl"):
                w = getattr(row, attr, None)
                if w:
                    try:
                        w.configure(bg=bg)
                    except Exception:
                        pass
            cf = getattr(row, "_ctrl_frame", None)
            if cf:
                cf.configure(bg=bg)
                for w in cf.winfo_children():
                    try:
                        w.configure(bg=bg)
                    except Exception:
                        pass

        for name, rows in self._group_rows.items():
            active = name == self.selected
            for row in rows:
                set_row(row, active)

    def _toggle_favorite(self, name: str):
        self.gm.toggle_favorite(name, self._selected_world)

    def _bind_scroll(self, canvas):
        self._active_scroll_canvas = canvas
        canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        canvas.bind_all("<Button-4>",   self._on_mousewheel)
        canvas.bind_all("<Button-5>",   self._on_mousewheel)

    def _unbind_scroll(self):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self._canvas.unbind_all(seq)
            except Exception:
                pass

    def _on_mousewheel(self, event):
        c = getattr(self, "_active_scroll_canvas", self._canvas)
        if event.num == 4:
            c.yview_scroll(-1, "units")
        elif event.num == 5:
            c.yview_scroll(1, "units")
        elif IS_MAC:
            c.yview_scroll(-1 if event.delta > 0 else 1, "units")
        else:
            c.yview_scroll(int(-1 * (event.delta / 120)) or (-1 if event.delta > 0 else 1), "units")

    def update_session_status(self, session_id: int, status: str):
        self._session_statuses[session_id] = status
        self._refresh()

    def _select_world(self, world: str):
        self._selected_world = world
        for w, btn in self._world_btns.items():
            btn.configure(
                bg=ACCENT if w == world else BG3,
                fg="#000" if w == world else FG,
            )
        self.selected = None
        self._refresh()
        if self.on_world_changed:
            self.on_world_changed(world)

    # ---- zarządzanie grupami ----
    def _new_group(self):
        name = simpledialog.askstring("Nowa grupa", "Nazwa grupy:", parent=self)
        if name and self.gm.add_group(name, world=self._selected_world):
            pass
        elif name:
            messagebox.showwarning("Uwaga", f"Grupa '{name}' już istnieje.", parent=self)

    def _context_menu(self, event, group_name: str):
        menu = tk.Menu(self, tearoff=0, bg=BG2, fg=FG,
                       activebackground=BG3, activeforeground=ACCENT,
                       relief="flat", bd=0)
        menu.add_command(label="✏️  Zmień nazwę",
                         command=lambda: self._rename_group(group_name))
        menu.add_command(label="📋  Program grupy…",
                         command=lambda: GroupProgramDialog(self.winfo_toplevel(), self.gm, group_name, self._selected_world))
        menu.add_command(label="🪟  Układ okien…",
                         command=lambda: LayoutDialog(self.winfo_toplevel(), self.gm, group_name, self._selected_world))
        menu.add_separator()
        menu.add_command(label="🗑  Usuń grupę",
                         command=lambda: self._delete_group(group_name))
        menu.tk_popup(event.x_root, event.y_root)

    def _rename_group(self, old):
        new = simpledialog.askstring("Zmień nazwę", f"Nowa nazwa dla '{old}':",
                                      parent=self, initialvalue=old)
        if new and not self.gm.rename_group(old, new, self._selected_world):
            messagebox.showwarning("Uwaga", "Nie można zmienić nazwy.", parent=self)

    def _delete_group(self, name):
        if messagebox.askyesno("Usuń grupę",
                                f"Usunąć grupę '{name}'?\nSesje zostaną przeniesione do Domyślnej.",
                                parent=self):
            self.gm.remove_group(name, self._selected_world)
            if self.selected == name:
                self._select(None)

    # ---- sterowanie grupą ----
    def _start_group(self, group: str, world: str = None) -> int:
        """Start sesji grupy (3 strumienie, logowania po kolei). Zwraca liczbę startowanych sesji."""
        if self._get_sessions_fn is None:
            return 0
        world = world or self._selected_world
        sessions = self._get_sessions_fn()
        to_start = [s for s in sessions
                    if self.gm.group_of(s.session_id) == group
                    and self.gm.world_of_session(s.session_id) == world
                    and not s.is_running and not s.is_banned()]
        if not to_start:
            return 0

        def _sequential():
            STREAMS = 3   # niezależne strumienie startowania

            def stream_worker(sessions, stream_idx):
                # Rozłóż starty w czasie żeby Chrome instances nie kolidowały
                time.sleep(stream_idx * 1.5)
                for s in sessions:
                    s.after(0, s._on_play)
                    # Poczekaj aż _on_play ustawi _runner (max 30s)
                    runner = None
                    t0 = time.time()
                    while time.time() - t0 < 30:
                        r = s._runner
                        if r is not None:
                            runner = r
                            break
                        time.sleep(0.2)
                    # Czekaj na sygnał "logowanie zakończone" tej konkretnej sesji
                    if runner is not None:
                        runner.login_done_event.wait(timeout=300)

            for i, sess_slice in enumerate(
                    [to_start[j::STREAMS] for j in range(STREAMS)]):
                if not sess_slice:
                    continue
                threading.Thread(
                    target=stream_worker,
                    args=(sess_slice, i),
                    daemon=True,
                ).start()

        threading.Thread(target=_sequential, daemon=True).start()
        return len(to_start)

    def _stop_group(self, group: str, world: str = None) -> int:
        if self._get_sessions_fn is None:
            return 0
        world = world or self._selected_world
        n = 0
        for s in self._get_sessions_fn():
            if (self.gm.group_of(s.session_id) == group
                    and self.gm.world_of_session(s.session_id) == world):
                if s.is_running or getattr(s, "_pending_restart", None) is not None:
                    s._on_stop()
                    n += 1
        return n



# ============================================
# DIALOG: NOWY CONFIG
# ============================================
class GroupProgramDialog(tk.Toplevel):
    """Program grupy: każda sesja grupy (bez własnego programu) ustawia go w bocie przy STARCIE i uruchamia bota."""
    NONE = "(bez zmiany – program wybrany w bocie)"

    def __init__(self, parent, gm, group: str, world: str):
        super().__init__(parent)
        self.gm, self.group, self.world = gm, group, world
        self.title(f"Program grupy – {group}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        cur = gm.program_of(group, world)
        progs = _list_programs()
        self.var = tk.StringVar(value=cur or self.NONE)
        tk.Label(self, text=f"📋 Program bota dla grupy „{group}”", font=FONT_BOLD, bg=BG, fg=ACCENT).pack(anchor="w", padx=16, pady=(14, 6))
        ttk.Combobox(self, textvariable=self.var, state="readonly", width=42,
                     values=[self.NONE] + progs + ([cur] if cur and cur not in progs else [])).pack(anchor="w", padx=16)
        tk.Label(self, text="Przy STARCIE sesji launcher ustawia ten program w bocie i uruchamia bota.\n"
                            "Sesja z zaznaczonym „Własny program” używa swojego.",
                 bg=BG, fg=FG_DIM, font=FONT_SMALL, justify="left").pack(anchor="w", padx=16, pady=8)
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(btns, text="Zapisz", command=self._save, bg=GREEN, fg="#000", relief="flat", font=FONT_BOLD, padx=10).pack(side="right")
        tk.Button(btns, text="Anuluj", command=self.destroy, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL, padx=10).pack(side="right", padx=6)

    def _save(self):
        v = self.var.get()
        self.gm.set_program(self.group, self.world, "" if v == self.NONE else v)
        self.destroy()


class LauncherSettingsDialog(tk.Toplevel):
    """Ustawienia launchera: serwer Kraken API (adres panelu i token użytkownika) – zapis do api.json.
    Launcher wysyła wtedy logi sesji, a przy starcie sesji przekazuje adres i token botowi w przeglądarce."""

    def __init__(self, parent, app=None):
        super().__init__(parent)
        from log_shipper import SHIPPER
        self.app = app
        self.title("Ustawienia launchera")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.url = tk.StringVar(value=SHIPPER.url)
        self.token = tk.StringVar(value=SHIPPER.token)
        self.host_name = tk.StringVar(value=SHIPPER.host_name)
        tk.Label(self, text="📡 Serwer Kraken API", font=FONT_BOLD, bg=BG, fg=ACCENT).pack(anchor="w", padx=16, pady=(14, 6))
        for label, var, show in (("Adres panelu:", self.url, ""), ("Token:", self.token, "•"), ("Nazwa hosta:", self.host_name, "")):
            row = tk.Frame(self, bg=BG)
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text=label, width=13, anchor="w", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
            e = tk.Entry(row, textvariable=var, width=48, show=show, bg=BG3, fg=FG, insertbackground=FG, relief="flat", font=FONT_SMALL)
            e.pack(side="left", fill="x", expand=True)
            if show:
                self._tok_entry = e
        self.show = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="pokaż token", variable=self.show, bg=BG, fg=FG_DIM, selectcolor=BG3, activebackground=BG,
                       font=FONT_SMALL, command=lambda: self._tok_entry.configure(show="" if self.show.get() else "•")).pack(anchor="w", padx=16)
        self.info = tk.Label(self, text="Adres i token z panelu (https://…). Przy starcie sesji launcher przekaże je też botowi.",
                             bg=BG, fg=FG_DIM, font=FONT_SMALL, wraplength=460, justify="left")
        self.info.pack(anchor="w", padx=16, pady=(6, 4))
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btns, text="Zapisz", command=self._save, bg=GREEN, fg="#000", relief="flat", font=FONT_BOLD, padx=10).pack(side="right")
        tk.Button(btns, text="Sprawdź połączenie", command=self._check, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL, padx=10).pack(side="right", padx=6)
        tk.Button(btns, text="⬇ Odtwórz z serwera", command=self._restore, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL, padx=10).pack(side="left")
        tk.Button(btns, text="Anuluj", command=self.destroy, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL, padx=10).pack(side="right")

    def _check(self):
        from log_shipper import check
        self.info.configure(text="⏳ Sprawdzam…", fg=FG_DIM)
        url, token = self.url.get(), self.token.get()
        def run():
            msg = check(url, token)
            self.after(0, lambda: self.info.configure(text=msg, fg=GREEN if msg.startswith("✅") else RED))
        threading.Thread(target=run, daemon=True).start()

    def _save(self):
        from log_shipper import save_config
        url = self.url.get().strip()
        if url and not url.lower().startswith("https://"):
            self.info.configure(text="Adres musi zaczynać się od https:// (bot w przeglądarce nie wyśle niczego na http).", fg=RED)
            return
        save_config(url, self.token.get(), self.host_name.get())
        self.destroy()

    def _restore(self):
        """Ustawienia launchera zapisane na serwerze (grupy, sesje, configi kont) → ten komputer."""
        from log_shipper import save_config, HostLink, SHIPPER
        if not self.app:
            return
        save_config(self.url.get(), self.token.get(), self.host_name.get())
        if not SHIPPER.enabled:
            self.info.configure(text="Najpierw adres (https://…) i token.", fg=RED)
            return
        try:
            saved = HostLink.saved_hosts()
        except Exception as e:
            self.info.configure(text=f"❌ Serwer: {str(e)[:120]}", fg=RED)
            return
        if not saved:
            self.info.configure(text="Na serwerze nie ma zapisanych ustawień żadnego launchera z tym tokenem.", fg=RED)
            return
        # Własny host, a gdy go nie ma (nowy komputer) – wybór spośród zapisanych.
        own = next((h for h in saved if h["host_id"] == SHIPPER.host_id), None)
        pick = own
        if not pick:
            labels = [f"{h.get('name') or h['host_id']} – {h['sessions']} sesji, {h['configs']} configów, "
                      f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(h['updated'] or 0))}" for h in saved]
            choice = simpledialog.askinteger("Odtwórz z serwera",
                                             "Którego launchera ustawienia odtworzyć?\n" + "\n".join(f"{i + 1}. {l}" for i, l in enumerate(labels)),
                                             parent=self, minvalue=1, maxvalue=len(saved), initialvalue=1)
            if not choice:
                return
            pick = saved[choice - 1]
        if not messagebox.askyesno("Odtwórz z serwera", f"Zastąpić grupy, sesje i configi ustawieniami „{pick.get('name') or pick['host_id']}”?", parent=self):
            return
        try:
            data = HostLink.fetch_state(pick["host_id"])
            msg = self.app.restore_from_server(data)
        except Exception as e:
            msg = f"❌ {str(e)[:150]}"
        self.info.configure(text=msg, fg=GREEN if msg.startswith("Odtworzono") else RED)


class LayoutDialog(tk.Toplevel):
    """Układ okien grupy: siatka (kolumny × wiersze) na wybranym ekranie i zoom przeglądarki.
    Sesje zajmują miejsca w kolejności w grupie (od lewej, potem kolejny wiersz). Działa od następnego STARTU sesji."""

    def __init__(self, parent, gm, group: str, world: str):
        super().__init__(parent)
        self.gm, self.group, self.world = gm, group, world
        self.title(f"Układ okien – {group}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.screens = _screens()
        lay = gm.layout_of(group, world)
        self.enabled = tk.BooleanVar(value=bool(lay["enabled"]))
        self.screen = tk.StringVar(value=self._screen_label(min(int(lay["screen"]), len(self.screens) - 1)))
        self.cols = tk.StringVar(value=str(lay["cols"]))
        self.rows = tk.StringVar(value=str(lay["rows"]))
        self.zoom = tk.StringVar(value="Auto" if lay["zoom"] == "auto" else f"{lay['zoom']}%")
        pad = {"padx": 14, "pady": 3}
        tk.Checkbutton(self, text="Układaj okna przeglądarek tej grupy", variable=self.enabled, bg=BG, fg=FG,
                       selectcolor=BG3, activebackground=BG, font=FONT_SMALL, command=self._preview).pack(anchor="w", **pad)
        row = tk.Frame(self, bg=BG); row.pack(fill="x", **pad)
        tk.Label(row, text="Ekran:", bg=BG, fg=FG_DIM, font=FONT_SMALL, width=10, anchor="w").pack(side="left")
        cb = ttk.Combobox(row, textvariable=self.screen, state="readonly", width=34,
                          values=[self._screen_label(i) for i in range(len(self.screens))])
        cb.pack(side="left"); cb.bind("<<ComboboxSelected>>", lambda _e: self._preview())
        row = tk.Frame(self, bg=BG); row.pack(fill="x", **pad)
        tk.Label(row, text="Siatka:", bg=BG, fg=FG_DIM, font=FONT_SMALL, width=10, anchor="w").pack(side="left")
        for var, label in ((self.cols, "kolumn"), (self.rows, "wierszy")):
            sp = tk.Spinbox(row, from_=1, to=10, width=3, textvariable=var, command=self._preview,
                            bg=BG3, fg=FG, buttonbackground=BG3, relief="flat")
            sp.pack(side="left"); sp.bind("<KeyRelease>", lambda _e: self._preview())
            tk.Label(row, text=f" {label}   ", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
        row = tk.Frame(self, bg=BG); row.pack(fill="x", **pad)
        tk.Label(row, text="Skalowanie:", bg=BG, fg=FG_DIM, font=FONT_SMALL, width=10, anchor="w").pack(side="left")
        zc = ttk.Combobox(row, textvariable=self.zoom, state="readonly", width=8,
                          values=["Auto"] + [f"{z}%" for z in ZOOM_CHOICES[1:]])
        zc.pack(side="left"); zc.bind("<<ComboboxSelected>>", lambda _e: self._preview())
        self.info = tk.Label(self, text="", bg=BG, fg=FG_DIM, font=FONT_SMALL, justify="left")
        self.info.pack(anchor="w", **pad)
        btns = tk.Frame(self, bg=BG); btns.pack(fill="x", padx=14, pady=(6, 12))
        tk.Button(btns, text="Zapisz", command=self._save, bg=GREEN, fg="#000", relief="flat", font=FONT_BOLD,
                  padx=10).pack(side="right")
        tk.Button(btns, text="Anuluj", command=self.destroy, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL,
                  padx=10).pack(side="right", padx=6)
        self._preview()

    def _screen_label(self, i: int) -> str:
        s = self.screens[i]
        return f"{i + 1}. {s['name']} – {s['w']}×{s['h']}"

    def _layout(self) -> dict:
        try:
            idx = int(self.screen.get().split(".")[0]) - 1
        except ValueError:
            idx = 0
        z = self.zoom.get().rstrip("%").lower()
        def num(v, d):
            try:
                return max(1, min(10, int(v.get())))
            except ValueError:
                return d
        return {"enabled": self.enabled.get(), "screen": max(0, idx), "cols": num(self.cols, 5), "rows": num(self.rows, 2),
                "zoom": "auto" if z == "auto" else z}

    def _preview(self):
        lay = dict(self._layout(), enabled=True)
        a = _window_slot(lay, 0)
        n = lay["cols"] * lay["rows"]
        self.info.configure(text=f"Okno: {a['w']}×{a['h']}, zoom {a['zoom']}% · miejsc w siatce: {n}\n"
                                 f"Sesje wg kolejności w grupie; {n + 1}. sesja wraca na miejsce 1.\n"
                                 "Zmiana działa od następnego STARTU sesji (okno bez kart i paska adresu).")

    def _save(self):
        self.gm.set_layout(self.group, self.world, self._layout())
        self.destroy()


class ScheduleDialog(tk.Toplevel):
    """⏰ Harmonogram: lista wpisów (grupa / sesja, akcja, termin), dodawanie, edycja, wł./wył., uruchom teraz, usuń,
    a pod spodem dziennik ostatnich wykonań. Wpisy wykonuje BotGUI._schedule_tick (co 15 s), zapis w stanie launchera."""

    COLS = (("on", "Wł.", 40), ("target", "Cel", 210), ("action", "Akcja", 200), ("when", "Kiedy", 170),
            ("next", "Następnie", 110), ("last", "Ostatnio", 110))

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Harmonogram")
        self.configure(bg=BG)
        self.transient(parent)
        self.geometry("900x520")
        st = ttk.Style(self)
        st.configure("Treeview", background=BG3, fieldbackground=BG3, foreground=FG, rowheight=22, font=FONT_SMALL)
        st.configure("Treeview.Heading", background=BG2, foreground=FG_DIM, font=FONT_SMALL)
        st.map("Treeview", background=[("selected", VIOLET)])
        tk.Label(self, text="⏰ Harmonogram – start / stop grup i sesji, nowe sesje z nowym configiem",
                 font=FONT_BOLD, bg=BG, fg=ACCENT).pack(anchor="w", padx=14, pady=(12, 6))
        self.tree = ttk.Treeview(self, columns=[c for c, _, _ in self.COLS], show="headings", height=10, selectmode="browse")
        for c, label, w in self.COLS:
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w, anchor="w", stretch=c in ("target", "action"))
        self.tree.pack(fill="x", padx=14)
        self.tree.bind("<Double-1>", lambda _e: self._edit())
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=14, pady=8)
        for text, fn, fg in (("＋ Dodaj", self._add, ACCENT), ("✎ Edytuj", self._edit, FG), ("⏯ Wł. / wył.", self._toggle, FG),
                             ("▶ Uruchom teraz", self._run_now, GREEN), ("🗑 Usuń", self._delete, RED)):
            tk.Button(btns, text=text, command=fn, bg=BG3, fg=fg, relief="flat", cursor="hand2",
                      font=FONT_SMALL, padx=10, pady=3).pack(side="left", padx=(0, 6))
        tk.Label(self, text="Dziennik", font=(UI_FONT, 8, "bold"), bg=BG, fg=FG_DIM).pack(anchor="w", padx=14)
        self.log = tk.Text(self, font=FONT_MONO, bg="#0b0d14", fg="#94a3b8", relief="flat", bd=0, height=10, state="disabled")
        self.log.pack(fill="both", expand=True, padx=14, pady=(2, 12))
        self._refresh()

    def _selected(self):
        sel = self.tree.selection()
        return next((e for e in self.app._schedules if e["id"] == sel[0]), None) if sel else None

    def _refresh(self):
        import scheduler as S
        if not self.winfo_exists():
            return
        sel = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        fmt = lambda t: time.strftime("%d.%m %H:%M", time.localtime(t)) if t else "—"
        for e in self.app._schedules:
            self.tree.insert("", "end", iid=e["id"], values=(
                "✔" if e.get("enabled") else "—", S.describe_target(e), S.ACTIONS.get(e["action"], e["action"]),
                S.describe_when(e), fmt(S.next_run(e)), fmt(e.get("last_run"))))
        if sel and self.tree.exists(sel[0]):
            self.tree.selection_set(sel[0])
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        for t, label, msg in reversed(self.app._schedule_log):
            self.log.insert(tk.END, f"{time.strftime('%d.%m %H:%M:%S', time.localtime(t))}  {label}: {msg}\n")
        self.log.configure(state="disabled")
        self.after(5000, self._refresh)

    def _saved(self, e: dict, is_new: bool):
        if is_new:
            self.app._schedules.append(e)
        self.app._save_state()
        self._refresh()

    def _add(self):
        ScheduleEditDialog(self, self.app, None, self._saved)

    def _edit(self):
        e = self._selected()
        if e:
            ScheduleEditDialog(self, self.app, e, self._saved)

    def _toggle(self):
        e = self._selected()
        if e:
            e["enabled"] = not e.get("enabled")
            if e["enabled"]:
                # odstęp liczony od włączenia; termin „o godzinie”, który już minął – dopiero następny
                e["created"] = time.time()
                e["last_run"] = 0 if e["kind"] == "interval" else time.time()
            self.app._save_state()
            self._refresh()

    def _run_now(self):
        e = self._selected()
        if e:
            e["last_run"] = time.time()
            self.app.run_schedule(e)
            self.app._save_state()
            self._refresh()

    def _delete(self):
        e = self._selected()
        if e and messagebox.askyesno("Harmonogram", "Usunąć zaznaczony wpis?", parent=self):
            self.app._schedules.remove(e)
            self.app._save_state()
            self._refresh()


class ScheduleEditDialog(tk.Toplevel):
    """Wpis harmonogramu: cel (grupa / sesja), akcja, termin (codziennie o godzinie / co N minut / jednorazowo),
    a dla „Nowa sesja z nowym configiem” – ustawienia sesji (puste = jak ostatnia sesja grupy)."""
    SAME = "(jak ostatnia sesja grupy)"

    def __init__(self, parent, app, entry, on_save):
        import scheduler as S
        super().__init__(parent)
        self.S, self.app, self.on_save = S, app, on_save
        self.is_new = entry is None
        self.e = entry if entry is not None else S.new_entry()
        e = self.e
        self.title("Nowy wpis harmonogramu" if self.is_new else "Edycja wpisu harmonogramu")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.groups = [(n, w) for (w, n) in app.gm._groups]
        self.group_labels = [f"{n} ({w})" for n, w in self.groups]
        self.sessions = [(s.uid, s.name, app.gm.group_of(s.session_id)) for s in app._sessions]
        self.session_labels = [f"{n} [{g}]" for _, n, g in self.sessions]
        p = e.get("params") or {}

        self.target = tk.StringVar(value=e["target"])
        cur_g = next((i for i, (n, w) in enumerate(self.groups) if n == e.get("group") and w == e.get("world")), 0)
        self.group = tk.StringVar(value=self.group_labels[cur_g] if self.group_labels else "")
        cur_s = next((i for i, (u, _, _) in enumerate(self.sessions) if u == e.get("session")), 0)
        self.session = tk.StringVar(value=self.session_labels[cur_s] if self.session_labels else "")
        self.action = tk.StringVar(value=S.ACTIONS[e["action"]])
        self.kind = tk.StringVar(value=S.KINDS[e["kind"]])
        self.time = tk.StringVar(value=e.get("time") or "11:00")
        self.days = [tk.BooleanVar(value=i in (e.get("days") or [])) for i in range(7)]
        mins = int(e.get("every") or 60)
        in_h = mins >= 60 and mins % 60 == 0
        self.every = tk.StringVar(value=str(mins // 60 if in_h else mins))
        self.unit = tk.StringVar(value="godzin" if in_h else "minut")
        self.wfrom = tk.StringVar(value=e.get("from") or "")
        self.wto = tk.StringVar(value=e.get("to") or "")
        self.first = tk.StringVar(value=S.FIRST.get(e.get("first") or "after", S.FIRST["after"]))
        self.first_at = tk.StringVar(value=e.get("first_at") or "11:00")
        self._last_action = e["action"]
        self.date = tk.StringVar(value=e.get("date") or time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400)))
        self.prof = tk.StringVar(value=PROF_RANDOM_LABEL if p.get("prof") == PROF_RANDOM
                                 else PROF_LABEL.get(p.get("prof", ""), PROF_LABEL[""]))
        self.server = tk.StringVar(value=p.get("server") or self.SAME)
        self.browser = tk.StringVar(value=p.get("browser") or self.SAME)
        self.template = tk.StringVar(value=p.get("template") or self.SAME)
        self.program = tk.StringVar(value=p.get("program") or "(program grupy)")
        self.start = tk.BooleanVar(value=p.get("start", True))
        self.disable_full = tk.BooleanVar(value=p.get("disable_when_full", True))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", padx=16, pady=(12, 4))
        self.body = body

        def row(parent, label):
            r = tk.Frame(parent, bg=BG)
            tk.Label(r, text=label, width=16, anchor="w", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
            return r

        def combo(parent, var, values, width=30, cmd=None):
            cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=width, font=FONT_SMALL)
            cb.pack(side="left")
            if cmd:
                cb.bind("<<ComboboxSelected>>", lambda _e: cmd())
            return cb

        def entry(parent, var, width=8):
            tk.Entry(parent, textvariable=var, width=width, bg=BG3, fg=FG, insertbackground=FG, relief="flat",
                     font=FONT_SMALL).pack(side="left")

        def check(parent, text, var):
            tk.Checkbutton(parent, text=text, variable=var, bg=BG, fg=FG, selectcolor=BG3, activebackground=BG,
                           font=FONT_SMALL).pack(side="left", padx=(0, 6))

        self.r_target = row(body, "Cel:")
        for val, text in (("group", "Grupa"), ("session", "Sesja")):
            tk.Radiobutton(self.r_target, text=text, value=val, variable=self.target, command=self._layout, bg=BG, fg=FG,
                           selectcolor=BG3, activebackground=BG, font=FONT_SMALL).pack(side="left", padx=(0, 8))
        self.r_group = row(body, "Grupa:")
        combo(self.r_group, self.group, self.group_labels)
        self.r_session = row(body, "Sesja:")
        combo(self.r_session, self.session, self.session_labels)
        self.r_action = row(body, "Akcja:")
        self.action_cb = combo(self.r_action, self.action, list(S.ACTIONS.values()), cmd=self._layout)
        self.r_kind = row(body, "Kiedy:")
        combo(self.r_kind, self.kind, list(S.KINDS.values()), cmd=self._layout)
        self.r_date = row(body, "Data:")
        entry(self.r_date, self.date, 12)
        tk.Label(self.r_date, text="  RRRR-MM-DD", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
        self.r_time = row(body, "Godzina:")
        entry(self.r_time, self.time)
        tk.Label(self.r_time, text="  GG:MM", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
        self.r_days = row(body, "Dni:")
        for i, d in enumerate(S.DAYS):
            check(self.r_days, d, self.days[i])
        self.r_every = row(body, "Odstęp: co")
        entry(self.r_every, self.every, 5)
        tk.Label(self.r_every, text=" ", bg=BG).pack(side="left")
        combo(self.r_every, self.unit, ["minut", "godzin"], 8)
        self.r_first = row(body, "Pierwszy raz:")
        combo(self.r_first, self.first, list(S.FIRST.values()), 22, cmd=self._layout)
        self.first_at_box = tk.Frame(self.r_first, bg=BG)
        tk.Label(self.first_at_box, text="  ", bg=BG).pack(side="left")
        entry(self.first_at_box, self.first_at, 6)
        tk.Label(self.first_at_box, text="  GG:MM, potem co odstęp", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
        self.r_window = row(body, "Tylko w godzinach:")
        entry(self.r_window, self.wfrom, 6)
        tk.Label(self.r_window, text=" – ", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")
        entry(self.r_window, self.wto, 6)
        tk.Label(self.r_window, text="  (puste = cała doba)", bg=BG, fg=FG_DIM, font=FONT_SMALL).pack(side="left")

        # Nowa sesja z nowym configiem
        self.r_new = tk.Frame(body, bg=BG)
        tk.Label(self.r_new, text="Nowa sesja", font=(UI_FONT, 8, "bold"), bg=BG, fg=ACCENT).pack(anchor="w", pady=(8, 2))
        r = row(self.r_new, "Profesja:"); r.pack(fill="x", pady=2)
        combo(r, self.prof, [l for _, l in PROFESSIONS] + [PROF_RANDOM_LABEL], 20)
        r = row(self.r_new, "Serwer:"); r.pack(fill="x", pady=2)
        combo(r, self.server, [self.SAME] + SERVERS, 26)
        r = row(self.r_new, "Przeglądarka:"); r.pack(fill="x", pady=2)
        combo(r, self.browser, [self.SAME] + BROWSERS, 26, cmd=self._refresh_templates)
        r = row(self.r_new, "Szablon:"); r.pack(fill="x", pady=2)
        self.template_cb = combo(r, self.template, [self.SAME], 26)
        r = row(self.r_new, "Program:"); r.pack(fill="x", pady=2)
        combo(r, self.program, ["(program grupy)"] + _list_programs(), 34)
        r = row(self.r_new, ""); r.pack(fill="x", pady=2)
        check(r, "Uruchom sesję po utworzeniu", self.start)
        r = row(self.r_new, ""); r.pack(fill="x", pady=2)
        check(r, f"Wyłącz wpis po zapełnieniu grupy ({app.MAX_PER_GROUP} sesji)", self.disable_full)
        tk.Label(self.r_new, text="Każde wykonanie: nowy config (login, hasło, nick generowane; konto zakłada START sesji)\n"
                                  "i nowa sesja w grupie – aż do zapełnienia grupy.",
                 bg=BG, fg=FG_DIM, font=FONT_SMALL, justify="left").pack(anchor="w", pady=(4, 0))
        self._refresh_templates()

        self.err = tk.Label(self, text="", bg=BG, fg=RED, font=FONT_SMALL)
        self.err.pack(anchor="w", padx=16)
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", padx=16, pady=(4, 14))
        tk.Button(btns, text="Zapisz", command=self._save, bg=GREEN, fg="#000", relief="flat", font=FONT_BOLD, padx=10).pack(side="right")
        tk.Button(btns, text="Anuluj", command=self.destroy, bg=BG3, fg=FG, relief="flat", font=FONT_SMALL, padx=10).pack(side="right", padx=6)
        self._layout()

    def _refresh_templates(self):
        b = self.browser.get()
        vals = [self.SAME] + (_list_templates(b) if b in BROWSERS else [])
        self.template_cb["values"] = vals
        if self.template.get() not in vals:
            self.template.set(self.SAME)

    def _code(self, mapping: dict, label: str) -> str:
        return next((k for k, v in mapping.items() if v == label), "")

    def _layout(self):
        """Pokazuje tylko pola pasujące do celu, akcji i rodzaju terminu."""
        S = self.S
        is_group = self.target.get() == "group"
        acts = list(S.ACTIONS.values()) if is_group else [S.ACTIONS["start"], S.ACTIONS["stop"]]
        self.action_cb["values"] = acts
        if self.action.get() not in acts:
            self.action.set(acts[0])
        action = self._code(S.ACTIONS, self.action.get())
        create = action == "create_session"
        # nowy wpis „Nowa sesja”: domyślnie co 1 godzinę
        if create and self.is_new and action != self._last_action:
            self.kind.set(S.KINDS["interval"])
            self.every.set("1")
            self.unit.set("godzin")
        self._last_action = action
        kind = self._code(S.KINDS, self.kind.get())
        for w in self.body.winfo_children():
            w.pack_forget()
        if self._code(S.FIRST, self.first.get()) == "at":
            self.first_at_box.pack(side="left")
        else:
            self.first_at_box.pack_forget()
        rows = [self.r_target, self.r_group if is_group else self.r_session, self.r_action, self.r_kind]
        rows += {"daily": [self.r_time, self.r_days], "interval": [self.r_every, self.r_first, self.r_window],
                 "once": [self.r_date, self.r_time]}.get(kind, [])
        for r in rows:
            r.pack(fill="x", pady=2)
        if create:
            self.r_new.pack(fill="x")

    def _save(self):
        S, e = self.S, dict(self.e)
        e["target"] = self.target.get()
        if e["target"] == "group":
            i = self.group_labels.index(self.group.get()) if self.group.get() in self.group_labels else -1
            e["group"], e["world"] = self.groups[i] if i >= 0 else ("", "")
            e["session"] = e["session_name"] = ""
        else:
            i = self.session_labels.index(self.session.get()) if self.session.get() in self.session_labels else -1
            e["session"], e["session_name"] = (self.sessions[i][0], self.sessions[i][1]) if i >= 0 else ("", "")
            e["group"] = e["world"] = ""
        e["action"] = self._code(S.ACTIONS, self.action.get())
        e["kind"] = self._code(S.KINDS, self.kind.get())
        e["time"] = self.time.get().strip()
        e["days"] = [i for i, v in enumerate(self.days) if v.get()]
        try:
            e["every"] = int(self.every.get().strip()) * (60 if self.unit.get() == "godzin" else 1)
        except ValueError:
            e["every"] = self.every.get().strip()
        e["from"], e["to"] = self.wfrom.get().strip(), self.wto.get().strip()
        e["first"] = self._code(S.FIRST, self.first.get()) or "after"
        e["first_at"] = self.first_at.get().strip()
        e["date"] = self.date.get().strip()
        same = lambda v: "" if v == self.SAME else v
        e["params"] = {"prof": PROF_RANDOM if self.prof.get() == PROF_RANDOM_LABEL
                               else next((k for k, l in PROFESSIONS if l == self.prof.get()), ""),
                       "server": same(self.server.get()), "browser": same(self.browser.get()),
                       "template": same(self.template.get()),
                       "program": "" if self.program.get() == "(program grupy)" else self.program.get(),
                       "start": self.start.get(), "disable_when_full": self.disable_full.get()}
        err = S.validate(e)
        if err:
            self.err.configure(text=f"⚠️  {err}")
            return
        if e["kind"] == "interval":
            e["every"] = int(e["every"])
        # nowy wpis / zmiana terminu → odliczanie od nowa; godzina, która już minęła, wykona się w kolejnym terminie
        if self.is_new or any(e.get(k) != self.e.get(k) for k in ("kind", "time", "days", "every", "from", "to", "date", "first", "first_at")):
            e["created"] = time.time()
            e["last_run"] = 0 if e["kind"] == "interval" else time.time()
        self.e.clear()
        self.e.update(e)
        self.on_save(self.e, self.is_new)
        self.destroy()


class NewConfigDialog(tk.Toplevel):
    """Okno dialogowe do tworzenia nowego pliku konfiguracyjnego."""

    def __init__(self, parent, config_dir: str, on_created=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.on_created = on_created   # callback(name, path)
        self.result     = None

        self.title("Nowy config")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()               # modal
        self.transient(parent)

        self._build()
        self.update_idletasks()
        # wyśrodkuj względem rodzica
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"360x260+{px-180}+{py-130}")
        self.name_entry.focus_set()

    def _build(self):
        tk.Label(self, text="Nowy config", font=FONT_BOLD,
                 bg=BG, fg=ACCENT).pack(pady=(18, 4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 14))

        form = tk.Frame(self, bg=BG)
        form.pack(fill="x", padx=24)

        def row(label, show=""):
            tk.Label(form, text=label, font=FONT_SMALL,
                     bg=BG, fg=FG_DIM, anchor="w").pack(fill="x", pady=(6, 2))
            var = tk.StringVar()
            e = tk.Entry(form, textvariable=var, font=FONT_SMALL,
                         bg=BG3, fg=FG, insertbackground=FG,
                         relief="flat", show=show)
            e.pack(fill="x", ipady=5)
            return var, e

        self.name_var,  self.name_entry  = row("Nazwa pliku (bez .json)")
        self.login_var, self.login_entry = row("Login (username)")
        self.pass_var,  self.pass_entry  = row("Hasło", show="●")

        self.error_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                   bg=BG, fg=RED)
        self.error_lbl.pack(pady=(8, 0))

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=(10, 18))
        tk.Button(btn_row, text="Anuluj", command=self.destroy,
                  bg=BG3, fg=FG_DIM, relief="flat", cursor="hand2",
                  font=FONT_SMALL, padx=14, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="✅ Zapisz", command=self._save,
                  bg=GREEN, fg="#000", relief="flat", cursor="hand2",
                  font=FONT_BOLD, padx=14, pady=5).pack(side="left")

        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        name  = self.name_var.get().strip()
        login = self.login_var.get().strip()
        pwd   = self.pass_var.get()

        if not name:
            self.error_lbl.configure(text="⚠️  Podaj nazwę pliku!")
            return
        if not login:
            self.error_lbl.configure(text="⚠️  Podaj login!")
            return
        if not pwd:
            self.error_lbl.configure(text="⚠️  Podaj hasło!")
            return

        # sanityzacja nazwy
        safe = "".join(c for c in name if c.isalnum() or c in "-_")
        if not safe:
            self.error_lbl.configure(text="⚠️  Niedozwolone znaki w nazwie!")
            return

        filename = f"{safe}.json"
        path = os.path.join(self.config_dir, filename)

        if os.path.exists(path):
            self.error_lbl.configure(text=f"⚠️  Plik '{filename}' już istnieje!")
            return

        data = {"login": [{"username": login, "password": pwd}]}
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.error_lbl.configure(text=f"❌ Błąd zapisu: {e}")
            return

        if self.on_created:
            self.on_created(filename, path)
        self.destroy()

class SessionTab(tk.Frame):
    """Sesja: konto (config), serwer, przeglądarka i szablon profilu. START – przeglądarka z profilem grupy,
    logowanie i jednorazowa captcha; dalej gra bot Kraken (Tampermonkey). STOP – zamknięcie przeglądarki."""

    def __init__(self, parent, session_id: int,
                 config_map: dict,
                 group_manager: GroupManager,
                 name: str = "",
                 on_status_change=None,
                 on_config_added=None,
                 on_config_refresh=None,
                 get_all_sessions_fn=None,
                 on_banned=None):
        super().__init__(parent, bg=BG)
        self.on_banned            = on_banned
        self.session_id           = session_id
        self.name                 = name[:20] if name else ""
        # Stały identyfikator sesji (polecenia start/stop z panelu WWW trafiają po nim).
        import uuid as _uuid
        self.uid                  = _uuid.uuid4().hex[:12]
        self._config_map          = config_map
        self.gm                   = group_manager
        self.on_status_change     = on_status_change
        self.on_config_added      = on_config_added
        self.on_config_refresh    = on_config_refresh
        self._get_all_sessions_fn = get_all_sessions_fn

        self.stop_event       = threading.Event()
        self.bot_thread       = None
        self._runner          = None
        self.is_running       = False
        self.status           = "OFFLINE"
        self._pending_restart = None   # after() ID for restart-on-fail

        self._build()

    def _build(self):
        # PID label — prawy górny róg (nad rząd 1, wyrównany przez place)
        self.pid_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                bg=BG, fg=FG_DIM)
        self.pid_lbl.place(relx=1.0, x=-90, y=7, anchor="ne")

        # ---- rząd 1: config + serwer ----
        row1 = tk.Frame(self, bg=BG, pady=6)
        row1.pack(fill="x", padx=14)

        tk.Label(row1, text="Config:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.config_var = tk.StringVar()
        self.cfg_cb = ttk.Combobox(row1, textvariable=self.config_var,
                               font=FONT_SMALL, state="readonly", width=22)
        self._refresh_config_cb()
        self.cfg_cb.pack(side="left", padx=(0, 4))
        tk.Button(row1, text="＋", command=self._new_account,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(UI_FONT, 11, "bold"), padx=4).pack(side="left", padx=(0, 4))
        tk.Button(row1, text="✎", command=self._new_config,
                  bg=BG3, fg=FG_DIM, relief="flat", cursor="hand2",
                  font=(UI_FONT, 10), padx=3).pack(side="left", padx=(0, 4))
        tk.Button(row1, text="⟳", command=self._refresh_config_now,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=(UI_FONT, 11, "bold"), padx=4).pack(side="left", padx=(0, 10))

        tk.Label(row1, text="Serwer:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.server_var = tk.StringVar(value=SERVERS[0])
        server_cb = ttk.Combobox(row1, textvariable=self.server_var,
                                  font=FONT_SMALL, state="readonly", width=10)
        server_cb["values"] = SERVERS
        server_cb.pack(side="left", padx=(0, 14))

        # ---- rząd 1b: browser + template + anti-afk ----
        row1b = tk.Frame(self, bg=BG, pady=2)
        row1b.pack(fill="x", padx=14)

        tk.Label(row1b, text="Przeglądarka:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.browser_var = tk.StringVar(value="Brave")
        browser_cb = ttk.Combobox(row1b, textvariable=self.browser_var,
                                   font=FONT_SMALL, state="readonly", width=10)
        browser_cb["values"] = BROWSERS
        browser_cb.pack(side="left", padx=(0, 14))
        browser_cb.bind("<<ComboboxSelected>>", self._refresh_template_cb)

        tk.Label(row1b, text="Template:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.template_var = tk.StringVar(value="(brak)")
        self.template_cb  = ttk.Combobox(row1b, textvariable=self.template_var,
                                          font=FONT_SMALL, state="readonly", width=18)
        self._refresh_template_cb()
        self.template_cb.pack(side="left", padx=(0, 4))
        tk.Button(row1b, text="✏️ Edit", command=self._edit_template,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=FONT_SMALL, padx=6, pady=2).pack(side="left", padx=(0, 8))

        self.recreate_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Recreate",
                       variable=self.recreate_var,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(0, 14))

        self.restart_on_fail_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Restart on fail",
                       variable=self.restart_on_fail_var,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(10, 0))

        # ---- rząd 1d: profesja postaci (zapis w configu) ----
        row1d = tk.Frame(self, bg=BG, pady=2)
        row1d.pack(fill="x", padx=14)
        tk.Label(row1d, text="Profesja:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.prof_var = tk.StringVar(value=PROF_LABEL[""])
        self.prof_cb = ttk.Combobox(row1d, textvariable=self.prof_var, font=FONT_SMALL, state="readonly", width=18,
                                    values=[l for _, l in PROFESSIONS])
        self.prof_cb.pack(side="left")
        self.prof_cb.bind("<<ComboboxSelected>>", self._on_prof_selected)
        tk.Label(row1d, text="(zapis w configu; bot wybiera ją w tutorialu)", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(8, 0))
        self.cfg_cb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_prof(), add="+")
        self.after(0, self._refresh_prof)

        # ---- rząd 1c: program bota (z grupy albo własny sesji) ----
        row1c = tk.Frame(self, bg=BG, pady=2)
        row1c.pack(fill="x", padx=14)
        tk.Label(row1c, text="Program:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.prog_override_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1c, text="Własny program", variable=self.prog_override_var, command=self._refresh_program_row,
                       bg=BG, fg=FG, selectcolor=BG, activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(0, 6))
        self.program_var = tk.StringVar(value="")
        self.program_cb = ttk.Combobox(row1c, textvariable=self.program_var, font=FONT_SMALL, state="disabled", width=30)
        self.program_cb.pack(side="left")
        self.program_info = tk.Label(row1c, text="", font=FONT_SMALL, bg=BG, fg=FG_DIM)
        self.program_info.pack(side="left", padx=(8, 0))
        self.gm.subscribe(self._on_groups_changed)
        self.after(0, self._refresh_program_row)

        # ---- rząd 4: przyciski sterowania ----
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=14, pady=(8, 4))

        self.play_btn = tk.Button(ctrl, text="▶ START", command=self._on_play,
                                   bg=GREEN, fg="#000", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", padx=12, pady=5)
        self.play_btn.pack(side="left", padx=(0, 4))

        self.stop_btn = tk.Button(ctrl, text="⏹ STOP", command=self._on_stop,
                                   bg=RED, fg="#fff", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", padx=12, pady=5,
                                   state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 14))

        self.status_lbl = tk.Label(ctrl, text="● OFFLINE", font=FONT_SMALL,
                                    bg=BG, fg=FG_DIM)
        self.status_lbl.pack(side="left")

        # Bot w sesji: start/stop bez zamykania przeglądarki
        self.bot_start_btn = tk.Button(ctrl, text="▶ Bot", command=lambda: self.bot_command("bot_start"),
                                       bg=BG3, fg=GREEN, font=FONT_BOLD, relief="flat", cursor="hand2", padx=8, pady=4,
                                       state="disabled")
        self.bot_start_btn.pack(side="left", padx=(16, 4))
        self.bot_stop_btn = tk.Button(ctrl, text="⏸ Bot", command=lambda: self.bot_command("bot_stop"),
                                      bg=BG3, fg=ACCENT, font=FONT_BOLD, relief="flat", cursor="hand2", padx=8, pady=4,
                                      state="disabled")
        self.bot_stop_btn.pack(side="left", padx=(0, 6))
        self.bot_lbl = tk.Label(ctrl, text="", font=FONT_SMALL, bg=BG, fg=FG_DIM)
        self.bot_lbl.pack(side="left")
        self.after(2000, self._refresh_bot_row)

        tk.Button(ctrl, text="🗑 Wyczyść", command=self._clear_log,
                  bg=BG, fg=FG_DIM, relief="flat", cursor="hand2",
                  font=FONT_SMALL).pack(side="right")

        # ---- log ----
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(4, 0))
        self.log_widget = tk.Text(self, font=FONT_MONO,
                                   bg="#0b0d14", fg="#94a3b8",
                                   insertbackground=FG, relief="flat", bd=0,
                                   wrap="word", state="disabled")
        self.log_widget.pack(fill="both", expand=True, padx=14, pady=(4, 10))
        self.logger = SessionLogger(self.log_widget, profile_name=self.name or "session")

    def _edit_template(self):
        """Otwórz wybraną przeglądarkę z wybranym templatem — tylko margonem.pl."""
        tpl = self.template_var.get()
        if tpl == "(brak)":
            self.logger.write("⚠️  Wybierz template przed edycją!")
            return
        browser = self.browser_var.get()
        tpl_path = os.path.join(_get_templates_dir(browser), tpl)
        if not os.path.isdir(tpl_path):
            self.logger.write(f"⚠️  Katalog template nie istnieje: {tpl_path}")
            return

        self.logger.write(f"🌐 Otwieranie template '{tpl}' ({browser}) w przeglądarce...")

        def _open():
            try:
                import undetected_chromedriver as uc
                opts = uc.ChromeOptions()
                opts.add_argument("--password-store=basic")
                opts.add_argument("--use-mock-keychain")
                opts.add_argument("--disable-blink-features=AutomationControlled")
                opts.add_argument(f"--user-data-dir={tpl_path}")
                opts.add_argument("--start-maximized")
                opts.add_experimental_option("prefs", {
                    "credentials_enable_service": False,
                    "profile.password_manager_enabled": False,
                })
                if _browser_binary(browser):
                    opts.binary_location = _browser_binary(browser)
                driver = _start_uc(opts, browser, self.logger.write)
                driver.get("https://margonem.pl")
                self.logger.write(
                    f"✅ Template '{tpl}' otwarty — skonfiguruj przeglądarkę i zamknij okno.")
            except Exception as e:
                self.logger.write(f"❌ Błąd edycji template: {e}")

        threading.Thread(target=_open, daemon=True).start()

    def _refresh_template_cb(self, _=None):
        """Odśwież listę szablonów profili dla wybranej przeglądarki."""
        browser = self.browser_var.get()
        templates = ["(brak)"] + _list_templates(browser)
        self.template_cb["values"] = templates
        cur = self.template_var.get()
        if cur not in templates or cur == "(brak)":
            self.template_var.set(templates[1] if len(templates) > 1 else "(brak)")

    def _new_account(self):
        """＋: od razu nowy plik configu z wygenerowanym loginem, hasłem i nickiem ("provisioned": false).
        Konto i postać zakłada START tej sesji (w jej przeglądarce i profilu); plik istnieje od razu i jest na liście."""
        name, path, data = create_auto_config()
        nick = data["nick"]
        self.logger.write(f"🆕 Nowe konto (do założenia przy START): {name} – login {data['login'][0]['username']}, nick {nick}")
        self._on_config_file_created(name, path)

    def _new_config(self):
        """✎: ręczny config (istniejące konto – login i hasło wpisywane)."""
        base = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(base, "config")
        NewConfigDialog(
            self.winfo_toplevel(),
            config_dir,
            on_created=self._on_config_file_created,
        )

    def _on_config_file_created(self, filename: str, path: str):
        """Wywoływany gdy nowy plik config zostanie zapisany."""
        self._config_map[filename] = path
        self._refresh_config_cb()
        self.set_config(filename)
        self.logger.write(f"✅ Nowy config: {filename}")
        # powiadom BotGUI żeby zaktualizował pozostałe sesje
        if self.on_config_added:
            self.on_config_added(filename, path)

    def config_key(self) -> str:
        """Nazwa pliku wybranego configu (bez dopisku „(zablokowane)” z listy)."""
        v = self.config_var.get()
        return v[:-len(BANNED_SUFFIX)] if v.endswith(BANNED_SUFFIX) else v

    def _config_label(self, key: str) -> str:
        p = self._config_map.get(key)
        return key + BANNED_SUFFIX if p and config_banned(p) else key

    def set_config(self, key: str):
        self.config_var.set(self._config_label(key))

    def is_banned(self) -> bool:
        p = self._config_path()
        return bool(p) and config_banned(p)

    def _refresh_config_cb(self):
        """Odśwież wartości comboboxa configów (zablokowane konta z dopiskiem „(zablokowane)”)."""
        cur = self.config_key()
        self.cfg_cb["values"] = [self._config_label(k) for k in self._config_map]
        if cur in self._config_map:
            self.set_config(cur)
        elif self._config_map:
            self.set_config(next(iter(self._config_map)))

    def _refresh_config_now(self):
        """Wczytaj ponownie listę configów z katalogu (np. po ręcznym dodaniu pliku)."""
        if self.on_config_refresh:
            self.on_config_refresh()
        else:
            self._refresh_config_cb()
        self.logger.write("🔄 Lista configów odświeżona z katalogu.")

    # ---- tryb ----
    def _validate(self):
        cfg_key = self.config_key()
        cfg     = self._config_map.get(cfg_key, cfg_key)
        if not cfg or not os.path.isfile(cfg):
            self.logger.write("⚠️  Wybierz plik konfiguracyjny!")
            return None
        if config_banned(cfg):
            self.logger.write(f"⛔ Konto z configu {cfg_key} jest zablokowane – sesja nie wystartuje")
            return None

        # ---- sprawdź config lock ----
        cfg_base  = os.path.splitext(os.path.basename(cfg))[0]
        lock_path = os.path.join(os.path.dirname(cfg), f"{cfg_base}.lock")
        if os.path.exists(lock_path):
            is_stale = True

            # 1. czy jakaś INNA działająca sesja w tej samej instancji używa tego configa?
            if self._get_all_sessions_fn is not None:
                for s in self._get_all_sessions_fn():
                    if s.session_id == self.session_id:
                        continue
                    if s.is_running and s._runner is not None:
                        s_cfg = s._runner.config.get("config_path", "")
                        if os.path.normcase(s_cfg) == os.path.normcase(cfg):
                            is_stale = False
                            break

            # 2. jeśli nikt w tej instancji — sprawdź PID w pliku locka
            if is_stale:
                try:
                    with open(lock_path) as _lf:
                        _pid = int(_lf.read().strip())
                    if _pid != os.getpid():
                        # Zewnętrzny proces — sprawdź czy żyje
                        if _pid_alive(_pid):
                            is_stale = False   # żyje → aktywny lock
                    # _pid == os.getpid() ale żadna sesja nie używa → stale
                except Exception:
                    pass  # nie można odczytać PID → traktuj jako stale

            if is_stale:
                try:
                    os.remove(lock_path)
                    self.logger.write(f"🧹 Usunięto nieaktualny lock: {cfg_base}.lock")
                except Exception:
                    pass
            else:
                self.logger.write(
                    f"⚠️  Config '{cfg_key}' jest już używany przez inną sesję!")
                return None

        return {
            "config_path":     cfg,
            "browser":         self.browser_var.get(),
            "server":          self.server_var.get(),
            "template":        None if self.template_var.get() == "(brak)" else self.template_var.get(),
            "group":           self.gm.group_of(self.session_id),
            "group_world":     self.gm.world_of_session(self.session_id),
            "recreate":        self.recreate_var.get(),
            # Program bota: własny sesji albo program grupy ('' – bot zostaje przy swoim).
            "program":         self.effective_program(),
            # Układ okien grupy: miejsce wg kolejności sesji w grupie, ekran i zoom z ustawień grupy.
            "window":          _window_slot(self.gm.layout_of(self.gm.group_of(self.session_id),
                                                              self.gm.world_of_session(self.session_id)),
                                            self.gm.slot_of(self.session_id)),
        }

    # ---- sterowanie ----
    def _on_play(self):
        if self.is_running:
            return
        config = self._validate()
        if config is None:
            return
        self.stop_event.clear()
        self.is_running = True
        self._set_status("RUNNING")
        self.play_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        runner = BotRunner(config, self.stop_event, self.logger)
        self._runner = runner
        self.bot_thread = threading.Thread(
            target=self._bot_wrapper, args=(runner,), daemon=True)
        self.bot_thread.start()
        self.logger.write(
            f"🚀 Start  {os.path.basename(config['config_path'])}  "
            f"[{config['server']} · {config['browser']} · grupa: {self.gm.group_of(self.session_id)}]")
        self._poll_pid()

    def _bot_wrapper(self, runner: BotRunner):
        try:
            runner.run()
        finally:
            crashed = getattr(runner, "crashed", False) and not self.stop_event.is_set()
            banned = getattr(runner, "banned", False)
            self.after(0, lambda c=crashed, b=banned: self._on_finished(c, b))

    def _poll_pid(self):
        if not self.is_running:
            return
        runner = self._runner
        if runner is None:
            return
        pid = getattr(runner, "browser_pid", None)
        if pid:
            self.pid_lbl.configure(text=f"PID {pid}")
        else:
            self.after(500, self._poll_pid)

    def _on_stop(self):
        # Cancel a pending restart-on-fail even if the bot isn't running yet
        if self._pending_restart is not None:
            self.after_cancel(self._pending_restart)
            self._pending_restart = None
            if not self.is_running:
                self._set_status("OFFLINE")
                self.play_btn.configure(state="normal")
                self.logger.write("⏹️  Restart anulowany")
                return

        if not self.is_running:
            return

        self.stop_event.set()

        # Immediate UI feedback — disable buttons so user knows the click landed
        self._set_status("STOPPING")
        self.stop_btn.configure(state="disabled")
        self.logger.write("⏹️  Zatrzymywanie...")
        self.after(5000, self._force_kill_if_needed)

    def _force_kill_if_needed(self):
        if not self.is_running:
            return
        runner = self._runner
        pid = getattr(runner, "browser_pid", None) if runner else None
        if pid:
            try:
                _kill_pid(pid)
                self.logger.write(f"💀 Wymuszono zamknięcie PID {pid}")
            except Exception as e:
                self.logger.write(f"⚠️  SIGKILL PID {pid} nie powiodło się: {e}")
        else:
            self.logger.write("⚠️  Brak PID — nie można wymusić zatrzymania")

    def _on_finished(self, crashed: bool = False, banned: bool = False):
        self._runner    = None
        self.is_running = False
        self._set_status("OFFLINE")
        self.play_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.pid_lbl.configure(text="")
        if banned:
            if self.on_banned:
                self.on_banned(self)
            return

        if crashed and self.restart_on_fail_var.get():
            delay = 10
            self.logger.write(f"🔄 Restart za {delay}s...")
            self._pending_restart = self.after(delay * 1000, self._do_restart)

    def _do_restart(self):
        self._pending_restart = None
        self._on_play()

    def _set_status(self, status: str):
        self.status = status
        color = STATUS_COLORS.get(status, FG_DIM)
        self.status_lbl.configure(text=f"● {status}", fg=color)
        if self.on_status_change:
            self.on_status_change(self.session_id, status)

    def _clear_log(self):
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", tk.END)
        self.log_widget.configure(state="disabled")

    @property
    def bot_state(self) -> str:
        r = self._runner
        return (r.bot_state if r and self.is_running else "") or ""

    def _refresh_bot_row(self):
        try:
            if not self.winfo_exists():
                return
            st = self.bot_state
            self.bot_start_btn.configure(state="normal" if self.is_running and st == "stopped" else "disabled")
            self.bot_stop_btn.configure(state="normal" if self.is_running and st == "running" else "disabled")
            self.bot_lbl.configure(text={"running": "🤖 bot pracuje", "stopped": "🤖 bot zatrzymany",
                                         "loading": "🤖 bot się wczytuje"}.get(st, ""),
                                   fg=GREEN if st == "running" else FG_DIM)
            self.after(2000, self._refresh_bot_row)
        except Exception:
            pass

    def bot_command(self, action: str, done=None):
        """▶/⏸ Bot (launcher albo panel WWW): bot w działającej sesji; start z bieżącym programem sesji/grupy."""
        r = self._runner
        if not (r and self.is_running):
            if done:
                done(False, "sesja nie działa")
            return
        self.logger.write("▶ Start bota" if action == "bot_start" else "⏸ Zatrzymanie bota")
        r.bot_command(action, self.effective_program() if action == "bot_start" else None, done)

    def _config_path(self) -> str:
        key = self.config_key()
        return self._config_map.get(key, "") if key else ""

    def current_prof(self) -> str:
        p = self._config_path()
        return config_prof(p) if p and os.path.isfile(p) else ""

    def _refresh_prof(self):
        try:
            self.prof_var.set(PROF_LABEL.get(self.current_prof(), PROF_LABEL[""]))
        except Exception:
            pass

    def _on_prof_selected(self, _e=None):
        p = self._config_path()
        if not p or not os.path.isfile(p):
            self.logger.write("⚠️  Wybierz najpierw config – profesja zapisuje się w configu postaci")
            self._refresh_prof()
            return
        code = next((k for k, l in PROFESSIONS if l == self.prof_var.get()), "")
        set_config_prof(p, code)
        self.logger.write(f"🎓 Profesja w configu {os.path.basename(p)}: {PROF_LABEL[code]}")

    def _on_groups_changed(self):
        # Zamknięta karta sesji nadal jest na liście obserwatorów grup – bez wyjątku dla pozostałych.
        try:
            self.after(0, self._refresh_program_row)
        except Exception:
            pass

    def _group_program(self) -> str:
        return self.gm.program_of(self.gm.group_of(self.session_id), self.gm.world_of_session(self.session_id))

    def effective_program(self) -> str:
        """Program dla bota tej sesji: własny (gdy zaznaczony) albo program grupy; '' = bez zmiany."""
        return self.program_var.get().strip() if self.prog_override_var.get() else self._group_program()

    def _refresh_program_row(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        progs = _list_programs()
        if self.prog_override_var.get():
            self.program_cb.configure(state="readonly", values=progs)
            if not self.program_var.get():
                self.program_var.set(self._group_program() or (progs[0] if progs else ""))
            self.program_info.configure(text="tylko ta sesja")
        else:
            self.program_cb.configure(state="disabled", values=progs)
            gp = self._group_program()
            self.program_var.set(gp)
            self.program_info.configure(text="z grupy" if gp else "grupa: bez zmiany (program z bota)")

    def get_settings(self) -> dict:
        """Zwraca słownik bieżących ustawień sesji (do zapisu stanu)."""
        return {
            "uid":             self.uid,
            "name":            self.name,
            "config":          self.config_key(),
            "group":           self.gm.group_of(self.session_id),
            "group_world":     self.gm.world_of_session(self.session_id),
            "browser":         self.browser_var.get(),
            "server":          self.server_var.get(),
            "template":        self.template_var.get(),
            "recreate":        self.recreate_var.get(),
            "restart_on_fail": self.restart_on_fail_var.get(),
            "program_override": self.prog_override_var.get(),
            "program":         self.program_var.get() if self.prog_override_var.get() else "",
        }

    def apply_settings(self, d: dict):
        """Przywraca ustawienia sesji z zapisanego słownika (stare pola trybów są pomijane)."""
        if d.get("config") in self._config_map:
            self.set_config(d["config"])
        if d.get("browser") in BROWSERS:
            self.browser_var.set(d["browser"])
            self._refresh_template_cb()
        if d.get("server") in SERVERS:
            self.server_var.set(d["server"])
        tpl = d.get("template") or "(brak)"
        if tpl in ["(brak)"] + _list_templates(self.browser_var.get()):
            self.template_var.set(tpl)
        if "recreate" in d:
            self.recreate_var.set(bool(d["recreate"]))
        if "restart_on_fail" in d:
            self.restart_on_fail_var.set(bool(d["restart_on_fail"]))
        if d.get("program_override"):
            self.prog_override_var.set(True)
            self.program_var.set(d.get("program", ""))
        self.after(0, self._refresh_program_row)
        if "name" in d:
            self.name = str(d["name"])[:20]
        if d.get("uid"):
            self.uid = str(d["uid"])[:24]
        grp_world = d.get("group_world", WORLDS[0])
        group = d.get("group") or self.gm.first_group(grp_world)
        if group and group in self.gm.group_names(grp_world):
            self.gm.assign(self.session_id, group, grp_world)

    def stop_all(self):
        if self._pending_restart is not None:
            self.after_cancel(self._pending_restart)
            self._pending_restart = None
        self.stop_event.set()


# ============================================
# GŁÓWNE OKNO
# ============================================
class BotGUI:
    MAX_PER_GROUP = 10

    def __init__(self, root: tk.Tk, app_icon=None):
        self.root     = root
        self._app_icon = app_icon
        root.title("Kraken — Żul Operator")
        root.configure(bg=BG)
        root.minsize(1060, 660)

        self._config_map:    dict = {}
        self._sessions:   list = []
        self._session_counter = 0
        self._selected_world: str = WORLDS[0]

        self.gm = GroupManager()

        self._state_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "sessions_state.json")

        self._schedules: list = []        # wpisy harmonogramu (scheduler.py)
        self._schedule_log: list = []     # ostatnie wykonania: (czas, opis, wynik)

        self._scan_files()
        self._cleanup_lock_files()
        self._build_ui()
        self._load_state()
        self.root.after(5000, self._schedule_tick)
        # Host w panelu WWW: sygnał z listą sesji, polecenia start/stop, zapis ustawień na serwer.
        from log_shipper import HOST
        HOST.start()
        self._last_pushed = ""
        self._last_push_check = 0.0
        self.root.after(1500, self._host_tick)

    # ---- skanowanie ----
    def _scan_files(self):
        base = os.path.dirname(os.path.abspath(__file__))
        skip = {"discord.json"}

        config_dir = os.path.join(base, "config")
        configs = sorted([
            f for f in glob.glob(os.path.join(config_dir, "*.json"))
            if os.path.basename(f) not in skip
        ])
        self._config_map = {os.path.basename(p): p for p in configs}


    # ---- UI ----
    def _build_ui(self):
        root = self.root

        # --- nagłówek — belka z grafiką Krakena ---
        hdr = tk.Frame(root, bg=BG, height=HEADER_H)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # grafika po lewej (nie rozciąga się)
        _hdr_img, _img_w = _build_header_image(BG, height=HEADER_H)
        if _hdr_img:
            img_cv = tk.Canvas(hdr, bg=BG, width=_img_w, height=HEADER_H,
                               highlightthickness=0, bd=0)
            img_cv.pack(side="left")
            img_cv.create_image(0, 0, anchor="nw", image=_hdr_img)
            self._header_img_ref = _hdr_img  # zapobiegaj GC

        # prawa strona: tytuł + przyciski
        hdr_right = tk.Frame(hdr, bg=BG)
        hdr_right.pack(side="left", fill="both", expand=True)

        title_lbl = tk.Label(hdr_right, text="KRAKEN — ŻUL OPERATOR",
                             font=FONT_TITLE, bg=BG, fg=ACCENT)
        title_lbl.place(relx=0.0, rely=0.5, anchor="w", x=20)

        btn_frame = tk.Frame(hdr_right, bg=BG)
        btn_frame.place(relx=1.0, rely=0.5, anchor="e", x=-12)

        tk.Button(btn_frame, text="⏹ STOP ALL", command=self._stop_all,
                  bg=RED, fg="#fff", font=FONT_BOLD, relief="flat",
                  cursor="hand2", padx=10, pady=4).pack(side="right", padx=(6, 0))
        self.add_btn = tk.Button(btn_frame, text="＋  Nowa sesja",
                                  command=self._add_session,
                                  bg=BG3, fg=ACCENT, font=FONT_BOLD,
                                  relief="flat", cursor="hand2", padx=10, pady=4)
        self.add_btn.pack(side="right", padx=(6, 0))
        tk.Button(btn_frame, text="⏰ Harmonogram",
                  command=lambda: ScheduleDialog(root, self),
                  bg=BG3, fg=ACCENT, font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="right", padx=(6, 0))
        tk.Button(btn_frame, text="🗑 Usuń zablokowane",
                  command=self._delete_banned_ui,
                  bg=BG3, fg=RED, font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="right", padx=(6, 0))
        tk.Button(btn_frame, text="⚙️ Ustawienia",
                  command=lambda: LauncherSettingsDialog(root, app=self),
                  bg=BG3, fg=FG, font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="right", padx=(6, 0))
        tk.Button(btn_frame, text="💾 Zapisz",
                  command=self._on_save,
                  bg=BG3, fg=FG, font=FONT_BOLD,
                  relief="flat", cursor="hand2", padx=10, pady=4).pack(side="right", padx=(6, 0))

        tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

        # --- główny obszar: sidebar + notebook ---
        main = tk.Frame(root, bg=BG)
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # sidebar grup
        self.group_panel = GroupPanel(
            main, self.gm,
            on_select_group=self._on_group_filter,
            on_add_template=self._on_template_added,
            get_sessions_fn=lambda: self._sessions,
            on_account_created=self._on_config_added,
            on_world_changed=self._on_world_changed)
        self.group_panel.pack(side="left", fill="y", padx=(8, 0), pady=8)

        # separator
        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y", pady=8)

        # notebook sesji
        nb_frame = tk.Frame(main, bg=BG)
        nb_frame.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Bot.TNotebook",
                         background=BG, borderwidth=0, tabmargins=[2, 4, 0, 0])
        style.configure("Bot.TNotebook.Tab",
                         background=BG3, foreground=FG_DIM,
                         padding=[6, 6], font=FONT_SMALL, borderwidth=0)
        style.map("Bot.TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", FG)])

        self.notebook = ttk.Notebook(nb_frame, style="Bot.TNotebook")
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<Button-3>", self._on_tab_right_click)
        self.notebook.bind("<Button-2>", self._on_tab_right_click)
        self.notebook.bind("<Double-Button-1>", self._on_tab_double_click)
        self.notebook.bind("<ButtonPress-1>", self._on_tab_drag_start)
        self.notebook.bind("<B1-Motion>", self._on_tab_drag_motion)
        self.notebook.bind("<ButtonRelease-1>", self._on_tab_drag_end)
        self._drag_state: dict = {"active": False, "src_idx": None}

        # pasek statusu
        self.statusbar = tk.Label(root, text="", font=FONT_SMALL,
                                   bg=BG2, fg=FG_DIM, anchor="w",
                                   padx=12, pady=4)
        self.statusbar.pack(fill="x")

        self._group_filter: str | None = None  # None = wszystkie

        # Synchronizuj przycisk "Nowa sesja" ze stanem grup
        self.gm.subscribe(self._update_add_btn)
        self._update_add_btn()

    # ---- sesje ----
    def _update_add_btn(self):
        world = self._selected_world
        if not self.gm.group_names(world):
            self.add_btn.configure(state="disabled")
            return
        group = self._group_filter or self.gm.first_group(world)
        count = sum(1 for s in self._sessions
                    if self.gm.world_of_session(s.session_id) == world
                    and self.gm.group_of(s.session_id) == group)
        self.add_btn.configure(state="disabled" if count >= self.MAX_PER_GROUP else "normal")

    def _add_session(self, group: str = None, name: str = None, world: str = None):
        world = world or self._selected_world
        if not self.gm.group_names(world):
            tk.messagebox.showwarning(
                "Brak grupy",
                "Utwórz najpierw grupę, a następnie dodaj sesję.\n"
                "Profil przeglądarki jest tworzony w katalogu grupy — "
                "bez grupy template nie zostanie poprawnie skopiowany.",
                parent=self.root,
            )
            return
        target_group = group or self._group_filter or self.gm.first_group(world)
        count = sum(1 for s in self._sessions
                    if self.gm.world_of_session(s.session_id) == world
                    and self.gm.group_of(s.session_id) == target_group)
        if count >= self.MAX_PER_GROUP:
            return

        if name is None:
            prefix = f"{target_group}_"
            used = set()
            for s in self._sessions:
                if (self.gm.world_of_session(s.session_id) == world
                        and self.gm.group_of(s.session_id) == target_group
                        and s.name.startswith(prefix)):
                    try:
                        used.add(int(s.name[len(prefix):]))
                    except ValueError:
                        pass
            idx = 1
            while idx in used:
                idx += 1
            name = f"{target_group}_{idx:02d}"

        self._session_counter += 1
        sid = self._session_counter

        tab = SessionTab(
            self.notebook, sid,
            self._config_map,
            self.gm,
            name=name,
            on_status_change=self._on_session_status,
            on_config_added=self._on_config_added,
            on_config_refresh=self._on_config_refresh,
            get_all_sessions_fn=lambda: self._sessions,
            on_banned=self._on_banned,
        )
        self._sessions.append(tab)

        target = group or self._group_filter or self.gm.first_group(world)
        self.gm.assign(sid, target, world)

        self.notebook.add(tab, text=self._tab_text(tab))

        # Hide immediately if doesn't match current world/filter
        sid_world = self.gm.world_of_session(sid)
        if sid_world != self._selected_world or \
                (self._group_filter is not None and self.gm.group_of(sid) != self._group_filter):
            try:
                self.notebook.tab(tab, state="hidden")
            except Exception:
                pass
        else:
            self.notebook.select(tab)

        tk.Button(tab, text="✕ Zamknij",
                  command=lambda t=tab: self._remove_session(t),
                  bg=BG, fg=FG_DIM, relief="flat", cursor="hand2",
                  font=FONT_SMALL).place(relx=1.0, x=-6, y=6, anchor="ne")

        self._update_add_btn()
        self._update_statusbar()
        return tab

    def _remove_session(self, tab: SessionTab):
        tab.stop_all()
        tab.logger.close()
        self.gm.remove_session(tab.session_id)
        self._sessions.remove(tab)
        self.notebook.forget(tab)
        tab.destroy()
        self._refresh_tab_texts()
        self._update_add_btn()
        self._update_statusbar()

    def _stop_all(self):
        for s in self._sessions:
            s._on_stop()

    def _tab_text(self, tab) -> str:
        icons = {"RUNNING": "▶", "STOPPING": "◼", "OFFLINE": "○", "ERROR": "✕"}
        if tab.status == "OFFLINE" and tab.is_banned():
            return f"⛔ {tab.name}"
        return f"{icons.get(tab.status, '○')} {tab.name}"

    def _on_banned(self, tab):
        """Sesja wykryła zablokowane konto: dopisek „(zablokowane)” na listach configów, ⛔ na zakładce, zapis na serwer."""
        for s in self._sessions:
            s._refresh_config_cb()
        self._refresh_tab_texts()
        self._save_state()

    def _banned_sessions(self) -> list:
        return [s for s in self._sessions if not s.is_running and s.is_banned()]

    def delete_banned(self) -> int:
        """Usuwa wszystkie (zatrzymane) sesje z configiem zablokowanego konta; configi zostają z oznaczeniem."""
        tabs = self._banned_sessions()
        for t in tabs:
            self._remove_session(t)
        if tabs:
            self._save_state()
        return len(tabs)

    def _delete_banned_ui(self):
        tabs = self._banned_sessions()
        if not tabs:
            messagebox.showinfo("Zablokowane", "Brak sesji z zablokowanym kontem.", parent=self.root)
            return
        names = ", ".join(t.name for t in tabs[:15]) + (" …" if len(tabs) > 15 else "")
        if messagebox.askyesno("Usuń zablokowane", f"Usunąć {len(tabs)} sesji z zablokowanym kontem?\n{names}", parent=self.root):
            self.delete_banned()

    def _refresh_tab_texts(self):
        for tab in self._sessions:
            try:
                self.notebook.tab(tab, text=self._tab_text(tab))
            except Exception:
                pass

    def _filter_notebook(self, group_name):
        if not hasattr(self, "notebook"):
            return
        world = self._selected_world
        for tab in self._sessions:
            sid = tab.session_id
            in_world = self.gm.world_of_session(sid) == world
            in_group = group_name is None or self.gm.group_of(sid) == group_name
            show = in_world and in_group
            try:
                self.notebook.tab(tab, state="normal" if show else "hidden")
            except Exception:
                pass
        for tab in self._sessions:
            sid = tab.session_id
            in_world = self.gm.world_of_session(sid) == world
            in_group = group_name is None or self.gm.group_of(sid) == group_name
            if in_world and in_group:
                try:
                    self.notebook.select(tab)
                except Exception:
                    pass
                break

    def _on_group_filter(self, group_name):
        self._group_filter = group_name
        self._filter_notebook(group_name)
        if hasattr(self, "add_btn"):
            self._update_add_btn()

    def _on_world_changed(self, world: str):
        self._selected_world = world
        self._group_filter   = None
        self._filter_notebook(None)
        if hasattr(self, "add_btn"):
            self._update_add_btn()

    def _on_session_status(self, session_id: int, status: str):
        for tab in self._sessions:
            if tab.session_id == session_id:
                try:
                    self.notebook.tab(tab, text=self._tab_text(tab))
                except Exception:
                    pass
                break

        self.group_panel.update_session_status(session_id, status)
        self._update_statusbar()

    # ---- drag-and-drop zakładek ----

    def _on_tab_drag_start(self, event):
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
            self._drag_state = {"active": True, "src_idx": idx}
        except Exception:
            self._drag_state = {"active": False, "src_idx": None}

    def _on_tab_drag_motion(self, event):
        if not self._drag_state.get("active"):
            return
        try:
            self.notebook.configure(cursor="fleur")
        except Exception:
            pass

    def _on_tab_drag_end(self, event):
        if not self._drag_state.get("active"):
            return
        self._drag_state["active"] = False
        try:
            self.notebook.configure(cursor="")
        except Exception:
            pass
        src = self._drag_state.get("src_idx")
        if src is None:
            return
        try:
            dst = self.notebook.index(f"@{event.x},{event.y}")
        except Exception:
            return
        if src == dst:
            return
        self._move_tab(src, dst)

    def _move_tab(self, src_idx: int, dst_idx: int):
        n = len(self._sessions)
        if src_idx == dst_idx or not (0 <= src_idx < n) or not (0 <= dst_idx < n):
            return
        tab = self._sessions[src_idx]
        self.notebook.insert(dst_idx, tab)
        self._sessions.insert(dst_idx, self._sessions.pop(src_idx))
        self._save_state()

    def _on_tab_double_click(self, event):
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
            tab = self._sessions[idx] if idx < len(self._sessions) else None
            if tab:
                self._rename_session(tab)
        except Exception:
            pass

    def _on_tab_right_click(self, event):
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
        except Exception:
            return
        tab = self._sessions[idx] if idx < len(self._sessions) else None
        if tab is None:
            return
        menu = tk.Menu(self.root, tearoff=0, bg=BG2, fg=FG,
                       activebackground=BG3, activeforeground=ACCENT,
                       relief="flat", bd=0)
        menu.add_command(label="✏️  Zmień nazwę",
                         command=lambda: self._rename_session(tab))
        menu.add_separator()
        menu.add_command(label="✕  Zamknij sesję",
                         command=lambda: self._remove_session(tab))
        menu.tk_popup(event.x_root, event.y_root)

    def _rename_session(self, tab: SessionTab):
        new_name = simpledialog.askstring(
            "Zmień nazwę", "Nowa nazwa sesji (max 20 znaków):",
            initialvalue=tab.name, parent=self.root)
        if new_name is None:
            return
        new_name = new_name.strip()[:20]
        if not new_name:
            return
        tab.name = new_name
        try:
            self.notebook.tab(tab, text=self._tab_text(tab))
        except Exception:
            pass
        self._save_state()

    def _update_statusbar(self):
        running = sum(1 for s in self._sessions if s.status == "RUNNING")
        total   = len(self._sessions)
        groups  = len(self.gm.group_names())
        self.statusbar.configure(
            text=f"  Sesje: {total}   ▶ Aktywne: {running}   ○ Offline: {total-running}"
                 f"   |   Grupy: {groups}")

    def _on_config_added(self, filename: str, path: str):
        """Aktualizuj _config_map i odśwież combobox we wszystkich sesjach."""
        self._config_map[filename] = path
        for s in self._sessions:
            s._refresh_config_cb()

    def _on_config_refresh(self):
        """Wczytaj listę configów z dysku od nowa i odśwież combobox we wszystkich sesjach."""
        base = os.path.dirname(os.path.abspath(__file__))
        skip = {"discord.json"}
        config_dir = os.path.join(base, "config")
        configs = sorted([
            f for f in glob.glob(os.path.join(config_dir, "*.json"))
            if os.path.basename(f) not in skip
        ])
        # mutacja w miejscu — sesje trzymają referencję do tego samego słownika
        self._config_map.clear()
        self._config_map.update({os.path.basename(p): p for p in configs})
        for s in self._sessions:
            s._refresh_config_cb()

    def _on_template_added(self):
        """Odśwież dropdown template we wszystkich sesjach."""
        for s in self._sessions:
            s._refresh_template_cb()

    # ---- host w panelu WWW ----
    def _host_tick(self):
        from log_shipper import HOST
        try:
            HOST.snapshot = [{
                "uid": s.uid, "name": s.name or f"sesja {i + 1}", "group": self.gm.group_of(s.session_id),
                "group_world": self.gm.world_of_session(s.session_id),
                "world": s.server_var.get().lower(), "config": s.config_key(), "banned": s.is_banned(),
                "char": os.path.splitext(s.config_key())[0], "status": s.status, "program": s.effective_program(),
                "prof": PROF_LABEL.get(s.current_prof(), ""), "bot": s.bot_state,
                "server": s.server_var.get(), "browser": s.browser_var.get(), "template": s.template_var.get(),
                "prog_override": bool(s.prog_override_var.get()),
                "own_program": s.program_var.get() if s.prog_override_var.get() else "",
                "recreate": bool(s.recreate_var.get()), "restart_on_fail": bool(s.restart_on_fail_var.get()),
            } for i, s in enumerate(self._sessions)]
            if time.time() - getattr(self, "_screens_at", 0) > 60:
                self._screens_at, self._screens_cache = time.time(), _screens()
            HOST.options = {
                "groups": [dict({"name": n, "world": w, "program": self.gm.program_of(n, w)},
                                **{f"layout_{k}": v for k, v in self.gm.layout_of(n, w).items()}) for (w, n) in self.gm._groups],
                "configs": sorted(self._config_map),
                "config_profs": [{"name": c, "prof": config_prof(p), "banned": config_banned(p)} for c, p in sorted(self._config_map.items())],
                "screens": [{"name": f"{i + 1}. {x['name']} – {x['w']}×{x['h']}"} for i, x in enumerate(getattr(self, "_screens_cache", []))],
                "zooms": ZOOM_CHOICES,
                "worlds": WORLDS,
                "servers": SERVERS, "browsers": BROWSERS,
                "templates": {b: _list_templates(b) for b in BROWSERS},
                "programs": _list_programs(),
                "professions": [{"name": k, "world": l} for k, l in PROFESSIONS],
            }
            while True:
                try:
                    c = HOST.commands.get_nowait()
                except Exception:
                    break
                self._run_command(c)
            # Zmienione ustawienia → serwer (co 2 min sprawdzamy, czy coś się zmieniło).
            if time.time() - self._last_push_check > 120:
                self._last_push_check = time.time()
                if json.dumps(self._state(), sort_keys=True) != self._last_pushed:
                    self._save_state()
        except Exception as e:
            print(f"host: {e}")
        self.root.after(2000, self._host_tick)

    def _run_command(self, c: dict):
        from log_shipper import HOST
        p = c.get("params") or {}
        if c.get("action") == "create_config":
            try:
                if p.get("mode") == "manual":
                    if not p.get("login") or not p.get("password"):
                        return HOST.report(c["id"], False, "brak loginu lub hasła")
                    fname, path = create_manual_config(p.get("name", ""), p["login"], p["password"], p.get("prof", ""))
                    msg = f"utworzono {fname}"
                else:
                    fname, path, data = create_auto_config(p.get("prof", ""))
                    msg = f"utworzono {fname} (nick {data['nick']}, konto założy START sesji)"
                self._on_config_added(fname, path)
                self._save_state()
                return HOST.report(c["id"], True, msg)
            except Exception as e:
                return HOST.report(c["id"], False, str(e)[:200])
        if c.get("action") == "create_session":
            group, world = p.get("group", ""), p.get("world", "") or self._selected_world
            if group not in self.gm.group_names(world):
                return HOST.report(c["id"], False, f"brak grupy „{group}” ({world}) w launcherze")
            tab = self._add_session(group=group, name=(p.get("name") or None), world=world)
            if not tab:
                return HOST.report(c["id"], False, f"grupa „{group}” jest pełna")
            tab.apply_settings({k: v for k, v in {
                "config": p.get("config"), "server": p.get("server"), "browser": p.get("browser"),
                "template": p.get("template") or "(brak)", "group": group, "group_world": world,
                "program_override": bool(p.get("program")), "program": p.get("program", ""),
            }.items() if v is not None})
            self._save_state()
            tab.logger.write("🌐 Sesja utworzona z panelu WWW")
            return HOST.report(c["id"], True, f"utworzono „{tab.name}”")
        act = c.get("action")
        # ── grupy ──
        if act in ("create_group", "rename_group", "delete_group", "update_group"):
            g, w = (p.get("name") or "").strip(), p.get("world") or self._selected_world
            if act == "create_group":
                ok = bool(g) and self.gm.add_group(g, world=w)
                msg = f"grupa „{g}” utworzona" if ok else f"grupa „{g}” już istnieje albo pusta nazwa"
            elif act == "rename_group":
                new = (p.get("new") or "").strip()
                ok = self.gm.rename_group(g, new, w)
                msg = f"„{g}” → „{new}”" if ok else "nie można zmienić nazwy (zajęta?)"
            elif act == "delete_group":
                if any(s.is_running and self.gm.group_of(s.session_id) == g for s in self._sessions):
                    return HOST.report(c["id"], False, "w grupie działają sesje – zatrzymaj je")
                ok = self.gm.remove_group(g, w)
                msg = f"grupa „{g}” usunięta (sesje przeniesione)" if ok else "brak grupy"
            else:
                if g not in self.gm.group_names(w):
                    return HOST.report(c["id"], False, f"brak grupy „{g}”")
                if "program" in p:
                    self.gm.set_program(g, w, p.get("program") or "")
                lay = {k[7:]: v for k, v in p.items() if k.startswith("layout_")}
                if lay:
                    cur = self.gm.layout_of(g, w)
                    for k, v in lay.items():
                        if k == "enabled":
                            cur[k] = v in (True, "true", "1", "on")
                        elif k in ("screen", "cols", "rows"):
                            try:
                                cur[k] = max(0 if k == "screen" else 1, int(v))
                            except ValueError:
                                pass
                        elif k == "zoom" and v in ZOOM_CHOICES:
                            cur[k] = v
                    self.gm.set_layout(g, w, cur)
                ok, msg = True, f"grupa „{g}” zapisana"
            if ok:
                self._save_state()
            return HOST.report(c["id"], ok, msg)
        # ── profesja configu ──
        if act == "set_config_prof":
            path = self._config_map.get(p.get("config", ""))
            if not path:
                return HOST.report(c["id"], False, "brak configu")
            prof = p.get("prof", "")
            if prof not in PROF_LABEL:
                return HOST.report(c["id"], False, "nieznana profesja")
            set_config_prof(path, prof)
            for s in self._sessions:
                s._refresh_prof()
            self._save_state()
            return HOST.report(c["id"], True, f"{p.get('config')}: {PROF_LABEL[prof]}")
        if act == "delete_banned":
            n = self.delete_banned()
            return HOST.report(c["id"], True, f"usunięto {n} sesji z zablokowanym kontem" if n else "brak sesji z zablokowanym kontem")
        tab = next((s for s in self._sessions if s.uid == c.get("session")), None)
        name = c.get("session_name") or c.get("session")
        if not tab:
            return HOST.report(c["id"], False, f"brak sesji „{name}” w launcherze")
        if c.get("action") == "start":
            if tab.is_running:
                return HOST.report(c["id"], True, "już działa")
            if tab.is_banned():
                return HOST.report(c["id"], False, "konto zablokowane – sesja nie wystartuje")
            tab.logger.write("🌐 START z panelu WWW")
            tab._on_play()
            return HOST.report(c["id"], tab.is_running, "uruchomiona" if tab.is_running else "nie wystartowała (config?)")
        if c.get("action") == "stop":
            if not tab.is_running:
                return HOST.report(c["id"], True, "już zatrzymana")
            tab.logger.write("🌐 STOP z panelu WWW")
            tab._on_stop()
            return HOST.report(c["id"], True, "zatrzymywana")
        if act in ("bot_start", "bot_stop"):
            tab.logger.write(f"🌐 {'▶ Start' if act == 'bot_start' else '⏸ Zatrzymanie'} bota z panelu WWW")
            tab.bot_command(act, lambda ok, msg, cid=c["id"]: HOST.report(cid, ok, msg))
            return
        if act == "update_session":
            if tab.is_running and any(k in p for k in ("config", "browser", "group", "template")):
                return HOST.report(c["id"], False, "zatrzymaj sesję, żeby zmienić config, grupę, przeglądarkę lub szablon")
            boolv = lambda v: v in (True, "true", "1", "on")
            d = {}
            for k in ("name", "config", "server", "browser", "template"):
                if p.get(k) not in (None, ""):
                    d[k] = p[k]
            for k in ("recreate", "restart_on_fail"):
                if k in p:
                    d[k] = boolv(p[k])
            if "prog_override" in p:
                d["program_override"] = boolv(p["prog_override"])
                d["program"] = p.get("program", "") if d["program_override"] else ""
                if not d["program_override"]:
                    tab.prog_override_var.set(False)
            # bez grupy w danych apply_settings przeniósłby sesję do pierwszej grupy – zostaje bieżąca
            d["group"] = p.get("group") or self.gm.group_of(tab.session_id)
            d["group_world"] = p.get("group_world") or self.gm.world_of_session(tab.session_id)
            tab.apply_settings(d)
            tab._refresh_prof()
            tab._refresh_program_row()
            self._refresh_tab_texts()
            self._save_state()
            return HOST.report(c["id"], True, f"„{tab.name}” zapisana")
        if act == "delete_session":
            if tab.is_running:
                return HOST.report(c["id"], False, "zatrzymaj sesję przed usunięciem")
            self._remove_session(tab)
            self._save_state()
            return HOST.report(c["id"], True, f"„{name}” usunięta")
        HOST.report(c["id"], False, "nieznane polecenie")

    def _state(self) -> dict:
        return {"groups": self.gm.to_dict(), "sessions": [s.get_settings() for s in self._sessions],
                "schedules": self._schedules}

    # ---- harmonogram ----
    def _schedule_tick(self):
        import scheduler as S
        try:
            now = time.time()
            ran = False
            for e in list(self._schedules):
                if S.due(e, now):
                    e["last_run"] = now
                    if e["kind"] == "once":
                        e["enabled"] = False
                    self.run_schedule(e)
                    ran = True
            if ran:
                self._save_state()
        except Exception as ex:
            print(f"harmonogram: {ex}")
        self.root.after(15000, self._schedule_tick)

    def run_schedule(self, e: dict) -> str:
        """Wykonanie wpisu harmonogramu (o czasie albo „Uruchom teraz”); wynik trafia do dziennika i paska stanu."""
        import scheduler as S
        try:
            msg = self._do_schedule(e)
        except Exception as ex:
            msg = f"❌ {ex}"
        label = f"{S.ACTIONS.get(e['action'], e['action'])} · {S.describe_target(e)}"
        self._schedule_log.append((time.time(), label, msg))
        del self._schedule_log[:-50]
        self.statusbar.configure(text=f"  ⏰ {label}: {msg}")
        self.root.after(8000, self._update_statusbar)
        return msg

    def _do_schedule(self, e: dict) -> str:
        act, g, w = e["action"], e.get("group", ""), e.get("world") or self._selected_world
        if e["target"] == "session":
            tab = next((s for s in self._sessions if s.uid == e.get("session")), None)
            if not tab:
                return "brak sesji w launcherze"
            if act == "start":
                if tab.is_running:
                    return "już działa"
                if tab.is_banned():
                    return "konto zablokowane"
                tab.logger.write("⏰ START z harmonogramu")
                tab._on_play()
                return "uruchomiona" if tab.is_running else "nie wystartowała (log sesji)"
            if act == "stop":
                if not tab.is_running:
                    return "już zatrzymana"
                tab.logger.write("⏰ STOP z harmonogramu")
                tab._on_stop()
                return "zatrzymywana"
            return "nieznana akcja"
        if g not in self.gm.group_names(w):
            return f"brak grupy „{g}” ({w})"
        if act == "start":
            n = self.group_panel._start_group(g, w)
            return f"startuję {n} sesji" if n else "brak sesji do startu"
        if act == "stop":
            n = self.group_panel._stop_group(g, w)
            return f"zatrzymuję {n} sesji" if n else "nic nie działało"
        if act == "create_session":
            return self._schedule_create(e, g, w)
        return "nieznana akcja"

    def _group_count(self, g: str, w: str) -> int:
        return sum(1 for s in self._sessions
                   if self.gm.world_of_session(s.session_id) == w and self.gm.group_of(s.session_id) == g)

    def _schedule_create(self, e: dict, g: str, w: str) -> str:
        """Nowy config (konto do założenia przy START) + nowa sesja w grupie; ustawienia z wpisu,
        a puste – jak w ostatniej sesji grupy. Po zapełnieniu grupy wpis może się wyłączyć."""
        p = e.get("params") or {}
        if self._group_count(g, w) >= self.MAX_PER_GROUP:
            if p.get("disable_when_full", True):
                e["enabled"] = False
                return f"grupa pełna ({self.MAX_PER_GROUP}) – wpis wyłączony"
            return f"grupa pełna ({self.MAX_PER_GROUP})"
        last = next((s for s in reversed(self._sessions)
                     if self.gm.world_of_session(s.session_id) == w and self.gm.group_of(s.session_id) == g), None)
        base = last.get_settings() if last else {}
        prof = p.get("prof", "")
        if prof == PROF_RANDOM:
            import random
            prof = random.choice([k for k, _ in PROFESSIONS if k])
        name, path, data = create_auto_config(prof)
        self._on_config_added(name, path)
        tab = self._add_session(group=g, world=w)
        if not tab:
            return "nie udało się dodać sesji"
        server = p.get("server") or base.get("server") or (w if w in SERVERS else SERVERS[0])
        browser = p.get("browser") or base.get("browser") or BROWSERS[0]
        tab.apply_settings({
            "config": name, "server": server, "browser": browser,
            "template": p.get("template") or (base.get("template") if browser == base.get("browser") else "") or "(brak)",
            "group": g, "group_world": w,
            "program_override": bool(p.get("program")), "program": p.get("program", ""),
        })
        tab.logger.write(f"⏰ Sesja utworzona z harmonogramu – nowy config {name} (nick {data['nick']}"
                         + (f", profesja {PROF_LABEL[prof]}" if prof else "") + ")")
        if p.get("start", True):
            tab.after(800, tab._on_play)
        full = self._group_count(g, w) >= self.MAX_PER_GROUP
        if full and p.get("disable_when_full", True):
            e["enabled"] = False
        return (f"„{tab.name}” z configiem {name}" + (" – START" if p.get("start", True) else "")
                + (" · grupa pełna, wpis wyłączony" if full and p.get("disable_when_full", True) else ""))

    def _configs_for_sync(self) -> dict:
        out = {}
        for name, path in self._config_map.items():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    out[name] = json.load(f)
            except Exception:
                pass
        return out

    def restore_from_server(self, data: dict) -> str:
        """Odtwarza ustawienia zapisane na serwerze: configi kont, grupy i sesje (bez działających sesji)."""
        if any(s.is_running for s in self._sessions):
            return "Zatrzymaj najpierw wszystkie sesje."
        base = os.path.dirname(os.path.abspath(__file__))
        cdir = os.path.join(base, "config")
        os.makedirs(cdir, exist_ok=True)
        n = 0
        for name, content in (data.get("configs") or {}).items():
            fn = os.path.basename(str(name))
            if not fn.endswith(".json") or fn in ("discord.json",) or not isinstance(content, dict):
                continue
            tmp = os.path.join(cdir, fn + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            os.replace(tmp, os.path.join(cdir, fn))
            n += 1
        state = data.get("state") or {}
        with open(self._state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        for tab in list(self._sessions):
            self._remove_session(tab)
        for (w, gname) in list(self.gm._groups):
            self.gm._groups.pop((w, gname), None)
        self.gm._favorites.clear()
        self._on_config_refresh()
        self._load_state()
        self.gm._notify()
        self._last_pushed = json.dumps(self._state(), sort_keys=True)
        return f"Odtworzono: {n} configów, {len(state.get('groups') or [])} grup, {len(state.get('sessions') or [])} sesji."

    # ---- persystencja stanu ----
    def _save_state(self):
        state = self._state()
        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        # Kopia ustawień i configów na serwerze (⚙️ Ustawienia › Odtwórz z serwera na innym komputerze).
        try:
            from log_shipper import HOST
            HOST.push_state(state, self._configs_for_sync())
            self._last_pushed = json.dumps(state, sort_keys=True)
        except Exception:
            pass

    def _load_state(self):
        if not os.path.isfile(self._state_file):
            return
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            return

        import scheduler as S
        self._schedules = [S.normalize(e) for e in (state.get("schedules") or []) if isinstance(e, dict)]

        # odtwórz grupy
        for g in state.get("groups", []):
            name  = g.get("name", "")
            color = g.get("color", "")
            world = g.get("world", "Gordion")
            if name and (world, name) not in self.gm._groups:
                self.gm._add_group(name, color, world)
            if name and g.get("layout"):
                self.gm._groups[(world, name)]["layout"] = dict(LAYOUT_DEFAULT, **g["layout"])
            if name and g.get("program"):
                self.gm._groups[(world, name)]["program"] = g["program"]
            if g.get("favorite"):
                self.gm._favorites.add((world, name))

        # odtwórz sesje (tylko gdy istnieją grupy)
        if not self.gm.group_names():
            return
        for d in state.get("sessions", []):
            s_world = d.get("group_world", WORLDS[0])
            self._add_session(name=d.get("name") or "sesja", world=s_world)
            self._sessions[-1].apply_settings(d)

    def _on_save(self):
        self._save_state()
        self.statusbar.configure(text="✅ Stan zapisany")
        self.root.after(3000, lambda: self._update_statusbar())

    def on_close(self):
        self._save_state()
        for s in self._sessions:
            s.stop_all()
            s.logger.close()
        self._cleanup_lock_files()
        self.root.destroy()

    def _cleanup_lock_files(self):
        base = os.path.dirname(os.path.abspath(__file__))
        removed = 0
        for subdir in ("config",):
            d = os.path.join(base, subdir)
            if not os.path.isdir(d):
                continue
            for entry in os.listdir(d):
                if entry.endswith(".lock"):
                    try:
                        os.remove(os.path.join(d, entry))
                        removed += 1
                    except Exception:
                        pass
        if removed:
            print(f"🧹 Usunięto {removed} plików .lock przy zamknięciu")


# ============================================
# ENTRY POINT
# ============================================
def _build_header_image(bg_hex: str, height: int = HEADER_H):
    """
    Wczytuje top_label.png, wycina czarne pasy góra/dół,
    skaluje do stałej wysokości `height`, nakłada fade od 3/4 szerokości
    do prawej krawędzi w kierunku koloru okna bg_hex.
    Zwraca (ImageTk.PhotoImage, szerokość) lub (None, 0).
    """
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "styles", "top_label.png")
    try:
        from PIL import Image as _PILImage, ImageTk as _ImageTk

        img = _PILImage.open(path).convert("RGBA")
        w, h = img.size
        px = img.load()

        # --- wycinanie czarnych pasów ---
        top_cut = 0
        for y in range(h):
            found = False
            for x in range(0, w, 80):
                r, g, b, *_ = px[x, y]
                if r > 12 or g > 12 or b > 12:
                    top_cut = y
                    found = True
                    break
            if found:
                break

        bot_cut = h - 1
        for y in range(h - 1, -1, -1):
            found = False
            for x in range(0, w, 80):
                r, g, b, *_ = px[x, y]
                if r > 12 or g > 12 or b > 12:
                    bot_cut = y
                    found = True
                    break
            if found:
                break

        img = img.crop((0, top_cut, w, bot_cut + 1))
        cw, ch = img.size

        # --- skalowanie do stałej wysokości ---
        new_w = int(cw * height / ch)
        img = img.resize((new_w, height), _PILImage.LANCZOS)

        # --- fade overlay: przezroczysty do 3/4, potem ramp do bg_hex ---
        br = int(bg_hex[1:3], 16)
        bg_g = int(bg_hex[3:5], 16)
        bb = int(bg_hex[5:7], 16)

        overlay = _PILImage.new("RGBA", (new_w, height), (0, 0, 0, 0))
        ovx = overlay.load()
        fade_start = int(new_w * 0.75)
        fade_len   = max(new_w - fade_start - 1, 1)
        for x in range(fade_start, new_w):
            a = int(255 * (x - fade_start) / fade_len)
            for y in range(height):
                ovx[x, y] = (br, bg_g, bb, a)

        result = _PILImage.alpha_composite(img, overlay)
        photo  = _ImageTk.PhotoImage(result)
        return photo, new_w
    except Exception as e:
        _sys.__stderr__.write(f"[header_img] {e}\n")
        return None, 0


def _load_app_icon(root: tk.Tk) -> "tk.PhotoImage | None":
    base = os.path.dirname(os.path.abspath(__file__))
    icns_path = os.path.join(base, "styles", "icon.icns")
    png_path  = os.path.join(base, "styles", "icon.png")
    try:
        from PIL import Image, ImageDraw, ImageTk
        if os.path.isfile(icns_path):
            # .icns ma już wbudowane zaokrąglone rogi i przezroczystość
            img = Image.open(icns_path).convert("RGBA").resize((256, 256), Image.LANCZOS)
        elif os.path.isfile(png_path):
            size = 256
            img = Image.open(png_path).convert("RGBA").resize((size, size), Image.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([0, 0, size - 1, size - 1],
                                   radius=int(size * 0.2237), fill=255)
            img.putalpha(mask)
        else:
            raise FileNotFoundError("brak icon.icns i icon.png")
        photo = ImageTk.PhotoImage(img)
        root._app_icon_ref = photo
        return photo
    except ImportError:
        pass
    except Exception:
        pass
    # fallback: zwykły PhotoImage z PNG (bez zaokrągleń)
    try:
        img = tk.PhotoImage(file=png_path)
        img = img.subsample(32, 32)
        return img
    except Exception:
        return None


def _set_dock_icon():
    """Ustawia ikonę w Docku macOS przez PyObjC (NSApplication)."""
    base = os.path.dirname(os.path.abspath(__file__))
    icns_path = os.path.join(base, "styles", "icon.icns")
    png_path  = os.path.join(base, "styles", "icon.png")
    path = icns_path if os.path.isfile(icns_path) else png_path
    if not os.path.isfile(path):
        return
    try:
        from AppKit import NSApplication, NSImage
        ns_img = NSImage.alloc().initWithContentsOfFile_(path)
        if ns_img:
            NSApplication.sharedApplication().setApplicationIconImage_(ns_img)
    except Exception:
        pass


def main():
    root = tk.Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.after(100, lambda: root.attributes("-topmost", False))
    root.focus_force()

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TCombobox",
                     fieldbackground=BG3, background=BG3,
                     foreground=FG, selectbackground=BG3,
                     selectforeground=FG, bordercolor=BORDER,
                     arrowcolor=ACCENT, relief="flat")
    style.map("TCombobox",
              fieldbackground=[("readonly", BG3)],
              foreground=[("readonly", FG)])

    _icon = _load_app_icon(root)
    if _icon:
        root.iconphoto(True, _icon)
    _set_dock_icon()

    app = BotGUI(root, app_icon=_icon)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()