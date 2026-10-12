import threading
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Maks. 2 sesje jednocześnie przechodzą przez etap logowania.
_LOGIN_GATE    = threading.Semaphore(2)   # max 2 równoległe logowania
_LOGIN_STARTED = threading.Semaphore(0)   # sygnał: sesja weszła do _do_login
_LOGIN_DONE    = threading.Semaphore(0)   # sygnał: logowanie zakończone → zwalnia slot

_PREFLIGHT_BUDGET   = 60   # s na cały etap formularza; przekroczenie → restart sesji
_ENTER_GAME_TIMEOUT = 30   # s na GAME_CANVAS po kliknięciu; przekroczenie → refresh
_POLL              = 0.15  # s między sprawdzeniami DOM


def login(driver, username, password):
    _LOGIN_GATE.acquire()
    try:
        _do_login(driver, username, password)
    finally:
        _LOGIN_GATE.release()
        _LOGIN_DONE.release()


def _find(driver, by, selector):
    """Zwraca pierwszy pasujący element lub None — bez wyjątków."""
    try:
        els = driver.find_elements(by, selector)
        return els[0] if els else None
    except WebDriverException:
        return None


def _wait_first(driver, checks: list, deadline: float):
    """
    Polling-loop: zwraca (nazwa, element) gdy którykolwiek warunek zostanie spełniony.
    Zwraca (None, None) po przekroczeniu deadline.
    checks = [(nazwa, lambda driver -> element_lub_None), ...]
    """
    while time.time() < deadline:
        for name, check in checks:
            result = check(driver)
            if result:
                return name, result
        time.sleep(_POLL)
    return None, None


def _do_login(driver, username, password):
    _LOGIN_STARTED.release()

    deadline = time.time() + _PREFLIGHT_BUDGET

    # --- Krok 1: czekaj na formularz, wybranie postaci lub link logowania ---
    what, el = _wait_first(driver, [
        ("form",  lambda d: _find(d, By.ID, "login-input")),
        ("char",  lambda d: _find(d, By.ID, "chnick")),          # już zalogowany
        ("enter", lambda d: _find(d, By.CSS_SELECTOR, "div.c-btn.enter-game")),
        ("link",  lambda d: _find(d, By.LINK_TEXT, "Zaloguj się na Stronie Głównej")),
    ], deadline)

    if what == "link":
        try:
            el.click()
        except WebDriverException:
            pass
        what, el = _wait_first(driver, [
            ("form", lambda d: _find(d, By.ID, "login-input")),
            ("char", lambda d: _find(d, By.ID, "chnick")),
        ], deadline)

    if time.time() >= deadline or what is None:
        raise RuntimeError(f"Login preflight timeout ({_PREFLIGHT_BUDGET}s) – restart sesji")

    # Jeśli postać już wybrana — przejdź od razu do kroku "Wejdź do gry"
    if what in ("char", "enter"):
        pass  # pomiń formularz, idź do kroku 5

    else:
        # --- Krok 2: wpisz login ---
        login_el = _find(driver, By.ID, "login-input") or el
        if login_el:
            try:
                login_el.clear()
                login_el.send_keys(username)
            except WebDriverException:
                pass

        # --- Krok 3: wpisz hasło ---
        pwd_el = _find(driver, By.ID, "login-password")
        if pwd_el:
            try:
                pwd_el.clear()
                pwd_el.send_keys(password)
            except WebDriverException:
                pass

        # --- Krok 4: kliknij przycisk "Zaloguj się" ---
        btn = _find(driver, By.ID, "js-login-btn")
        if btn is None:
            btn = _find(driver, By.XPATH,
                        "//span[text()='Zaloguj się']/ancestor::button | "
                        "//span[text()='Zaloguj się']/ancestor::div[contains(@class,'btn')]")
        if btn:
            try:
                driver.execute_script("arguments[0].click();", btn)
            except WebDriverException:
                pass

        if time.time() >= deadline:
            raise RuntimeError(f"Login preflight timeout ({_PREFLIGHT_BUDGET}s) – restart sesji")

    # --- Krok 5: "Wejdź do gry" → retry z refresh aż do GAME_CANVAS ---

    # Najpierw poczekaj aż przycisk "Wejdź do gry" pojawi się (lub GAME_CANVAS od razu)
    what, _ = _wait_first(driver, [
        ("enter",  lambda d: _find(d, By.CSS_SELECTOR, "div.c-btn.enter-game")),
        ("canvas", lambda d: _find(d, By.CSS_SELECTOR, "canvas#GAME_CANVAS")),
    ], time.time() + _ENTER_GAME_TIMEOUT)

    while True:
        if what == "canvas":
            return  # sukces

        if what is None:
            # Timeout bez przycisku — refresh
            try:
                driver.refresh()
            except WebDriverException:
                pass
            time.sleep(1.5)
            what, _ = _wait_first(driver, [
                ("enter",  lambda d: _find(d, By.CSS_SELECTOR, "div.c-btn.enter-game")),
                ("canvas", lambda d: _find(d, By.CSS_SELECTOR, "canvas#GAME_CANVAS")),
            ], time.time() + _ENTER_GAME_TIMEOUT)
            continue

        # Zamknij popup jeśli widoczny
        popup = _find(driver, By.CSS_SELECTOR,
                      "div.disabled-enter-game-info div.close-game-info")
        if popup:
            try:
                driver.execute_script("arguments[0].click();", popup)
                time.sleep(3)
            except WebDriverException:
                pass

        # Kliknij "Wejdź do gry"
        enter_btn = _find(driver, By.CSS_SELECTOR, "div.c-btn.enter-game")
        if enter_btn:
            try:
                driver.execute_script("arguments[0].click();", enter_btn)
            except WebDriverException:
                pass

        # Po kliknięciu: krótka pauza żeby strona zaczęła nawigację
        # (przycisk nadal jest chwilowo w DOM — nie sprawdzamy go ponownie)
        time.sleep(1.5)

        # Teraz czekaj TYLKO na GAME_CANVAS
        what, _ = _wait_first(driver, [
            ("canvas", lambda d: _find(d, By.CSS_SELECTOR, "canvas#GAME_CANVAS")),
        ], time.time() + _ENTER_GAME_TIMEOUT)

        if what == "canvas":
            return  # sukces

        # Timeout — refresh i wróć do czekania na przycisk
        try:
            driver.refresh()
        except WebDriverException:
            pass
        time.sleep(1.5)
        what, _ = _wait_first(driver, [
            ("enter",  lambda d: _find(d, By.CSS_SELECTOR, "div.c-btn.enter-game")),
            ("canvas", lambda d: _find(d, By.CSS_SELECTOR, "canvas#GAME_CANVAS")),
        ], time.time() + _ENTER_GAME_TIMEOUT)
