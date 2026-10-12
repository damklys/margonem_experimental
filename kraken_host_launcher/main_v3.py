import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import threading
import time
import os
import re
import shutil
import json
import glob
import queue
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

FONT_MONO  = ("Courier New", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_GRP   = ("Segoe UI", 9, "bold")

MODES = ["exp", "heros", "kopalnia", "e2", "dobijarka", "kolos", "otchlan", "playbook", "none", "elite"]

STATUS_COLORS = {
    "OFFLINE":  FG_DIM,
    "RUNNING":  GREEN,
    "PAUSED":   VIOLET,
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

BROWSER_BINARY = {
    "Brave": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
}
_DETECTED_BROWSER_VERSION_CACHE = {}

def _detect_browser_major_version(browser: str) -> int | None:
    """Odczytuje aktualną wersję główną (major) zainstalowanej przeglądarki.

    Chrome/Brave aktualizują się automatycznie w tle, więc wersja nie może
    być na sztywno wpisana w kodzie (patrz: BROWSER_VERSION niżej) - robiła
    się nieaktualna i powodowała błąd "session not created" w ChromeDriverze.
    """
    if browser in _DETECTED_BROWSER_VERSION_CACHE:
        return _DETECTED_BROWSER_VERSION_CACHE[browser]

    binary = BROWSER_BINARY.get(browser)
    if not binary:
        try:
            import undetected_chromedriver as uc
            binary = uc.find_chrome_executable()
        except Exception:
            binary = None

    version = None
    if binary and os.path.exists(binary):
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
    group_safe = group.replace(" ", "_") if group else "default"
    d = os.path.join(base, "profiles", "groups", group_safe, profile_name)
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
        self._open_file()

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


def _auto_select_exp(base_dir: str, level: int):
    """Return (name, path) of a suitable, unlocked exp location or None."""
    exp_dir = os.path.join(base_dir, "exp")
    if not os.path.isdir(exp_dir):
        return None
    for name in sorted(os.listdir(exp_dir)):
        path = os.path.join(exp_dir, name, "route.json")
        if not os.path.isfile(path):
            continue
        if os.path.exists(os.path.join(exp_dir, f"{name}.lock")):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("min_lvl", 0) <= level <= data.get("max_lvl", 999):
                return name, path
        except Exception:
            continue
    return None


# ============================================
# BOT RUNNER
# ============================================
class BotRunner:
    def __init__(self, config: dict,
                 pause_event: threading.Event,
                 stop_event: threading.Event,
                 logger: SessionLogger):
        self.config          = config
        self.pause_event     = pause_event
        self.stop_event      = stop_event
        self.logger          = logger
        self.driver          = None
        self.browser_pid: "int | None" = None
        self.navigate_queue  = queue.Queue()
        self._exp_lock_path    = None
        self._config_lock_path = None
        self.pause_callback: "callable | None" = None
        self.login_done_event  = threading.Event()   # sygnał: logowanie zakończone

    def log(self, msg):
        self.logger.write(msg)

    def pause_check(self):
        while not self.pause_event.is_set():
            if self.stop_event.is_set():
                raise StopIteration("Bot zatrzymany.")
            time.sleep(0.2)
        if self.stop_event.is_set():
            raise StopIteration("Bot zatrzymany.")

    def stop_check(self):
        if self.stop_event.is_set():
            raise StopIteration("Bot zatrzymany.")

    def _collect_event_rewards(self):
        """Otwiera Kalendarz, odbiera dostępne nagrody eventu i zamyka okno."""
        from selenium.webdriver.common.by import By

        drv = self.driver

        def _calendar_visible() -> bool:
            try:
                el = drv.find_element(By.CSS_SELECTOR, "div.rewards-calendar")
                return el.is_displayed()
            except Exception:
                return False

        self.log("🎁 Event: otwieram Kalendarz…")

        # Klikaj przycisk co 2s aż okno się pojawi (max 30s)
        # Nie przerywaj gdy przycisk chwilowo niedostępny — gra ładuje widgety po logowaniu
        _CAL_SELECTORS = (
            "div.widget-rewards-calendar-icon",
            "div.widget-calendar-icon",
            "[class*='rewards-calendar-icon']",
            "[class*='calendar-icon']",
        )
        t0 = time.time()
        opened = False
        while time.time() - t0 < 30:
            if _calendar_visible():
                opened = True
                break
            clicked = False
            for sel in _CAL_SELECTORS:
                try:
                    btn = drv.find_element(By.CSS_SELECTOR, sel)
                    if btn.is_displayed():
                        drv.execute_script("arguments[0].click();", btn)
                        clicked = True
                        break
                except Exception:
                    pass
            if not clicked:
                self.log("⏳ Event: czekam na widget Kalendarza…")
            time.sleep(2.0)

        if not opened:
            self.log("⚠️  Event: Kalendarz nie otworzył się po 30s — pomijam")
            return

        self.log("📅 Event: Kalendarz otwarty")
        time.sleep(0.5)

        # Zbierz dostępne nagrody — re-query po każdym kliknięciu bo DOM się zmienia.
        # Nagroda do odebrania: .reward gdzie child .item-wrapper NIE ma klasy "lock".
        # Nagroda zablokowana:  .reward gdzie child .item-wrapper MA klasę "lock" → pomijamy.
        collected = 0
        for _ in range(50):
            rew = None
            try:
                for el in drv.find_elements(By.CSS_SELECTOR, ".rewards-calendar .reward"):
                    try:
                        wrapper = el.find_element(By.CSS_SELECTOR, ".item-wrapper")
                        if "lock" in (wrapper.get_attribute("class") or ""):
                            continue  # kłódka — pomiń
                        if el.is_displayed():
                            rew = el
                            break
                    except Exception:
                        continue
            except Exception as e:
                self.log(f"⚠️  Event: błąd skanowania nagród — {e}")
                break

            if rew is None:
                break

            try:
                drv.execute_script("arguments[0].click();", rew)
                collected += 1
                self.log(f"🎁 Event: odebrałem nagrodę #{collected}")
                time.sleep(0.8)
                # Zamknij ewentualne popup potwierdzenia nagrody
                for sel in (
                    ".reward-popup .close",
                    ".popup-window .close-button",
                    ".c-window .close-button-corner-decor .close-button",
                    "div.button.close",
                ):
                    try:
                        cb = drv.find_element(By.CSS_SELECTOR, sel)
                        if cb.is_displayed():
                            drv.execute_script("arguments[0].click();", cb)
                            time.sleep(0.4)
                            break
                    except Exception:
                        pass
            except Exception as e:
                self.log(f"⚠️  Event: błąd klikania nagrody — {e}")
                break

        if collected == 0:
            self.log("ℹ️  Event: brak dostępnych nagród do odebrania")

        # Zamknij okno Kalendarza — znajdź .c-window zawierające .rewards-calendar przez JS
        time.sleep(0.3)
        try:
            close_btn = drv.execute_script("""
                var cal = document.querySelector('div.rewards-calendar');
                if (!cal) return null;
                var win = cal.closest('div.c-window');
                if (!win) return null;
                return win.querySelector('.close-button-corner-decor .close-button');
            """)
            if close_btn:
                drv.execute_script("arguments[0].click();", close_btn)
            else:
                raise RuntimeError("close_btn not found via JS")
        except Exception as e:
            self.log(f"⚠️  Event: błąd szukania przycisku zamknięcia — {e}")
            return

        # Zweryfikuj że okno faktycznie zniknęło (max 5s)
        t0 = time.time()
        while time.time() - t0 < 5:
            if not _calendar_visible():
                self.log("✅ Event: Kalendarz zamknięty")
                return
            time.sleep(0.3)

        self.log("⚠️  Event: Kalendarz nadal widoczny po kliknięciu zamknięcia")

    def run(self):
        self.crashed = False
        _THREAD_STREAM.set_logger(self.logger)
        try:
            self._run_bot()
        except StopIteration as e:
            self.log(f"⛔ {e}")
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
            if self._exp_lock_path and os.path.exists(self._exp_lock_path):
                try:
                    os.remove(self._exp_lock_path)
                    self.log("🔓 Zwolniono lock ekspowiska.")
                except Exception:
                    pass
            if self.driver:
                try:
                    self.driver.quit()
                    self.log("🔒 Przeglądarka zamknięta.")
                except Exception:
                    pass

    def _run_bot(self):
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import StaleElementReferenceException
        from login import login
        from enable_map import enable_map
        from kill_object import kill_object
        from battle_handler import check_and_handle_battle
        from get_near_e2 import get_near_e2
        from create_profile import create_profile
        from kill_e2 import kill_e2
        from move import move_to_next_map, travel_to, _get_location_text, _load_config, get_character_level
        from get_near_object import get_near_object, wait_for_mob
        from captcha import check_and_solve_captcha
        from discord_webhook import DiscordWebhook
        from anti_afk import check_interrupts
        from find_heros import find_nearest_heros_resp, find_heros_on_map, click_heros_resp
        from select_heros import load_heros_route
        from kill_heros import kill_heros
        from move_heros import click_gw
        from kolos_mode import run_kolos_leader, run_kolos_follower
        from e2_mode import run_e2

        def _is_game_loaded():
            return bool(self.driver.find_elements(By.CSS_SELECTOR, "canvas#GAME_CANVAS"))

        def _wait_for_game_canvas(timeout: float = 60.0) -> bool:
            t0 = time.time()
            while time.time() - t0 < timeout:
                if _is_game_loaded():
                    return True
                time.sleep(1)
            return False

        def _refresh_and_wait():
            self.log("🔄 Odświeżam stronę (brak minimapy / canvas)...")
            self.driver.refresh()
            if _wait_for_game_canvas(60.0):
                self.log("✅ Gra załadowana po odświeżeniu")
            else:
                self.log("⚠️  Gra nadal niedostępna po odświeżeniu")

        cfg              = self.config
        FARM_MODE        = cfg["mode"]
        config_path      = cfg["config_path"]
        delay            = cfg["delay"]
        exp_route        = cfg.get("exp_route_path")
        heros_json       = cfg.get("heros_json_path")
        no_attack        = cfg.get("no_attack", False)
        auto_exp         = cfg.get("auto_exp", False)
        kolos_cfg_path   = cfg.get("kolos_config_path")
        kolos_is_leader  = cfg.get("kolos_is_leader", False)

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

        options = uc.ChromeOptions()
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir={profile_path}")
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
        # "none": driver.get() wraca natychmiast, ChromeDriver nie blokuje
        # find_element z powodu trwającej nawigacji
        options.page_load_strategy = "none"
        if browser in BROWSER_BINARY:
            options.binary_location = BROWSER_BINARY[browser]

        server     = cfg.get("server", "")
        server_url = SERVER_URL.get(server, "")

        self.driver = uc.Chrome(options=options,
                                 version_main=_detect_browser_major_version(browser) or BROWSER_VERSION.get(browser, 148),
                                 driver_executable_path=None)
        try:
            self.browser_pid = self.driver.service.process.pid
            self.log(f"🔢 PID: {self.browser_pid}")
        except Exception:
            self.browser_pid = None

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        credentials = config_data["login"][0]

        self.pause_check()

        import login as _login_mod
        if profile_existed and not recreate and server_url:
            # Profil istnieje — wejdź bezpośrednio na serwer, pomijając logowanie
            self.log(f"⚡ Istniejący profil — wchodzę na {server_url}")
            self.driver.get(server_url)
            _login_mod._LOGIN_STARTED.release()
            # Czekaj na canvas#GAME_CANVAS (z obsługą captchy)
            t0 = time.time()
            _canvas_ok = False
            while time.time() - t0 < 60:
                check_and_solve_captcha(self.driver)
                if self.driver.find_elements(By.CSS_SELECTOR, "canvas#GAME_CANVAS"):
                    self.log("✅ Gra załadowana bezpośrednio")
                    _canvas_ok = True
                    break
                time.sleep(0.5)
            if _canvas_ok:
                _login_mod._LOGIN_DONE.release()
            else:
                self.log("⚠️  Bezpośrednie wejście nieudane – pełne logowanie")
                self.driver.get("https://margonem.pl")
                login(driver=self.driver,
                      username=credentials["username"],
                      password=credentials["password"])
        else:
            self.driver.get("https://margonem.pl")
            login(driver=self.driver,
                  username=credentials["username"],
                  password=credentials["password"])

        self.login_done_event.set()   # sygnał dla stream_worker: logowanie skończone
        self.log(f"⏳ Czekam {delay}s po logowaniu...")
        for _ in range(delay):
            time.sleep(1)
            self.stop_check()

        check_and_solve_captcha(self.driver)

        if cfg.get("event_rewards", False):
            self._collect_event_rewards()

        discord  = DiscordWebhook()

        while True:
            self.pause_check()
            try:

                # --- Detekcja walki PvP/PvE (pomijana w trybie none) ---
                if self.config.get("mode", "none") != "none":
                    _cfg_actions = self.config.get("actions") or self.config.get("action") or []
                    _battle = check_and_handle_battle(
                        self.driver, self.log, self.stop_event, actions=_cfg_actions or None)
                    if _battle == "stopped":
                        raise StopIteration("Bot zatrzymany.")
                    if _battle == "dead":
                        # Resetuj stan trasy — bot sam dotrze z powrotem na ekspowisko/e2/heros
                        self.driver._active_exp_route  = None
                        self.driver._move_seq_idx      = 0
                        self.driver._map_first_check   = False
                        self.driver._active_heros_json = None
                        self.driver._battle_first_seen = None
                        self.log("🔄 Restart trasy po śmierci...")
                        continue

                # --- Globalne sprawdzenie max poziomu ---
                if self.config.get("max_lvl_enabled") and self.config.get("max_lvl"):
                    _now = time.time()
                    if _now - getattr(self, "_last_lvl_check", 0) >= 60:
                        self._last_lvl_check = _now
                        _cur_lvl = get_character_level(self.driver)
                        _max_lvl = self.config["max_lvl"]
                        if _cur_lvl is not None and _cur_lvl >= _max_lvl:
                            self.log(f"🎉 Osiągnięto poziom {_cur_lvl} (max: {_max_lvl}) — pauza")
                            cur = self.config.get("mode", "none")
                            if cur != "none":
                                self.config["_saved_mode"] = cur
                            self.config["mode"] = "none"
                            if self.pause_callback:
                                self.pause_callback()

                FARM_MODE  = self.config["mode"]
                auto_exp   = self.config.get("auto_exp", False)
                heros_json = self.config.get("heros_json_path")

                # Dispatcher: polecenie nawigacji do mapy
                try:
                    nav_target = self.navigate_queue.get_nowait()
                    self.log(f"🗺️  Dyspozytor: nawiguję do '{nav_target}'")
                    ok = travel_to(self.driver, nav_target, stop_event=self.stop_event)
                    self.log(f"✅ Dotarłem do '{nav_target}'" if ok else f"❌ Nie dotarłem do '{nav_target}'")
                    self.stop_check()
                    continue
                except queue.Empty:
                    pass

                # Captcha + stasis — zawsze aktywne niezależnie od ustawień
                check_interrupts(self.driver, logger=self.log)

                if FARM_MODE == "none":
                    # Tylko logowanie — czekaj w pętli
                    check_and_solve_captcha(self.driver)
                    time.sleep(5)

                elif FARM_MODE == "exp":
                    check_and_solve_captcha(self.driver)
                    try:
                        enable_map(self.driver, enabled=True)
                    except Exception:
                        if not _is_game_loaded():
                            _refresh_and_wait()
                        else:
                            self.log("⚠️  enable_map błąd – retry za 3s")
                        time.sleep(3)
                        continue

                    # Auto-dobór ekspowiska na podstawie poziomu postaci
                    if auto_exp and self.config.get("exp_route_path") is None:
                        level = get_character_level(self.driver)
                        if level is None:
                            self.log("⚠️  Auto EXP: nie udało się odczytać poziomu – retry za 5s")
                            time.sleep(5)
                            continue
                        self.log(f"📊 Auto EXP: poziom postaci = {level}")
                        chosen = _auto_select_exp(base_dir, level)
                        if chosen is None:
                            self.log("⚠️  Auto EXP: brak wolnej lokacji dla tego poziomu – retry za 10s")
                            time.sleep(10)
                            continue
                        exp_name, exp_path = chosen
                        self.config["exp_route_path"] = exp_path
                        self.log(f"🎯 Auto EXP: wybrano '{exp_name}' (lvl {level})")


                    exp_route = self.config.get("exp_route_path")
                    if exp_route != getattr(self.driver, "_active_exp_route", None):
                        # Zwolnij stary lock przed przejściem na nową trasę
                        if self._exp_lock_path and os.path.exists(self._exp_lock_path):
                            try:
                                os.remove(self._exp_lock_path)
                            except Exception:
                                pass
                        self.driver._active_exp_route = exp_route
                        self.driver._move_seq_idx = 0
                        self._last_lvl_check = 0
                        # Utwórz lock dla nowej lokacji
                        exp_name = os.path.basename(os.path.dirname(exp_route))
                        self._exp_lock_path = os.path.join(base_dir, "exp", f"{exp_name}.lock")
                        try:
                            open(self._exp_lock_path, "w").close()
                            self.log(f"🔒 Lock: {exp_name}")
                        except Exception:
                            pass
                        _exp_steps = _load_config(exp_route)
                        self.driver._exp_steps_cache = _exp_steps or []
                        if _exp_steps:
                            _first_map = _exp_steps[0].get("location", "")
                            if _first_map and _get_location_text(self.driver) != _first_map:
                                self.log(f"🗺️  EXP: nawiguję do startowej mapy: {_first_map}")
                                if not travel_to(self.driver, _first_map, stop_event=self.stop_event):
                                    self.log(f"❌ Nie udało się dotrzeć do {_first_map} – retry")
                                    time.sleep(3)
                                    continue
                                self.log(f"✅ Dotarłem do: {_first_map}")

                    # Odczytaj parametry aktualnego kroku trasy
                    _steps  = getattr(self.driver, "_exp_steps_cache", [])
                    _sidx   = getattr(self.driver, "_move_seq_idx", 0)
                    _step   = _steps[_sidx % len(_steps)] if _steps else {}
                    _attack = _step.get("attack", True)
                    _excl   = _step.get("excluded_mobs", [])
                    if _excl:
                        self.log(f"[DEBUG] krok={_sidx} lokacja={_step.get('location')} excl={_excl}")

                    # Wykryj zmianę mapy — resetuj stan i ustaw flagę pierwszego sprawdzenia
                    try:
                        _cur_map = _get_location_text(self.driver)
                    except Exception:
                        if not _is_game_loaded():
                            _refresh_and_wait()
                        time.sleep(2)
                        continue

                    # Sprawdź czy jesteśmy na właściwej mapie trasy (np. po śmierci lub wznowieniu)
                    _expected_map = _step.get("location", "")
                    if _expected_map and _cur_map != _expected_map:
                        # Sprawdź czy bieżąca mapa jest gdziekolwiek w trasie
                        _route_locs = [s.get("location", "") for s in _steps]
                        if _cur_map in _route_locs:
                            # Zsynchronizuj indeks do najbliższego pasującego kroku
                            _candidates = [i for i, loc in enumerate(_route_locs) if loc == _cur_map]
                            _n = len(_route_locs)
                            _best = min(_candidates, key=lambda i: (i - _sidx) % _n)
                            self.driver._move_seq_idx = _best
                            self.log(f"📍 Synchronizuję trasę: krok {_best} ('{_cur_map}')")
                        else:
                            # Mapa spoza trasy (np. miasto po śmierci) — wróć do pierwszego kroku
                            _first_map = _route_locs[0] if _route_locs else ""
                            _nav_target = _first_map or _expected_map
                            self.log(f"📍 Poza trasą: '{_cur_map}' → nawiguję do '{_nav_target}'...")
                            if travel_to(self.driver, _nav_target, stop_event=self.stop_event):
                                self.log(f"✅ Powrót na trasę: {_nav_target}")
                                self.driver._move_seq_idx = 0
                            else:
                                self.log(f"❌ Nie udało się wrócić do '{_nav_target}' – retry za 5s")
                                time.sleep(5)
                        continue

                    if _cur_map != getattr(self.driver, "_char_level_map", None):
                        self.driver._char_level_map = _cur_map
                        self.driver._char_level_cached = get_character_level(self.driver)
                        self.driver._ignored_tip_ids = set()
                        self.driver._map_first_check = True
                    _char_lvl      = getattr(self.driver, "_char_level_cached", None)
                    _ignored       = getattr(self.driver, "_ignored_tip_ids", set())
                    _first_check   = getattr(self.driver, "_map_first_check", False)

                    if not _attack:
                        self.log("⏩ Lokacja pośrednia – przechodzę dalej")
                        self.driver._map_first_check = False
                        if not move_to_next_map(self.driver, exp_route):
                            self.driver._move_fail_count = getattr(self.driver, "_move_fail_count", 0) + 1
                            if self.driver._move_fail_count >= 3:
                                self.log("🔄 GW nie znalezione 3x z rzędu – odświeżam stronę...")
                                self.driver._move_fail_count = 0
                                _refresh_and_wait()
                            else:
                                time.sleep(1)
                        else:
                            self.driver._move_fail_count = 0
                    else:
                        if _first_check:
                            # Po zmianie mapy: czekaj aż moby załadują się do DOM (max 2s)
                            self.driver._map_first_check = False
                            mob_id = wait_for_mob(self.driver, excluded=_excl,
                                                  ignored_tip_ids=_ignored, timeout_s=2.0)
                        else:
                            mob_id = get_near_object(self.driver, excluded=_excl,
                                                     ignored_tip_ids=_ignored)

                        if mob_id is None:
                            self.log("🟡 Brak mobów – ruch...")
                            self.driver._ignored_tip_ids = set()
                            if not move_to_next_map(self.driver, exp_route):
                                self.driver._move_fail_count = getattr(self.driver, "_move_fail_count", 0) + 1
                                if self.driver._move_fail_count >= 3:
                                    self.log("🔄 GW nie znalezione 3x z rzędu – odświeżam stronę...")
                                    self.driver._move_fail_count = 0
                                    _refresh_and_wait()
                                continue
                            else:
                                self.driver._move_fail_count = 0
                        else:
                            self.driver._move_fail_count = 0
                            result = kill_object(self.driver, mob_id, char_level=_char_lvl)
                            if result == "IGNORED":
                                _ignored.add(mob_id)

                elif FARM_MODE == "e2":
                    e2_cfg_path  = cfg.get("e2_config_path")
                    e2_is_leader    = cfg.get("e2_is_leader", False)
                    e2_is_attacker  = cfg.get("e2_is_attacker", False)
                    e2_pos_idx      = int(cfg.get("e2_position_idx", 0))
                    if not e2_cfg_path or not os.path.isfile(e2_cfg_path):
                        self.log("⚠️  Brak konfiguracji E2 — przełącz na tryb none")
                        self.config["mode"] = "none"
                        continue
                    with open(e2_cfg_path, encoding="utf-8") as _f:
                        e2_cfg_data = json.load(_f)
                    positions = e2_cfg_data.get("waiting_positions", [])
                    wait_pos  = positions[e2_pos_idx] if positions else {"x": 0, "y": 0, "top": 0.0, "left": 0.0, "label": "?"}
                    run_e2(
                        self.driver,
                        e2_cfg      = e2_cfg_data,
                        is_leader   = e2_is_leader,
                        is_attacker = e2_is_attacker,
                        wait_pos    = wait_pos,
                        stop_event  = self.stop_event,
                        log_fn      = self.log,
                    )

                elif FARM_MODE == "heros":
                    check_and_solve_captcha(self.driver)
                    enable_map(self.driver, enabled=True)
                    if heros_json != getattr(self.driver, "_active_heros_json", None):
                        self.driver._active_heros_json = heros_json
                        heros_data = load_heros_route(heros_json)
                        self.driver._heros_route       = heros_data["route"]
                        self.driver._heros_route_index = heros_data["route_index"]
                        self.log(f"🔄 Heros: załadowano trasę '{os.path.basename(os.path.dirname(heros_json))}'")

                        first_map = self.driver._heros_route[0]["location"]
                        if _get_location_text(self.driver) != first_map:
                            self.log(f"🗺️  Heros: nawiguję do startowej mapy: {first_map}")
                            if not travel_to(self.driver, first_map, stop_event=self.stop_event):
                                self.log(f"❌ Nie udało się dotrzeć do {first_map}")
                                return
                            self.log(f"✅ Dotarłem do: {first_map}")

                    route       = self.driver._heros_route
                    route_index = self.driver._heros_route_index
                    location    = route[route_index]
                    self.log(f"📍 [{route_index+1}/{len(route)}] {location['location']}")

                    for _, resp_coords in enumerate(location.get("respawns", [])):
                        self.pause_check()
                        resp_tip_id = find_nearest_heros_resp(
                            self.driver,
                            (resp_coords["left"], resp_coords["top"]),
                            tolerance=20)
                        if resp_tip_id is None:
                            continue
                        heros_detected = click_heros_resp(
                            self.driver, resp_tip_id,
                            timeout=120, discord_webhook=discord)
                        if heros_detected:
                            heros_tip_id = find_heros_on_map(self.driver)
                            if no_attack:
                                while heros_tip_id:
                                    time.sleep(2)
                                    self.pause_check()
                                    check_and_solve_captcha(self.driver)
                                    heros_tip_id = find_heros_on_map(self.driver)
                            elif heros_tip_id:
                                kill_heros(self.driver, heros_tip_id, max_time_s=30)
                        time.sleep(0.5)

                    gw = location.get("gw")
                    if gw:
                        next_idx = (route_index + 1) % len(route)
                        next_map = route[next_idx]["location"]
                        ok = click_gw(self.driver, (gw["left"], gw["top"]),
                                      expected_map_name=next_map, timeout=120, tolerance=30)
                        if not ok:
                            ok = click_gw(self.driver, (gw["left"], gw["top"]),
                                          expected_map_name=next_map, timeout=120, tolerance=50)
                            if not ok:
                                self.driver._heros_route_index = next_idx
                                time.sleep(2)
                                continue

                    self.driver._heros_route_index = (route_index + 1) % len(route)
                    time.sleep(0.5)

                elif FARM_MODE == "kopalnia":
                    from mine_mode import run_mine
                    mine_path    = self.config.get("mine_config_path")
                    mine_pos_idx = int(self.config.get("mine_position_idx", 0))
                    mine_auto    = bool(self.config.get("mine_auto", True))
                    if not mine_path or not os.path.isfile(mine_path):
                        self.log("⚠️  Mine: brak pliku konfiguracji – zatrzymuję")
                        return
                    with open(mine_path, encoding="utf-8") as _mf:
                        mine_cfg = json.load(_mf)
                    mine_cfg["actions"] = (
                        self.config.get("actions") or
                        self.config.get("action") or
                        mine_cfg.get("actions") or
                        mine_cfg.get("action") or []
                    )
                    run_mine(self.driver, mine_cfg, self.stop_event, self.log,
                             auto_enter=mine_auto, mine_position_idx=mine_pos_idx)
                    return

                elif FARM_MODE == "elite":
                    from mine_mode import run_mine_elite_only
                    mine_path    = self.config.get("mine_config_path")
                    mine_pos_idx = int(self.config.get("mine_position_idx", 0))
                    if not mine_path or not os.path.isfile(mine_path):
                        self.log("⚠️  Elite: brak pliku konfiguracji kopalni – zatrzymuję")
                        return
                    with open(mine_path, encoding="utf-8") as _mf:
                        mine_cfg = json.load(_mf)
                    mine_cfg["actions"] = (
                        self.config.get("actions") or
                        self.config.get("action") or
                        mine_cfg.get("actions") or
                        mine_cfg.get("action") or []
                    )
                    run_mine_elite_only(self.driver, mine_cfg, self.stop_event, self.log,
                                        fight_location=mine_cfg.get("fight_location", ""),
                                        position_idx=mine_pos_idx)
                    return

                elif FARM_MODE == "dobijarka":
                    check_and_solve_captcha(self.driver)
                    self.log("⚙️  Tryb dobijarka – w przygotowaniu...")
                    time.sleep(10)

                elif FARM_MODE == "playbook":
                    pb_path = self.config.get("playbook_path")
                    if not pb_path or not os.path.isfile(pb_path):
                        self.log("⚠️  Playbook: brak pliku – zatrzymuję")
                        return
                    from actions.executor        import ActionRegistry, PlaybookExecutor, load_playbook
                    from actions.find_object    import find_object
                    from actions.solve_captcha  import solve_captcha
                    from actions.kill_object    import kill_object_action
                    from actions.navigate_to    import navigate_to
                    from actions.wait           import wait as wait_action
                    from actions.anti_afk       import anti_afk
                    from actions.move_to        import move_to
                    from actions.check_role     import check_role
                    from actions.disband_group  import disband_group
                    from actions.wait_group     import wait_group
                    from actions.make_group     import make_group
                    from actions.check_afk_members import check_afk_members
                    from actions.checkout_group import checkout_group
                    from actions.wait_battle    import wait_battle
                    from actions.attack_colossus import attack_colossus
                    from actions.quick_fight    import quick_fight
                    from actions.watch_battle   import watch_battle
                    from actions.end_battle     import end_battle
                    from actions.wait_death     import wait_death
                    from actions.play                import play as play_action
                    from actions.check_colossus_done  import check_colossus_done
                    from actions.use_repeat_entry    import use_repeat_entry
                    from actions.check_group_size    import check_group_size
                    _pb_registry = ActionRegistry()
                    _pb_registry.register("find_object",      find_object)
                    _pb_registry.register("solve_captcha",    solve_captcha)
                    _pb_registry.register("kill_object",      kill_object_action)
                    _pb_registry.register("navigate_to",      navigate_to)
                    _pb_registry.register("wait",             wait_action)
                    _pb_registry.register("anti_afk",         anti_afk)
                    _pb_registry.register("move_to",          move_to)
                    _pb_registry.register("check_role",       check_role)
                    _pb_registry.register("disband_group",    disband_group)
                    _pb_registry.register("wait_group",       wait_group)
                    _pb_registry.register("make_group",       make_group)
                    _pb_registry.register("check_afk_members", check_afk_members)
                    _pb_registry.register("checkout_group",   checkout_group)
                    _pb_registry.register("wait_battle",      wait_battle)
                    _pb_registry.register("attack_colossus",  attack_colossus)
                    _pb_registry.register("quick_fight",      quick_fight)
                    _pb_registry.register("watch_battle",     watch_battle)
                    _pb_registry.register("end_battle",       end_battle)
                    _pb_registry.register("wait_death",       wait_death)
                    _pb_registry.register("play",                play_action)
                    _pb_registry.register("check_colossus_done", check_colossus_done)
                    _pb_registry.register("use_repeat_entry",    use_repeat_entry)
                    _pb_registry.register("check_group_size",    check_group_size)
                    _pb_data = load_playbook(pb_path)
                    _pb_executor = PlaybookExecutor(
                        self.driver,
                        registry=_pb_registry,
                        stop_event=self.stop_event,
                        log_fn=self.log,
                    )
                    if self.config.get("kolos_repeat"):
                        _pb_executor.ctx.set("kolos_repeat", "true")
                    _pb_executor.run(_pb_data)

                elif FARM_MODE == "kolos":
                    kolos_cfg_path  = self.config.get("kolos_config_path")
                    kolos_is_leader = self.config.get("kolos_is_leader", False)
                    if not kolos_cfg_path or not os.path.isfile(kolos_cfg_path):
                        self.log("⚠️  Kolos: brak pliku konfiguracji – zatrzymuję")
                        return
                    with open(kolos_cfg_path, encoding="utf-8") as _kf:
                        kolos_cfg = json.load(_kf)
                    if kolos_is_leader:
                        kolos_result = run_kolos_leader(self.driver, kolos_cfg, self.stop_event, self.log)
                    else:
                        kolos_result = run_kolos_follower(self.driver, kolos_cfg, self.stop_event, self.log)
                    if kolos_result in ("killed", "pause"):
                        reason = "zabiciu kolosusa" if kolos_result == "killed" else "blokadzie sali"
                        self.log(f"⏸️  Kolos: pausuję sesję po {reason}")
                        cur = self.config.get("mode", "none")
                        if cur != "none":
                            self.config["_saved_mode"] = cur
                        self.config["mode"] = "none"
                        if self.pause_callback:
                            self.pause_callback()
                        continue
                    return

                elif FARM_MODE == "otchlan":
                    from otchlan_mode import run_otchlan
                    run_otchlan(self.driver, self.stop_event, self.log)
                    return

            except StopIteration:
                raise
            except StaleElementReferenceException:
                self.log("⚠️  Stale element – retry za 1s")
                time.sleep(1)

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
        self._groups[key] = {"color": color, "sessions": []}
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

    def to_dict(self) -> list:
        return [{"name": n, "world": w, "color": d["color"],
                 "favorite": (w, n) in self._favorites}
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

    def __init__(self, parent, on_created=None):
        super().__init__(parent)
        self.on_created = on_created   # callback(filename, path)
        self._stop      = threading.Event()
        self._driver    = None

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
        if browser in BROWSER_BINARY:
            opts.binary_location = BROWSER_BINARY[browser]

        try:
            self._driver = uc.Chrome(options=opts,
                                      version_main=_detect_browser_major_version(browser) or BROWSER_VERSION.get(browser, 148),
                                      driver_executable_path=None)
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

        if nick and not self._stop.is_set():
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
        tk.Label(world_hdr, text="ŚWIAT", font=("Segoe UI", 8, "bold"),
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
                font=("Segoe UI", 8, "bold"), padx=8, pady=2,
            )
            btn.pack(side="left", padx=(0, 4))
            self._world_btns[w] = btn

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ---- nagłówek grup ----
        hdr = tk.Frame(self, bg=BG2, pady=8)
        hdr.pack(fill="x", padx=10)
        tk.Label(hdr, text="GRUPY", font=("Segoe UI", 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")
        tk.Button(hdr, text="＋", command=self._new_group,
                  bg=BG2, fg=ACCENT, relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold")).pack(side="right")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # === ULUBIONE (stała wysokość, max 5 wierszy) ===
        self.fav_outer = tk.Frame(self, bg=BG2)
        self.fav_outer.pack(fill="x")
        # zawartość budowana dynamicznie w _refresh()

        # === WSZYSTKIE GRUPY (scrollowalne, wypełnia resztę) ===
        all_lbl_row = tk.Frame(self, bg=BG2, pady=3)
        all_lbl_row.pack(fill="x", padx=10)
        tk.Label(all_lbl_row, text="WSZYSTKIE", font=("Segoe UI", 7, "bold"),
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
        tk.Label(tpl_hdr, text="PROFILE", font=("Segoe UI", 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")

        tk.Button(tpl_hdr, text="＋ Template", command=self._add_template_dialog,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=("Segoe UI", 8, "bold"), padx=6, pady=2).pack(side="right")
        tk.Button(tpl_hdr, text="＋ Konto", command=self._create_account_dialog,
                  bg=BG3, fg=GREEN, relief="flat", cursor="hand2",
                  font=("Segoe UI", 8, "bold"), padx=6, pady=2).pack(side="right", padx=(0, 4))

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
                            font=("Segoe UI", 9), bg=BG2,
                            fg="#FFD700" if is_fav else FG_DIM, cursor="hand2")
            star.pack(side="left", padx=(2, 0))
            row._star_lbl = star
            def _star_click(e, n=name):
                self._toggle_favorite(n)
                return "break"
            star.bind("<Button-1>", _star_click)

        dot = tk.Label(row, text="●", font=("Segoe UI", 10), bg=BG2, fg=color)
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
                            font=("Segoe UI", 8), padx=0, pady=0, width=1,
                            bd=0, highlightthickness=0)
            tk.Button(ctrl, text="⏹", command=lambda n=name: self._stop_group(n),
                      **_btn_cfg).pack(side="right")
            tk.Button(ctrl, text="⏸", command=lambda n=name: self._pause_group(n),
                      **_btn_cfg).pack(side="right")
            tk.Button(ctrl, text="▶", command=lambda n=name: self._start_group(n),
                      **_btn_cfg).pack(side="right")

            count_lbl = tk.Label(row, text="", font=("Segoe UI", 8),
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
            tk.Label(self.tpl_list_frame, text="Brak szablonów", font=("Segoe UI", 8),
                     bg=BG2, fg=FG_DIM).pack(anchor="w", padx=4)
        for browser, t in templates:
            row = tk.Frame(self.tpl_list_frame, bg=BG2)
            row.pack(fill="x", pady=1)
            tk.Label(row, text="🗂", font=("Segoe UI", 9),
                     bg=BG2, fg=FG_DIM).pack(side="left", padx=(2, 4))
            tk.Label(row, text=f"[{browser}] {t}", font=("Segoe UI", 8),
                     bg=BG2, fg=FG, anchor="w").pack(side="left", fill="x", expand=True)
            tk.Button(row, text="🗑",
                      command=lambda b=browser, n=t: self._delete_template(b, n),
                      bg=BG2, fg=FG_DIM, relief="flat", cursor="hand2",
                      font=("Segoe UI", 8)).pack(side="right")

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
            tk.Label(fhdr, text="ULUBIONE", font=("Segoe UI", 8, "bold"),
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
        else:
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
    def _start_group(self, group: str):
        if self._get_sessions_fn is None:
            return
        sessions = self._get_sessions_fn()
        to_start = [s for s in sessions
                    if self.gm.group_of(s.session_id) == group
                    and self.gm.world_of_session(s.session_id) == self._selected_world
                    and not s.is_running]
        if not to_start:
            return

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

    def _pause_group(self, group: str):
        if self._get_sessions_fn is None:
            return
        for s in self._get_sessions_fn():
            if (self.gm.group_of(s.session_id) == group
                    and self.gm.world_of_session(s.session_id) == self._selected_world
                    and s.is_running):
                s._on_pause()

    def _stop_group(self, group: str):
        if self._get_sessions_fn is None:
            return
        for s in self._get_sessions_fn():
            if (self.gm.group_of(s.session_id) == group
                    and self.gm.world_of_session(s.session_id) == self._selected_world):
                if s.is_running or getattr(s, "_pending_restart", None) is not None:
                    s._on_stop()



# ============================================
# DIALOG: NOWY CONFIG
# ============================================
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

# ============================================
# PANEL DYSPOZYTORSKI (drugi sidebar)
# ============================================
class DispatchPanel(tk.Frame):
    """
    Panel wyboru akcji grupowej: tryb + cel + grupa → START/STOP.
    Tryby: E2, Kopalnia, Heros, Go (wszystkie mapy ze świata).
    """
    WIDTH = 220
    MODES = ["E2", "Kopalnia", "Heros", "Kolos", "Go"]

    def __init__(self, parent, group_manager: GroupManager, base_dir: str,
                 get_sessions_fn=None):
        super().__init__(parent, bg=BG2, width=self.WIDTH)
        self.pack_propagate(False)
        self.gm               = group_manager
        self.base_dir         = base_dir
        self._active          = False
        self._get_sessions_fn = get_sessions_fn

        self._scan_targets()
        self._build()
        self.gm.subscribe(self._refresh_groups)

    # ---- skanowanie katalogów ----
    def _scan_targets(self):
        """Odczytaj dostępne cele dla każdego trybu."""
        self._e2_list    = self._scan_dir("e2")
        self._mine_list  = self._scan_mine()
        self._heros_data = self._scan_heros()
        self._world_list = self._scan_world()
        self._kolos_list = self._scan_kolos()

    def _scan_dir(self, subdir: str) -> list:
        d = os.path.join(self.base_dir, subdir)
        if not os.path.isdir(d):
            return []
        return sorted([
            name for name in os.listdir(d)
            if os.path.isdir(os.path.join(d, name))
        ])

    def _scan_mine(self) -> list:
        d = os.path.join(self.base_dir, "mine")
        if not os.path.isdir(d):
            return []
        return sorted([
            os.path.splitext(f)[0]
            for f in os.listdir(d) if f.endswith(".json")
        ])

    def _scan_heros(self) -> dict:
        """
        Zwraca {heros_name: [{"label": ..., "data": {...}}, ...]}
        """
        result = {}
        heros_dir = os.path.join(self.base_dir, "heros")
        if not os.path.isdir(heros_dir):
            return result
        for name in sorted(os.listdir(heros_dir)):
            json_path = os.path.join(heros_dir, name, "heros.json")
            if not os.path.isfile(json_path):
                continue
            spawns = []
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
                for loc in data.get("route", []):
                    loc_name = loc.get("location", "?")
                    for resp in loc.get("respawns", []):
                        x = resp.get("x", resp.get("left", "?"))
                        y = resp.get("y", resp.get("top",  "?"))
                        label = f"{loc_name}  ({x}, {y})"
                        spawns.append({"label": label, "location": loc_name,
                                       "data": resp})
            except Exception:
                pass
            result[name] = spawns
        return result

    def _scan_kolos(self) -> list:
        """Zwraca posortowaną listę nazw (bez .json) plików z katalogu colossus/."""
        d = os.path.join(self.base_dir, "colossus")
        if not os.path.isdir(d):
            return []
        return sorted([
            os.path.splitext(f)[0]
            for f in os.listdir(d) if f.endswith(".json")
        ])

    def _scan_world(self) -> list:
        """
        Zwraca posortowaną listę nazw map ze świata (./world/*.json).
        Preferuje pole "location" z JSON-a, fallback do nazwy pliku.
        """
        world_dir = os.path.join(self.base_dir, "world")
        if not os.path.isdir(world_dir):
            return []
        names = []
        for path in sorted(glob.glob(os.path.join(world_dir, "*.json"))):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("location")
                if name:
                    names.append(name)
                else:
                    names.append(os.path.splitext(os.path.basename(path))[0])
            except Exception:
                names.append(os.path.splitext(os.path.basename(path))[0])
        return sorted(set(names), key=lambda s: s.lower())

    # ---- budowanie UI ----
    def _build(self):
        # --- nagłówek ---
        hdr = tk.Frame(self, bg=BG2, pady=8)
        hdr.pack(fill="x", padx=10)
        tk.Label(hdr, text="DYSPOZYTOR", font=("Segoe UI", 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(side="left")
        tk.Button(hdr, text="⟳", command=self._rescan,
                  bg=BG2, fg=ACCENT, relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold")).pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG2)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # --- wybór trybu: 2 × 2 grid, żeby pomieścić 4 przyciski ---
        tk.Label(body, text="Tryb:", font=("Segoe UI", 8, "bold"),
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 4))

        self.dispatch_mode = tk.StringVar(value="E2")
        mode_row = tk.Frame(body, bg=BG2)
        mode_row.pack(fill="x", pady=(0, 8))
        mode_row.grid_columnconfigure(0, weight=1, uniform="m")
        mode_row.grid_columnconfigure(1, weight=1, uniform="m")
        self._mode_btns = {}
        for i, m in enumerate(self.MODES):
            b = tk.Radiobutton(mode_row, text=m, variable=self.dispatch_mode,
                               value=m, command=self._on_mode_change,
                               bg=BG2, fg=FG, selectcolor=BG2,
                               activebackground=BG2, activeforeground=ACCENT,
                               font=("Segoe UI", 8, "bold"), relief="flat",
                               indicatoron=False, cursor="hand2",
                               bd=0, pady=5)
            b.grid(row=i // 2, column=i % 2, sticky="ew",
                   padx=(0 if i % 2 == 0 else 2, 2 if i % 2 == 0 else 0),
                   pady=1)
            self._mode_btns[m] = b
        self._refresh_mode_colors()

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))

        # --- dynamiczna sekcja celu ---
        self.target_frame = tk.Frame(body, bg=BG2)
        self.target_frame.pack(fill="both", expand=True)

        # ---- E2 ----
        self.e2_frame = tk.Frame(self.target_frame, bg=BG2)
        tk.Label(self.e2_frame, text="Elita II:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.e2_var = tk.StringVar()
        self.e2_lb  = tk.Listbox(self.e2_frame,
                                  listvariable=tk.StringVar(value=self._e2_list),
                                  font=FONT_SMALL, bg=BG3, fg=FG,
                                  selectbackground=ACCENT, selectforeground="#000",
                                  relief="flat", bd=0, height=8,
                                  activestyle="none")
        self.e2_lb.pack(fill="x")
        if self._e2_list:
            self.e2_lb.selection_set(0)

        # ---- Kopalnia ----
        self.mine_frame = tk.Frame(self.target_frame, bg=BG2)
        tk.Label(self.mine_frame, text="Kopalnia:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.mine_lb = tk.Listbox(self.mine_frame,
                                   listvariable=tk.StringVar(value=self._mine_list),
                                   font=FONT_SMALL, bg=BG3, fg=FG,
                                   selectbackground=ACCENT, selectforeground="#000",
                                   relief="flat", bd=0, height=8,
                                   activestyle="none")
        self.mine_lb.pack(fill="x")
        if self._mine_list:
            self.mine_lb.selection_set(0)

        # ---- Heros ----
        self.heros_frame = tk.Frame(self.target_frame, bg=BG2)
        tk.Label(self.heros_frame, text="Heros:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.heros_var = tk.StringVar()
        self.heros_cb  = ttk.Combobox(self.heros_frame, textvariable=self.heros_var,
                                       font=FONT_SMALL, state="readonly", width=22)
        self.heros_cb["values"] = list(self._heros_data.keys())
        if self._heros_data:
            self.heros_var.set(list(self._heros_data.keys())[0])
        self.heros_cb.pack(fill="x", pady=(0, 6))
        self.heros_cb.bind("<<ComboboxSelected>>", self._on_heros_selected)

        tk.Label(self.heros_frame, text="Respawn:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.spawn_lb = tk.Listbox(self.heros_frame,
                                    font=FONT_SMALL, bg=BG3, fg=FG,
                                    selectbackground=ACCENT, selectforeground="#000",
                                    relief="flat", bd=0, height=6,
                                    activestyle="none")
        self.spawn_lb.pack(fill="x")
        self._refresh_spawn_list()

        # ---- Go (wszystkie mapy ze świata, wyszukiwarka) ----
        self.go_frame = tk.Frame(self.target_frame, bg=BG2)
        tk.Label(self.go_frame, text="Wyszukaj mapę:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))

        self.go_search_var = tk.StringVar()
        self.go_search_var.trace_add("write", self._filter_go_list)
        go_search = tk.Entry(self.go_frame, textvariable=self.go_search_var,
                              font=FONT_SMALL, bg=BG3, fg=FG,
                              insertbackground=FG, relief="flat")
        go_search.pack(fill="x", ipady=4, pady=(0, 2))

        # licznik wyników
        self.go_count_lbl = tk.Label(self.go_frame, text="", font=("Segoe UI", 8),
                                      bg=BG2, fg=FG_DIM, anchor="w")
        self.go_count_lbl.pack(fill="x", pady=(0, 4))

        tk.Label(self.go_frame, text="Mapa docelowa:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))

        go_list_frame = tk.Frame(self.go_frame, bg=BG2)
        go_list_frame.pack(fill="both", expand=True)

        self.go_lb = tk.Listbox(go_list_frame, font=FONT_SMALL, bg=BG3, fg=FG,
                                 selectbackground=ACCENT, selectforeground="#000",
                                 relief="flat", bd=0, height=12,
                                 activestyle="none",
                                 exportselection=False)
        go_scroll = tk.Scrollbar(go_list_frame, orient="vertical",
                                  command=self.go_lb.yview,
                                  bg=BG3, troughcolor=BG2, bd=0,
                                  highlightthickness=0, relief="flat")
        self.go_lb.configure(yscrollcommand=go_scroll.set)
        go_scroll.pack(side="right", fill="y")
        self.go_lb.pack(side="left", fill="both", expand=True)

        # Enter w polu wyszukiwania → wybierz pierwszy wynik i odpal START
        go_search.bind("<Return>", self._on_go_search_enter)
        # Enter/podwójny klik na liście → odpal START
        self.go_lb.bind("<Double-Button-1>", lambda e: self._on_start())
        self.go_lb.bind("<Return>", lambda e: self._on_start())

        self._refresh_go_list()

        # ---- Kolos ----
        self.kolos_frame = tk.Frame(self.target_frame, bg=BG2)
        tk.Label(self.kolos_frame, text="Kolos config:", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.kolos_dispatch_var = tk.StringVar()
        self.kolos_dispatch_lb  = tk.Listbox(
            self.kolos_frame,
            listvariable=tk.StringVar(value=self._kolos_list),
            font=FONT_SMALL, bg=BG3, fg=FG,
            selectbackground=ACCENT, selectforeground="#000",
            relief="flat", bd=0, height=6,
            activestyle="none")
        self.kolos_dispatch_lb.pack(fill="x", pady=(0, 6))
        if self._kolos_list:
            self.kolos_dispatch_lb.selection_set(0)

        tk.Label(self.kolos_frame, text="Leader (sesja):", font=FONT_SMALL,
                 bg=BG2, fg=FG_DIM).pack(anchor="w", pady=(0, 3))
        self.kolos_leader_session_var = tk.StringVar()
        self.kolos_leader_cb = ttk.Combobox(
            self.kolos_frame, textvariable=self.kolos_leader_session_var,
            font=FONT_SMALL, state="readonly", width=22)
        self.kolos_leader_cb.pack(fill="x")
        self.kolos_frame.bind("<Map>", lambda e: self._refresh_kolos_sessions())

        # pokaż domyślny tryb
        self._on_mode_change()

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(10, 8))

        # --- aktywna grupa (ustawiana z zewnątrz przez set_group) ---
        self._current_group = None
        self._current_world = WORLDS[0]
        self._group_lbl = tk.Label(body, text="— wszystkie grupy —",
                                    font=("Segoe UI", 8), bg=BG2, fg=FG_DIM)
        self._group_lbl.pack(anchor="w", pady=(0, 8))

        # --- START / STOP (dyspozytor) ---
        btn_row = tk.Frame(body, bg=BG2)
        btn_row.pack(fill="x")
        self.start_btn = tk.Button(btn_row, text="▶ START",
                                    command=self._on_start,
                                    bg=GREEN, fg="#000", font=FONT_BOLD,
                                    relief="flat", cursor="hand2",
                                    padx=10, pady=6)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.stop_btn  = tk.Button(btn_row, text="⏹ STOP",
                                    command=self._on_stop,
                                    bg=RED, fg="#fff", font=FONT_BOLD,
                                    relief="flat", cursor="hand2",
                                    padx=10, pady=6, state="disabled")
        self.stop_btn.pack(side="left", fill="x", expand=True)

        # status
        self.status_lbl = tk.Label(body, text="", font=("Segoe UI", 8),
                                    bg=BG2, fg=FG_DIM, wraplength=200)
        self.status_lbl.pack(anchor="w", pady=(6, 0))

    # ---- tryb ----
    def _on_mode_change(self):
        mode = self.dispatch_mode.get()
        self.e2_frame.pack_forget()
        self.mine_frame.pack_forget()
        self.heros_frame.pack_forget()
        self.kolos_frame.pack_forget()
        self.go_frame.pack_forget()
        if mode == "E2":
            self.e2_frame.pack(fill="x")
        elif mode == "Kopalnia":
            self.mine_frame.pack(fill="x")
        elif mode == "Heros":
            self.heros_frame.pack(fill="x")
        elif mode == "Kolos":
            self._refresh_kolos_sessions()
            self.kolos_frame.pack(fill="x")
        elif mode == "Go":
            self.go_frame.pack(fill="both", expand=True)
        self._refresh_mode_colors()

    def _refresh_mode_colors(self):
        mode = self.dispatch_mode.get()
        for m, b in self._mode_btns.items():
            b.configure(bg=ACCENT if m == mode else BG3,
                        fg="#000" if m == mode else FG)

    def _refresh_kolos_sessions(self):
        """Odśwież listę sesji dostępnych jako leader kolosusa."""
        if self._get_sessions_fn is None:
            return
        group = self._current_group
        sessions = self._get_sessions_fn()
        names = []
        for s in sessions:
            in_group = (self.gm.world_of_session(s.session_id) == self._current_world and
                        (group is None or self.gm.group_of(s.session_id) == group))
            if in_group:
                names.append(s.name or f"sesja {s.session_id}")
        self.kolos_leader_cb["values"] = names
        if names and not self.kolos_leader_session_var.get():
            self.kolos_leader_session_var.set(names[0])

    # ---- heros respawny ----
    def _on_heros_selected(self, _=None):
        self._refresh_spawn_list()

    def _refresh_spawn_list(self):
        self.spawn_lb.delete(0, tk.END)
        name   = self.heros_var.get()
        spawns = self._heros_data.get(name, [])
        if not spawns:
            self.spawn_lb.insert(tk.END, "  (brak danych respawnów)")
        else:
            for s in spawns:
                self.spawn_lb.insert(tk.END, f"  {s['label']}")
            self.spawn_lb.selection_set(0)

    # ---- Go: lista map + wyszukiwarka ----
    def _filter_go_list(self, *args):
        query = self.go_search_var.get().strip().lower()
        self.go_lb.delete(0, tk.END)
        matches = [n for n in self._world_list
                   if not query or query in n.lower()]
        for n in matches:
            self.go_lb.insert(tk.END, n)
        if matches:
            self.go_lb.selection_set(0)
        total = len(self._world_list)
        if query:
            self.go_count_lbl.configure(text=f"{len(matches)} / {total} pasuje")
        else:
            self.go_count_lbl.configure(text=f"{total} map")

    def _refresh_go_list(self):
        self._filter_go_list()

    def _on_go_search_enter(self, _event=None):
        """Enter w polu wyszukiwania — jeśli jest dokładnie 1 trafienie, start;
        jeśli więcej, przenieś focus na listę."""
        if self.go_lb.size() == 1:
            self.go_lb.selection_clear(0, tk.END)
            self.go_lb.selection_set(0)
            self._on_start()
        elif self.go_lb.size() > 1:
            self.go_lb.focus_set()

    # ---- aktywna grupa ----
    def set_group(self, name: str | None, world: str = "Gordion"):
        self._current_group = name
        self._current_world = world
        if name:
            color = self.gm.color_of(name, world)
            self._group_lbl.configure(text=f"● {name}", fg=color)
        else:
            self._group_lbl.configure(text="— wszystkie grupy —", fg=FG_DIM)

    def _refresh_groups(self):
        pass

    # ---- rescan ----
    def _rescan(self):
        self._scan_targets()
        self.e2_lb["listvariable"]   = tk.StringVar(value=self._e2_list)
        self.mine_lb["listvariable"] = tk.StringVar(value=self._mine_list)
        self.heros_cb["values"]      = list(self._heros_data.keys())
        if self._heros_data:
            self.heros_var.set(list(self._heros_data.keys())[0])
        self._refresh_spawn_list()
        self._refresh_go_list()
        self.kolos_dispatch_lb["listvariable"] = tk.StringVar(value=self._kolos_list)
        if self._kolos_list:
            self.kolos_dispatch_lb.selection_set(0)
        self.status_lbl.configure(text="✅ Odświeżono")
        self.after(2000, lambda: self.status_lbl.configure(text=""))

    # ---- akcje ----
    def _get_selected_target(self) -> str | None:
        mode = self.dispatch_mode.get()
        if mode == "E2":
            sel = self.e2_lb.curselection()
            return self._e2_list[sel[0]] if sel else None
        elif mode == "Kopalnia":
            sel = self.mine_lb.curselection()
            return self._mine_list[sel[0]] if sel else None
        elif mode == "Heros":
            heros = self.heros_var.get()
            sel   = self.spawn_lb.curselection()
            spawns = self._heros_data.get(heros, [])
            if sel and spawns:
                return f"{heros} @ {spawns[sel[0]]['label']}"
            return heros if heros else None
        elif mode == "Kolos":
            sel = self.kolos_dispatch_lb.curselection()
            return self._kolos_list[sel[0]] if sel else None
        elif mode == "Go":
            sel = self.go_lb.curselection()
            return self.go_lb.get(sel[0]) if sel else None
        return None

    def _on_start(self):
        target = self._get_selected_target()
        group  = self._current_group
        mode   = self.dispatch_mode.get()
        if not target:
            self.status_lbl.configure(text="⚠️  Wybierz cel!", fg=RED)
            return

        if mode == "Go" and self._get_sessions_fn is not None:
            sessions = self._get_sessions_fn()
            sent = 0
            for session in sessions:
                in_group = (self.gm.world_of_session(session.session_id) == self._current_world and
                            (group is None or self.gm.group_of(session.session_id) == group))
                if in_group:
                    runner = getattr(session, "_runner", None)
                    if runner is not None:
                        runner.navigate_queue.put(target)
                        sent += 1
            label = f"'{group}'" if group else "wszystkich grup"
            self.status_lbl.configure(
                text=f"🗺️  Go: '{target}'\n→ {sent} sesji ({label})", fg=GREEN)
            return

        if mode == "Kolos" and self._get_sessions_fn is not None:
            leader_name = self.kolos_leader_session_var.get()
            kolos_dir   = os.path.join(self.base_dir, "colossus")
            kolos_path  = os.path.join(kolos_dir, f"{target}.json")
            sessions    = self._get_sessions_fn()
            sent = 0
            for session in sessions:
                in_group = (self.gm.world_of_session(session.session_id) == self._current_world and
                            (group is None or self.gm.group_of(session.session_id) == group))
                if not in_group:
                    continue
                is_leader = (session.name == leader_name or
                             f"sesja {session.session_id}" == leader_name)
                session.kolos_var.set(target)
                session.kolos_leader_var.set(is_leader)
                session.mode_var.set("kolos")
                session._on_mode_change()
                if not session.is_running:
                    session._on_play()
                sent += 1
            label = f"'{group}'" if group else "wszystkich grup"
            self.status_lbl.configure(
                text=f"▶ Kolos '{target}'\nleader: {leader_name} | {sent} sesji ({label})",
                fg=GREEN)
            self._active = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            return

        label = group or "wszystkie grupy"
        self.status_lbl.configure(
            text=f"▶ [{mode}] {target}\n→ {label}", fg=GREEN)

        self._active = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def _on_stop(self):
        self.status_lbl.configure(text="⏹ Zatrzymano", fg=FG_DIM)
        self._active = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")


# ============================================
# POJEDYNCZA SESJA
# ============================================
class SessionTab(tk.Frame):
    def __init__(self, parent, session_id: int,
                 config_map: dict, exp_map: dict, heros_map: dict,
                 group_manager: GroupManager,
                 name: str = "",
                 on_status_change=None,
                 on_config_added=None,
                 on_config_refresh=None,
                 get_all_sessions_fn=None,
                 kolos_map: dict = None,
                 mine_map: dict = None,
                 playbook_map: dict = None,
                 e2_map: dict = None):
        super().__init__(parent, bg=BG)
        self.session_id           = session_id
        self.name                 = name[:20] if name else ""
        self._config_map          = config_map
        self._exp_map             = exp_map
        self._heros_map           = heros_map
        self._kolos_map           = kolos_map or {}
        self._mine_map            = mine_map or {}
        self._playbook_map        = playbook_map or {}
        self._e2_map              = e2_map or {}
        self.gm                   = group_manager
        self.on_status_change     = on_status_change
        self.on_config_added      = on_config_added
        self.on_config_refresh    = on_config_refresh
        self._get_all_sessions_fn = get_all_sessions_fn

        self.pause_event      = threading.Event()
        self.stop_event       = threading.Event()
        self.bot_thread       = None
        self._runner          = None
        self.is_running       = False
        self.is_paused        = False
        self.status           = "OFFLINE"
        self._pending_restart = None   # after() ID for restart-on-fail

        self._build()

    def _build(self):
        # PID label — prawy górny róg (nad rząd 1, wyrównany przez place)
        self.pid_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                bg=BG, fg=FG_DIM)
        self.pid_lbl.place(relx=1.0, x=-90, y=7, anchor="ne")

        # ---- rząd 1: config + delay ----
        row1 = tk.Frame(self, bg=BG, pady=6)
        row1.pack(fill="x", padx=14)

        tk.Label(row1, text="Config:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.config_var = tk.StringVar()
        self.cfg_cb = ttk.Combobox(row1, textvariable=self.config_var,
                               font=FONT_SMALL, state="readonly", width=22)
        self.cfg_cb["values"] = list(self._config_map.keys())
        if self.cfg_cb["values"]:
            self.config_var.set(self.cfg_cb["values"][0])
        self.cfg_cb.pack(side="left", padx=(0, 4))
        tk.Button(row1, text="＋", command=self._new_config,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"), padx=4).pack(side="left", padx=(0, 4))
        tk.Button(row1, text="⟳", command=self._refresh_config_now,
                  bg=BG3, fg=ACCENT, relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"), padx=4).pack(side="left", padx=(0, 10))

        tk.Label(row1, text="Serwer:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.server_var = tk.StringVar(value=SERVERS[0])
        server_cb = ttk.Combobox(row1, textvariable=self.server_var,
                                  font=FONT_SMALL, state="readonly", width=10)
        server_cb["values"] = SERVERS
        server_cb.pack(side="left", padx=(0, 14))

        tk.Label(row1, text="Delay (s):", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.delay_var = tk.StringVar(value="10")
        tk.Entry(row1, textvariable=self.delay_var, font=FONT_SMALL,
                 bg=BG3, fg=FG, insertbackground=FG, relief="flat",
                 width=5).pack(side="left", ipady=3, padx=(0, 14))


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

        tk.Frame(row1b, bg=BORDER, width=1).pack(side="left", fill="y", padx=(0, 14))

        self.anti_afk_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Anti-AFK",
                       variable=self.anti_afk_var,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")

        self.event_rewards_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Event",
                       variable=self.event_rewards_var,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(10, 0))

        self.restart_on_fail_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Restart on fail",
                       variable=self.restart_on_fail_var,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(10, 0))

        tk.Frame(row1b, bg=BORDER, width=1).pack(side="left", fill="y", padx=(10, 10))

        self.max_lvl_enabled_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row1b, text="Max lvl:",
                       variable=self.max_lvl_enabled_var,
                       command=self._on_max_lvl_toggle,
                       bg=BG, fg=FG, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")
        self.max_lvl_var   = tk.StringVar(value="")
        self.max_lvl_entry = tk.Entry(
            row1b, textvariable=self.max_lvl_var,
            font=FONT_SMALL, bg=BG3, fg=FG, insertbackground=FG,
            relief="flat", width=5, state="disabled")
        self.max_lvl_entry.pack(side="left", padx=(2, 0))

        # ---- rząd 2: tryb ----
        row2 = tk.Frame(self, bg=BG)
        row2.pack(fill="x", padx=14)
        tk.Label(row2, text="Tryb:", font=FONT_SMALL, bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 6))
        self.mode_var   = tk.StringVar(value="exp")
        self._mode_btns = {}
        for m in MODES:
            b = tk.Radiobutton(row2, text=m.upper(), variable=self.mode_var, value=m,
                               command=self._on_mode_change,
                               bg=BG, fg=FG, selectcolor=BG,
                               activebackground=BG, activeforeground=ACCENT,
                               font=("Segoe UI", 8, "bold"), relief="flat",
                               indicatoron=False, cursor="hand2",
                               width=8, bd=0, pady=4)
            b.pack(side="left", padx=2)
            self._mode_btns[m] = b
        self._refresh_mode_colors()

        # ---- rząd 3: opcje trybu ----
        self.opt_row = tk.Frame(self, bg=BG)
        self.opt_row.pack(fill="x", padx=14, pady=(2, 0))

        self.exp_frame = tk.Frame(self.opt_row, bg=BG)
        self.auto_exp_var = tk.BooleanVar(value=False)
        self.auto_exp_cb  = tk.Checkbutton(
            self.exp_frame, text="Auto", variable=self.auto_exp_var,
            command=self._on_auto_exp_toggle,
            bg=BG, fg=FG, selectcolor=BG,
            activebackground=BG, activeforeground=ACCENT,
            font=FONT_SMALL)
        self.auto_exp_cb.pack(side="left", padx=(0, 6))
        tk.Label(self.exp_frame, text="Lokacja:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.exp_var = tk.StringVar()
        self.exp_cb  = ttk.Combobox(self.exp_frame, textvariable=self.exp_var,
                                     font=FONT_SMALL, state="readonly", width=26)
        self.exp_cb["values"] = list(self._exp_map.keys())
        if self.exp_cb["values"]:
            self.exp_var.set(self.exp_cb["values"][0])
        self.exp_cb.pack(side="left")
        self.exp_cb.bind("<<ComboboxSelected>>", self._on_exp_changed)


        self.heros_frame = tk.Frame(self.opt_row, bg=BG)
        tk.Label(self.heros_frame, text="Heros:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.heros_var = tk.StringVar()
        self.heros_cb  = ttk.Combobox(self.heros_frame, textvariable=self.heros_var,
                                       font=FONT_SMALL, state="readonly", width=26)
        self.heros_cb["values"] = list(self._heros_map.keys())
        if self.heros_cb["values"]:
            self.heros_var.set(self.heros_cb["values"][0])
        self.heros_cb.pack(side="left", padx=(0, 8))
        self.heros_cb.bind("<<ComboboxSelected>>", self._on_heros_changed)
        self.no_attack_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.heros_frame, text="no-attack",
                       variable=self.no_attack_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")

        # ---- e2 frame ----
        self.e2_frame = tk.Frame(self.opt_row, bg=BG)
        tk.Label(self.e2_frame, text="E2:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.e2_var = tk.StringVar()
        self.e2_cb  = ttk.Combobox(self.e2_frame, textvariable=self.e2_var,
                                    font=FONT_SMALL, state="readonly", width=22)
        self.e2_cb["values"] = list(self._e2_map.keys())
        if self.e2_cb["values"]:
            self.e2_var.set(self.e2_cb["values"][0])
        self.e2_cb.pack(side="left", padx=(0, 4))
        self.e2_cb.bind("<<ComboboxSelected>>", self._on_e2_changed)

        tk.Label(self.e2_frame, text="Poz:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.e2_pos_var = tk.StringVar()
        self.e2_pos_cb  = ttk.Combobox(self.e2_frame, textvariable=self.e2_pos_var,
                                        font=FONT_SMALL, state="readonly", width=8)
        self.e2_pos_cb.pack(side="left", padx=(0, 8))

        self.e2_leader_var   = tk.BooleanVar(value=False)
        self.e2_attacker_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.e2_frame, text="Lider",
                       variable=self.e2_leader_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")
        tk.Checkbutton(self.e2_frame, text="Attacker",
                       variable=self.e2_attacker_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(8, 0))

        self._refresh_e2_positions()

        # ---- kolos frame ----
        self.kolos_frame = tk.Frame(self.opt_row, bg=BG)
        tk.Label(self.kolos_frame, text="Kolos:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.kolos_var = tk.StringVar()
        self.kolos_cb  = ttk.Combobox(self.kolos_frame, textvariable=self.kolos_var,
                                       font=FONT_SMALL, state="readonly", width=26)
        self.kolos_cb["values"] = list(self._kolos_map.keys())
        if self.kolos_cb["values"]:
            self.kolos_var.set(self.kolos_cb["values"][0])
        self.kolos_cb.pack(side="left", padx=(0, 8))
        self.kolos_leader_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.kolos_frame, text="Lider",
                       variable=self.kolos_leader_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")
        self.kolos_repeat_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.kolos_frame, text="Repeat",
                       variable=self.kolos_repeat_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left", padx=(8, 0))

        # ---- mine / elite frame ----
        self.mine_frame = tk.Frame(self.opt_row, bg=BG)
        tk.Label(self.mine_frame, text="Kopalnia:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.mine_var = tk.StringVar()
        self.mine_cb  = ttk.Combobox(self.mine_frame, textvariable=self.mine_var,
                                      font=FONT_SMALL, state="readonly", width=20)
        self.mine_cb["values"] = list(self._mine_map.keys())
        if self.mine_cb["values"]:
            self.mine_var.set(self.mine_cb["values"][0])
        self.mine_cb.pack(side="left", padx=(0, 4))
        self.mine_cb.bind("<<ComboboxSelected>>", self._on_mine_changed)

        tk.Label(self.mine_frame, text="Poz:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.mine_pos_var = tk.StringVar()
        self.mine_pos_cb  = ttk.Combobox(self.mine_frame, textvariable=self.mine_pos_var,
                                          font=FONT_SMALL, state="readonly", width=16)
        self.mine_pos_cb.pack(side="left", padx=(0, 6))

        self.mine_auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.mine_frame, text="Auto",
                       variable=self.mine_auto_var,
                       bg=BG, fg=FG_DIM, selectcolor=BG,
                       activebackground=BG, activeforeground=ACCENT,
                       font=FONT_SMALL).pack(side="left")

        self._refresh_mine_positions()

        self.playbook_frame = tk.Frame(self.opt_row, bg=BG)
        tk.Label(self.playbook_frame, text="Playbook:", font=FONT_SMALL,
                 bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 4))
        self.playbook_var = tk.StringVar()
        self.playbook_cb  = ttk.Combobox(self.playbook_frame, textvariable=self.playbook_var,
                                          font=FONT_SMALL, state="readonly", width=24)
        self.playbook_cb["values"] = list(self._playbook_map.keys())
        if self.playbook_cb["values"]:
            self.playbook_var.set(self.playbook_cb["values"][0])
        self.playbook_cb.pack(side="left")

        self._on_mode_change()

        # ---- rząd 4: przyciski sterowania ----
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=14, pady=(8, 4))

        self.play_btn = tk.Button(ctrl, text="▶ START", command=self._on_play,
                                   bg=GREEN, fg="#000", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", padx=12, pady=5)
        self.play_btn.pack(side="left", padx=(0, 4))

        self.pause_btn = tk.Button(ctrl, text="⏸ PAUZA", command=self._on_pause,
                                    bg=VIOLET, fg="#fff", font=FONT_BOLD,
                                    relief="flat", cursor="hand2", padx=12, pady=5,
                                    state="disabled")
        self.pause_btn.pack(side="left", padx=(0, 4))

        self.stop_btn = tk.Button(ctrl, text="⏹ STOP", command=self._on_stop,
                                   bg=RED, fg="#fff", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", padx=12, pady=5,
                                   state="disabled")
        self.stop_btn.pack(side="left", padx=(0, 14))

        self.status_lbl = tk.Label(ctrl, text="● OFFLINE", font=FONT_SMALL,
                                    bg=BG, fg=FG_DIM)
        self.status_lbl.pack(side="left")

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
                if browser in BROWSER_BINARY:
                    opts.binary_location = BROWSER_BINARY[browser]
                driver = uc.Chrome(options=opts,
                                   version_main=_detect_browser_major_version(browser) or BROWSER_VERSION.get(browser, 148),
                                   driver_executable_path=None)
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

    def _new_config(self):
        """Otwórz dialog tworzenia nowego configa."""
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
        self.config_var.set(filename)
        self.logger.write(f"✅ Nowy config: {filename}")
        # powiadom BotGUI żeby zaktualizował pozostałe sesje
        if self.on_config_added:
            self.on_config_added(filename, path)

    def _refresh_config_cb(self):
        """Odśwież wartości comboboxa configów."""
        cur = self.config_var.get()
        self.cfg_cb["values"] = list(self._config_map.keys())
        if cur not in self._config_map and self.cfg_cb["values"]:
            self.config_var.set(self.cfg_cb["values"][0])

    def _refresh_config_now(self):
        """Wczytaj ponownie listę configów z katalogu (np. po ręcznym dodaniu pliku)."""
        if self.on_config_refresh:
            self.on_config_refresh()
        else:
            self._refresh_config_cb()
        self.logger.write("🔄 Lista configów odświeżona z katalogu.")

    # ---- tryb ----
    def _on_mine_changed(self, _=None):
        self._refresh_mine_positions()

    def _refresh_mine_positions(self):
        mine_key = self.mine_var.get()
        mine_path = self._mine_map.get(mine_key)
        positions = []
        if mine_path and os.path.isfile(mine_path):
            try:
                with open(mine_path, encoding="utf-8") as f:
                    data = json.load(f)
                positions = [
                    p.get("label", f"pos {i}")
                    for i, p in enumerate(data.get("positions", []))
                ]
            except Exception:
                pass
        self.mine_pos_cb["values"] = positions
        if positions:
            self.mine_pos_var.set(positions[0])

    def _on_e2_changed(self, _=None):
        self._refresh_e2_positions()

    def _refresh_e2_positions(self):
        key  = self.e2_var.get()
        path = self._e2_map.get(key)
        positions = []
        if path and os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                positions = [
                    p.get("label", f"({p['x']},{p['y']})")
                    for p in data.get("waiting_positions", [])
                ]
            except Exception:
                pass
        self.e2_pos_cb["values"] = positions
        if positions:
            self.e2_pos_var.set(positions[0])

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.exp_frame.pack_forget()
        self.heros_frame.pack_forget()
        self.e2_frame.pack_forget()
        self.kolos_frame.pack_forget()
        self.mine_frame.pack_forget()
        self.playbook_frame.pack_forget()
        if mode == "exp":
            self.exp_frame.pack(side="left")
        elif mode == "heros":
            self.heros_frame.pack(side="left")
        elif mode == "e2":
            self.e2_frame.pack(side="left")
        elif mode == "kolos":
            self.kolos_frame.pack(side="left")
        elif mode in ("kopalnia", "elite"):
            self.mine_frame.pack(side="left")
        elif mode == "playbook":
            self.playbook_frame.pack(side="left")
        self._refresh_mode_colors()
        if self._runner is not None:
            self.logger.write(f"🔄 Zmieniono tryb na: {mode.upper()}")
            if mode == "e2":
                e_key = self.e2_var.get()
                self._runner.config["e2_config_path"]  = self._e2_map.get(e_key, e_key) or None
                self._runner.config["e2_is_leader"]    = self.e2_leader_var.get()
                self._runner.config["e2_is_attacker"]  = self.e2_attacker_var.get()
                cur = self.e2_pos_cb.current()
                self._runner.config["e2_position_idx"] = max(0, cur) if cur >= 0 else 0
            elif mode == "kolos":
                k_key = self.kolos_var.get()
                self._runner.config["kolos_config_path"] = self._kolos_map.get(k_key, k_key) or None
                self._runner.config["kolos_is_leader"]   = self.kolos_leader_var.get()
            elif mode == "playbook":
                pb_key = self.playbook_var.get()
                self._runner.config["playbook_path"] = self._playbook_map.get(pb_key, pb_key) or None
            elif mode == "exp":
                exp_key = self.exp_var.get()
                self._runner.config["exp_route_path"] = self._exp_map.get(exp_key, exp_key) or None
            elif mode == "heros":
                h_key = self.heros_var.get()
                self._runner.config["heros_json_path"] = self._heros_map.get(h_key, h_key) or None
            elif mode in ("kopalnia", "elite"):
                m_key = self.mine_var.get()
                self._runner.config["mine_config_path"] = self._mine_map.get(m_key) or None
                self._runner.config["mine_auto"] = self.mine_auto_var.get()
                pos_vals = list(self.mine_pos_cb["values"])
                cur = self.mine_pos_cb.current()
                self._runner.config["mine_position_idx"] = max(0, cur) if cur >= 0 else 0
            if self.is_running:
                if self.is_paused:
                    self._runner.config["_saved_mode"] = mode
                else:
                    self._runner.config["mode"] = mode
                    self._on_pause()
            else:
                self._runner.config["mode"] = mode
            drv = self._runner.driver
            if drv is not None:
                for attr in ("_heros_route", "_active_exp_route"):
                    if hasattr(drv, attr):
                        delattr(drv, attr)

    def _refresh_mode_colors(self):
        mode = self.mode_var.get()
        for m, b in self._mode_btns.items():
            b.configure(bg=ACCENT if m == mode else BG3,
                        fg="#000" if m == mode else FG)

    def _on_auto_exp_toggle(self):
        auto = self.auto_exp_var.get()
        self.exp_cb.configure(state="disabled" if auto else "readonly")
        if self._runner is not None:
            if auto:
                self._runner.config["exp_route_path"] = None
                self.logger.write("🔄 Auto EXP: włączono automatyczny dobór lokacji")
            else:
                self._on_exp_changed()

    def _on_max_lvl_toggle(self):
        state = "normal" if self.max_lvl_enabled_var.get() else "disabled"
        self.max_lvl_entry.configure(state=state)
        if self._runner is not None:
            enabled = self.max_lvl_enabled_var.get()
            self._runner.config["max_lvl_enabled"] = enabled
            try:
                v = self.max_lvl_var.get().strip()
                self._runner.config["max_lvl"] = int(v) if (v and enabled) else None
            except ValueError:
                pass

    def _on_exp_changed(self, _=None):
        if self._runner is None:
            return
        if self.auto_exp_var.get():
            return
        exp_key = self.exp_var.get()
        new_path = self._exp_map.get(exp_key)
        if new_path:
            self._runner.config["exp_route_path"] = new_path
            self.logger.write(f"🔄 Zmieniono lokację EXP: {exp_key}")

    def _on_heros_changed(self, _=None):
        if self._runner is None:
            return
        h_key = self.heros_var.get()
        new_path = self._heros_map.get(h_key)
        if new_path:
            self._runner.config["heros_json_path"] = new_path
            self.logger.write(f"🔄 Zmieniono herosa: {h_key}")

    # ---- walidacja ----
    def _validate(self):
        mode    = self.mode_var.get()
        cfg_key = self.config_var.get()
        cfg     = self._config_map.get(cfg_key, cfg_key)
        if not cfg or not os.path.isfile(cfg):
            self.logger.write("⚠️  Wybierz plik konfiguracyjny!")
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
                        try:
                            os.kill(_pid, 0)
                            is_stale = False   # żyje → aktywny lock
                        except ProcessLookupError:
                            pass               # martwy → stale
                        except PermissionError:
                            is_stale = False   # żyje, brak uprawnień
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

        exp = None
        auto_exp = False
        if mode == "exp":
            auto_exp = self.auto_exp_var.get()
            if not auto_exp:
                exp_key = self.exp_var.get()
                exp = self._exp_map.get(exp_key, exp_key)
                if not exp or not os.path.isfile(exp):
                    self.logger.write("⚠️  Wybierz lokację EXP!")
                    return None

        max_lvl_enabled = self.max_lvl_enabled_var.get()
        max_lvl = None
        if max_lvl_enabled:
            try:
                v = self.max_lvl_var.get().strip()
                if v:
                    max_lvl = int(v)
            except ValueError:
                pass

        heros = None
        if mode == "heros":
            h_key = self.heros_var.get()
            heros = self._heros_map.get(h_key, h_key)
            if not heros or not os.path.isfile(heros):
                self.logger.write("⚠️  Wybierz herosa!")
                return None

        e2_path = None
        e2_is_leader = False
        e2_is_attacker = False
        e2_pos_idx = 0
        if mode == "e2":
            e_key = self.e2_var.get()
            e2_path = self._e2_map.get(e_key, e_key)
            if not e2_path or not os.path.isfile(e2_path):
                self.logger.write("⚠️  Wybierz konfigurację E2!")
                return None
            e2_is_leader   = self.e2_leader_var.get()
            e2_is_attacker = self.e2_attacker_var.get()
            cur = self.e2_pos_cb.current()
            e2_pos_idx = max(0, cur) if cur >= 0 else 0

        kolos_path = None
        kolos_is_leader = False
        if mode == "kolos":
            k_key = self.kolos_var.get()
            kolos_path = self._kolos_map.get(k_key, k_key)
            if not kolos_path or not os.path.isfile(kolos_path):
                self.logger.write("⚠️  Wybierz konfigurację Kolos!")
                return None
            kolos_is_leader = self.kolos_leader_var.get()
            kolos_repeat    = self.kolos_repeat_var.get()

        mine_path = None
        mine_pos_idx = 0
        mine_auto = True
        if mode in ("kopalnia", "elite"):
            m_key = self.mine_var.get()
            mine_path = self._mine_map.get(m_key, m_key)
            if not mine_path or not os.path.isfile(mine_path):
                self.logger.write("⚠️  Wybierz kopalnię!")
                return None
            pos_vals = list(self.mine_pos_cb["values"])
            cur = self.mine_pos_cb.current()
            mine_pos_idx = max(0, cur) if cur >= 0 else 0
            mine_auto = self.mine_auto_var.get()

        playbook_path = None
        if mode == "playbook":
            pb_key = self.playbook_var.get()
            playbook_path = self._playbook_map.get(pb_key, pb_key)
            if not playbook_path or not os.path.isfile(playbook_path):
                self.logger.write("⚠️  Wybierz playbook!")
                return None

        # Read action sequence from character config file
        cfg_actions = []
        try:
            with open(cfg, encoding="utf-8") as _f:
                cfg_data = json.load(_f)
            cfg_actions = cfg_data.get("action", cfg_data.get("actions", []))
        except Exception:
            pass

        try:
            delay = int(self.delay_var.get())
        except ValueError:
            delay = 10

        tpl = self.template_var.get()
        return {
            "mode":              mode,
            "config_path":       cfg,
            "delay":             delay,
            "exp_route_path":    exp,
            "auto_exp":          auto_exp,
            "max_lvl_enabled":   max_lvl_enabled,
            "max_lvl":           max_lvl,
            "heros_json_path":   heros,
            "no_attack":         self.no_attack_var.get(),
            "anti_afk":          self.anti_afk_var.get(),
            "browser":           self.browser_var.get(),
            "server":            self.server_var.get(),
            "template":          tpl if tpl != "(brak)" else None,
            "group":             self.gm.group_of(self.session_id),
            "group_world":       self.gm.world_of_session(self.session_id),
            "recreate":          self.recreate_var.get(),
            "e2_config_path":    e2_path,
            "e2_is_leader":      e2_is_leader,
            "e2_is_attacker":    e2_is_attacker,
            "e2_position_idx":   e2_pos_idx,
            "kolos_config_path": kolos_path,
            "kolos_is_leader":   kolos_is_leader,
            "kolos_repeat":      kolos_repeat if mode == "kolos" else False,
            "mine_config_path":  mine_path,
            "mine_position_idx": mine_pos_idx,
            "mine_auto":         mine_auto,
            "playbook_path":     playbook_path,
            "actions":           cfg_actions,
            "event_rewards":     self.event_rewards_var.get(),
        }

    # ---- sterowanie ----
    def _resume_exp(self):
        """Wznów bota: przywróć zapisany tryb, zresetuj trasę EXP tylko gdy wraca do exp."""
        resumed_mode = None
        if self._runner is not None:
            saved = self._runner.config.pop("_saved_mode", None)
            if saved:
                self._runner.config["mode"] = saved
                resumed_mode = saved
            drv = self._runner.driver
            if drv is not None and resumed_mode == "exp":
                drv._active_exp_route  = None
                drv._move_seq_idx      = 0
                drv._map_first_check   = False
                drv._stuck_since       = None
                drv._battle_first_seen = None
        self.is_paused = False
        self._set_status("RUNNING")
        self.pause_btn.configure(text="⏸ PAUZA")
        label = resumed_mode.upper() if resumed_mode else "BOT"
        self.logger.write(f"▶️  Wznowiono – tryb {label}")

    def _on_play(self):
        if self.is_paused:
            self._resume_exp()
            return
        if self.is_running:
            return

        config = self._validate()
        if config is None:
            return

        self.pause_event.set()
        self.stop_event.clear()
        self.is_running = True
        self.is_paused  = False
        self._set_status("RUNNING")
        self.play_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")

        runner = BotRunner(config, self.pause_event, self.stop_event, self.logger)
        runner.pause_callback = lambda: self.after(0, self._on_pause)
        self._runner = runner
        self.bot_thread = threading.Thread(
            target=self._bot_wrapper, args=(runner,), daemon=True)
        self.bot_thread.start()
        self.logger.write(
            f"🚀 Start  [{config['mode'].upper()}]  "
            f"{os.path.basename(config['config_path'])}  "
            f"[grupa: {self.gm.group_of(self.session_id)}]")
        self._poll_pid()

    def _bot_wrapper(self, runner: BotRunner):
        try:
            runner.run()
        finally:
            crashed = getattr(runner, "crashed", False) and not self.stop_event.is_set()
            self.after(0, lambda c=crashed: self._on_finished(c))

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

    def _on_pause(self):
        if not self.is_running:
            return
        if not self.is_paused:
            self.is_paused = True
            self._set_status("PAUSED")
            self.pause_btn.configure(text="▶ WZNÓW")
            self.logger.write("⏸️  Wstrzymano – przełączam na tryb NONE")
            if self._runner is not None:
                current = self._runner.config.get("mode", "none")
                if current != "none":
                    self._runner.config["_saved_mode"] = current
                self._runner.config["mode"] = "none"
        else:
            self._resume_exp()

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
        self.pause_event.set()   # unblocks pause_check() immediately

        # Immediate UI feedback — disable buttons so user knows the click landed
        self._set_status("STOPPING")
        self.stop_btn.configure(state="disabled")
        self.pause_btn.configure(state="disabled", text="⏸ PAUZA")
        self.logger.write("⏹️  Zatrzymywanie...")
        self.after(5000, self._force_kill_if_needed)

    def _force_kill_if_needed(self):
        if not self.is_running:
            return
        runner = self._runner
        pid = getattr(runner, "browser_pid", None) if runner else None
        if pid:
            try:
                import signal as _signal
                os.kill(pid, _signal.SIGKILL)
                self.logger.write(f"💀 Wymuszono SIGKILL PID {pid}")
            except Exception as e:
                self.logger.write(f"⚠️  SIGKILL PID {pid} nie powiodło się: {e}")
        else:
            self.logger.write("⚠️  Brak PID — nie można wymusić zatrzymania")

    def _on_finished(self, crashed: bool = False):
        self._runner    = None
        self.is_running = False
        self.is_paused  = False
        self._set_status("OFFLINE")
        self.play_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="⏸ PAUZA")
        self.stop_btn.configure(state="disabled")
        self.pid_lbl.configure(text="")

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

    def get_settings(self) -> dict:
        """Zwraca słownik bieżących ustawień sesji (do zapisu stanu)."""
        return {
            "name":      self.name,
            "config":    self.config_var.get(),
            "delay":     self.delay_var.get(),
            "group":       self.gm.group_of(self.session_id),
            "group_world": self.gm.world_of_session(self.session_id),
            "browser":   self.browser_var.get(),
            "server":    self.server_var.get(),
            "template":  self.template_var.get(),
            "mode":      self.mode_var.get(),
            "exp":              self.exp_var.get(),
            "auto_exp":         self.auto_exp_var.get(),
            "max_lvl_enabled":  self.max_lvl_enabled_var.get(),
            "max_lvl":          self.max_lvl_var.get(),
            "heros":     self.heros_var.get(),
            "no_attack":        self.no_attack_var.get(),
            "anti_afk":         self.anti_afk_var.get(),
            "recreate":         self.recreate_var.get(),
            "event_rewards":    self.event_rewards_var.get(),
            "restart_on_fail":  self.restart_on_fail_var.get(),
            "e2":               self.e2_var.get(),
            "e2_pos":           self.e2_pos_var.get(),
            "e2_is_leader":     self.e2_leader_var.get(),
            "e2_is_attacker":   self.e2_attacker_var.get(),
            "kolos":            self.kolos_var.get(),
            "kolos_is_leader":  self.kolos_leader_var.get(),
            "kolos_repeat":     self.kolos_repeat_var.get(),
            "mine":             self.mine_var.get(),
            "mine_pos":         self.mine_pos_var.get(),
            "mine_auto":        self.mine_auto_var.get(),
            "playbook":         self.playbook_var.get(),
        }

    def apply_settings(self, d: dict):
        """Przywraca ustawienia sesji z zapisanego słownika."""
        if d.get("config") in self._config_map:
            self.config_var.set(d["config"])
        if "delay" in d:
            self.delay_var.set(str(d["delay"]))
        if d.get("browser") in BROWSERS:
            self.browser_var.set(d["browser"])
        if d.get("server") in SERVERS:
            self.server_var.set(d["server"])

        tpl = d.get("template") or "(brak)"
        browser = self.browser_var.get()
        templates = ["(brak)"] + _list_templates(browser)
        if tpl in templates:
            self.template_var.set(tpl)

        if "mode" in d:
            self.mode_var.set(d["mode"])
            self._on_mode_change()

        if "auto_exp" in d:
            self.auto_exp_var.set(bool(d["auto_exp"]))
            self._on_auto_exp_toggle()

        if d.get("exp") in self._exp_map:
            self.exp_var.set(d["exp"])

        if "max_lvl_enabled" in d:
            self.max_lvl_enabled_var.set(bool(d["max_lvl_enabled"]))
        if "max_lvl" in d:
            self.max_lvl_var.set(str(d["max_lvl"]) if d["max_lvl"] else "")
        self._on_max_lvl_toggle()

        if d.get("heros") in self._heros_map:
            self.heros_var.set(d["heros"])

        if "no_attack" in d:
            self.no_attack_var.set(bool(d["no_attack"]))
        if "anti_afk" in d:
            self.anti_afk_var.set(bool(d["anti_afk"]))
        if "recreate" in d:
            self.recreate_var.set(bool(d["recreate"]))
        if "event_rewards" in d:
            self.event_rewards_var.set(bool(d["event_rewards"]))
        if "restart_on_fail" in d:
            self.restart_on_fail_var.set(bool(d["restart_on_fail"]))

        if d.get("e2") in self._e2_map:
            self.e2_var.set(d["e2"])
            self._refresh_e2_positions()
        if d.get("e2_pos") in list(self.e2_pos_cb["values"]):
            self.e2_pos_var.set(d["e2_pos"])
        if "e2_is_leader" in d:
            self.e2_leader_var.set(bool(d["e2_is_leader"]))
        if "e2_is_attacker" in d:
            self.e2_attacker_var.set(bool(d["e2_is_attacker"]))

        if d.get("kolos") in self._kolos_map:
            self.kolos_var.set(d["kolos"])
        if "kolos_is_leader" in d:
            self.kolos_leader_var.set(bool(d["kolos_is_leader"]))
        if "kolos_repeat" in d:
            self.kolos_repeat_var.set(bool(d["kolos_repeat"]))

        if d.get("mine") in self._mine_map:
            self.mine_var.set(d["mine"])
            self._refresh_mine_positions()
        if d.get("mine_pos") in list(self.mine_pos_cb["values"]):
            self.mine_pos_var.set(d["mine_pos"])
        if "mine_auto" in d:
            self.mine_auto_var.set(bool(d["mine_auto"]))

        if d.get("playbook") in self._playbook_map:
            self.playbook_var.set(d["playbook"])

        if "name" in d:
            self.name = str(d["name"])[:20]

        grp_world = d.get("group_world", WORLDS[0])
        group = d.get("group") or self.gm.first_group(grp_world)
        if group and group in self.gm.group_names(grp_world):
            self.gm.assign(self.session_id, group, grp_world)

    def stop_all(self):
        if self._pending_restart is not None:
            self.after_cancel(self._pending_restart)
            self._pending_restart = None
        self.stop_event.set()
        self.pause_event.set()


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
        self._exp_map:       dict = {}
        self._heros_map:     dict = {}
        self._kolos_map:     dict = {}
        self._mine_map:      dict = {}
        self._playbook_map:  dict = {}
        self._e2_map:        dict = {}
        self._sessions:   list = []
        self._session_counter = 0
        self._selected_world: str = WORLDS[0]

        self.gm = GroupManager()

        self._state_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "sessions_state.json")

        self._scan_files()
        self._cleanup_lock_files()
        self._build_ui()
        self._load_state()

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

        exp_dir = os.path.join(base, "exp")
        if os.path.isdir(exp_dir):
            def _exp_level(name):
                m = re.search(r'\((\d+)', name)
                return int(m.group(1)) if m else 0
            for sub in sorted(os.listdir(exp_dir), key=_exp_level):
                r = os.path.join(exp_dir, sub, "route.json")
                if os.path.isfile(r):
                    self._exp_map[sub] = r

        heros_dir = os.path.join(base, "heros")
        if os.path.isdir(heros_dir):
            for sub in sorted(os.listdir(heros_dir)):
                h = os.path.join(heros_dir, sub, "heros.json")
                if os.path.isfile(h):
                    self._heros_map[sub] = h

        kolos_dir = os.path.join(base, "colossus")
        if os.path.isdir(kolos_dir):
            for f in sorted(glob.glob(os.path.join(kolos_dir, "*.json"))):
                key = os.path.splitext(os.path.basename(f))[0]
                self._kolos_map[key] = f

        mine_dir = os.path.join(base, "mine")
        if os.path.isdir(mine_dir):
            for f in sorted(glob.glob(os.path.join(mine_dir, "*.json"))):
                key = os.path.splitext(os.path.basename(f))[0]
                self._mine_map[key] = f

        playbooks_dir = os.path.join(base, "playbooks")
        if os.path.isdir(playbooks_dir):
            for f in sorted(glob.glob(os.path.join(playbooks_dir, "*.json"))):
                key = os.path.splitext(os.path.basename(f))[0]
                self._playbook_map[key] = f

        e2_dir = os.path.join(base, "e2")
        if os.path.isdir(e2_dir):
            for f in sorted(glob.glob(os.path.join(e2_dir, "*.json"))):
                key = os.path.splitext(os.path.basename(f))[0]
                self._e2_map[key] = f

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
        self.collect_btn = tk.Button(btn_frame, text="🗺 Collect",
                                      command=self._on_collect,
                                      bg=BG3, fg=FG, font=FONT_BOLD,
                                      relief="flat", cursor="hand2", padx=10, pady=4)
        self.collect_btn.pack(side="right", padx=(6, 0))
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

        # panel dyspozytorski
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dispatch_panel = DispatchPanel(
            main, self.gm, base_dir,
            get_sessions_fn=lambda: self._sessions)
        self.dispatch_panel.pack(side="left", fill="y", pady=8)

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
            self._config_map, self._exp_map, self._heros_map,
            self.gm,
            name=name,
            on_status_change=self._on_session_status,
            on_config_added=self._on_config_added,
            on_config_refresh=self._on_config_refresh,
            get_all_sessions_fn=lambda: self._sessions,
            kolos_map=self._kolos_map,
            mine_map=self._mine_map,
            playbook_map=self._playbook_map,
            e2_map=self._e2_map,
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

    def _on_collect(self):
        """Uruchamia skanowanie mapy na aktywnej sesji w osobnym wątku."""
        try:
            idx = self.notebook.index(self.notebook.select())
            tab = self._sessions[idx] if idx < len(self._sessions) else None
        except Exception:
            tab = None

        if tab is None:
            from tkinter import messagebox
            messagebox.showinfo("Collect", "Brak aktywnej sesji.", parent=self.root)
            return

        driver = getattr(tab._runner, "driver", None) if tab._runner else None
        if driver is None:
            from tkinter import messagebox
            messagebox.showinfo("Collect", "Sesja nie ma aktywnego drivera.", parent=self.root)
            return

        self.collect_btn.configure(state="disabled", text="⏳ Collect...")

        def _run():
            from collect_world import collect_current_map
            collect_current_map(driver, logger=tab.logger.write)
            self.root.after(0, lambda: self.collect_btn.configure(
                state="normal", text="🗺 Collect"))

        threading.Thread(target=_run, daemon=True).start()

    def _tab_text(self, tab) -> str:
        icons = {"RUNNING": "▶", "PAUSED": "⏸", "STOPPING": "◼", "OFFLINE": "○", "ERROR": "✕"}
        return f"{icons.get(tab.status, '○')} {tab.name}"

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
        self.dispatch_panel.set_group(group_name, self._selected_world)
        if hasattr(self, "add_btn"):
            self._update_add_btn()

    def _on_world_changed(self, world: str):
        self._selected_world = world
        self._group_filter   = None
        self._filter_notebook(None)
        self.dispatch_panel.set_group(None, world)
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
        paused  = sum(1 for s in self._sessions if s.status == "PAUSED")
        total   = len(self._sessions)
        groups  = len(self.gm.group_names())
        self.statusbar.configure(
            text=f"  Sesje: {total}   ▶ Aktywne: {running}   "
                 f"⏸ Wstrzymane: {paused}   ○ Offline: {total-running-paused}"
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

    # ---- persystencja stanu ----
    def _save_state(self):
        state = {
            "groups":   self.gm.to_dict(),
            "sessions": [s.get_settings() for s in self._sessions],
        }
        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
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

        # odtwórz grupy
        for g in state.get("groups", []):
            name  = g.get("name", "")
            color = g.get("color", "")
            world = g.get("world", "Gordion")
            if name and (world, name) not in self.gm._groups:
                self.gm._add_group(name, color, world)
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
        for subdir in ("config", "exp"):
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