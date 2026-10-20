import threading
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Maks. 2 sesje jednocześnie przechodzą przez etap logowania.
_LOGIN_GATE    = threading.Semaphore(2)   # max 2 równoległe logowania
_LOGIN_STARTED = threading.Semaphore(0)   # sygnał: sesja weszła do _do_login
_LOGIN_DONE    = threading.Semaphore(0)   # sygnał: logowanie zakończone → zwalnia slot

_PREFLIGHT_BUDGET   = 90   # s na cały etap formularza; przekroczenie → restart sesji
_ENTER_GAME_TIMEOUT = 30   # s na GAME_CANVAS po kliknięciu; przekroczenie → refresh
_POLL              = 0.15  # s między sprawdzeniami DOM


class AccountBanned(Exception):
    """margonem.pl po kliknięciu „Zaloguj się” pokazuje „Konto zostało zablokowane” (#js-ban-box)."""


_JS_BANNED = ("const b=document.getElementById('js-ban-box');"
              "return !!b && b.getClientRects().length>0 && /zablokowane/i.test(b.textContent||'');")


def is_banned(driver) -> bool:
    try:
        return bool(driver.execute_script(_JS_BANNED))
    except WebDriverException:
        return False


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
    Zwraca (None, None) po przekroczeniu deadline. Zablokowane konto → AccountBanned.
    checks = [(nazwa, lambda driver -> element_lub_None), ...]
    """
    while time.time() < deadline:
        if is_banned(driver):
            raise AccountBanned("Konto zostało zablokowane")
        for name, check in checks:
            result = check(driver)
            if result:
                return name, result
        time.sleep(_POLL)
    return None, None


def _fill(driver, el_id, value) -> bool:
    """Wpisuje wartość w pole i sprawdza, że została (przy kilku przeglądarkach naraz strona potrafi jeszcze
    przerysować formularz i wyczyścić pole). Najpierw send_keys, potem – gdy wartość nie została – przez JS
    z wywołaniem zdarzeń input/change. True = pole ma właściwą wartość."""
    for attempt in range(4):
        el = _find(driver, By.ID, el_id)
        if el is None:
            time.sleep(0.5)
            continue
        try:
            if not (el.is_displayed() and el.is_enabled()):
                time.sleep(0.5)
                continue
            el.click()
            el.clear()
            el.send_keys(value)
        except WebDriverException:
            pass
        time.sleep(0.3)
        try:
            el = _find(driver, By.ID, el_id) or el
            if (el.get_attribute("value") or "") == value:
                return True
            driver.execute_script(
                "const e=arguments[0]; e.focus(); e.value=arguments[1];"
                "e.dispatchEvent(new Event('input',{bubbles:true}));"
                "e.dispatchEvent(new Event('change',{bubbles:true}));", el, value)
            time.sleep(0.3)
            if (el.get_attribute("value") or "") == value:
                return True
        except WebDriverException:
            pass
        time.sleep(0.7)
    return False


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
        # Strona dopiero co pokazała formularz – chwila na dokończenie skryptów (przy całej grupie trwa to dłużej).
        time.sleep(1.5)
        for attempt in range(3):
            if is_banned(driver):
                raise AccountBanned("Konto zostało zablokowane")
            # --- Krok 2–3: login i hasło (ze sprawdzeniem, że zostały w polach) ---
            ok_user = _fill(driver, "login-input", username)
            ok_pwd = _fill(driver, "login-password", password)
            if not (ok_user and ok_pwd):
                print(f"⚠️  Logowanie: pola formularza nie przyjęły danych (próba {attempt + 1}/3)")
                if time.time() >= deadline:
                    break
                time.sleep(2)
                continue

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

            # Formularz zniknął (wybór postaci / Wejdź do gry / gra) – zalogowano; nadal jest – kolejna próba.
            what, _ = _wait_first(driver, [
                ("enter",  lambda d: _find(d, By.CSS_SELECTOR, "div.c-btn.enter-game")),
                ("char",   lambda d: _find(d, By.ID, "chnick")),
                ("canvas", lambda d: _find(d, By.CSS_SELECTOR, "canvas#GAME_CANVAS")),
            ], time.time() + 10)
            if what:
                break
            if is_banned(driver):
                raise AccountBanned("Konto zostało zablokowane")
            print(f"⚠️  Logowanie: po kliknięciu „Zaloguj się” nadal formularz (próba {attempt + 1}/3)")
            if time.time() >= deadline:
                break

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
