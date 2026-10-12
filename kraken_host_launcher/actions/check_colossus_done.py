from __future__ import annotations

import time
from typing import Optional

from selenium.webdriver.common.by import By


def check_colossus_done(
    driver,
    exit_location: Optional[str] = None,
    stop_event=None,
    log_fn=print,
) -> bool:
    """
    Otwiera okno Świat → Panel aktywności i sprawdza czy
    'Pokonaj kolosa' ma klasę is-done (już dziś pokonany).

    Jeśli pokonany: opuszcza grupę (jeśli w niej jest),
    nawiguje do exit_location i zwraca True.
    Jeśli nie pokonany: zamyka okno i zwraca False.
    """

    def _world_window_visible() -> bool:
        try:
            el = driver.find_element(By.CSS_SELECTOR, "div.world-window")
            return el.is_displayed()
        except Exception:
            return False

    def _close_world_window() -> None:
        try:
            close_btn = driver.execute_script("""
                var ww = document.querySelector('div.world-window');
                if (!ww) return null;
                var win = ww.closest('div.c-window');
                if (!win) return null;
                return win.querySelector('.close-button-corner-decor .close-button');
            """)
            if close_btn:
                driver.execute_script("arguments[0].click();", close_btn)
        except Exception:
            pass

    log_fn("🌍 check_colossus_done: sprawdzam Panel aktywności…")

    # Klikaj przycisk Świat co 2s aż okno się pojawi (max 20s)
    t0 = time.time()
    opened = False
    while time.time() - t0 < 20:
        if _world_window_visible():
            opened = True
            break
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "div.widget-world-icon")
            driver.execute_script("arguments[0].click();", btn)
        except Exception as e:
            log_fn(f"⚠️  check_colossus_done: nie znaleziono przycisku Świat — {e}")
            return False
        time.sleep(2.0)

    if not opened:
        log_fn("⚠️  check_colossus_done: okno Świat nie otworzyło się")
        return False

    time.sleep(0.4)

    # Kliknij zakładkę Panel aktywności
    try:
        tab = driver.find_element(By.CSS_SELECTOR, "div.world-window .activities-tab")
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(0.8)
    except Exception as e:
        log_fn(f"⚠️  check_colossus_done: nie znaleziono zakładki aktywności — {e}")
        _close_world_window()
        return False

    # Sprawdź czy 'Pokonaj kolosa' ma klasę is-done
    done = False
    try:
        cells = driver.find_elements(By.CSS_SELECTOR, "td.activities__name")
        for cell in cells:
            if "Pokonaj kolosa" in (cell.text or ""):
                classes = cell.get_attribute("class") or ""
                if "is-done" in classes:
                    done = True
                break
    except Exception as e:
        log_fn(f"⚠️  check_colossus_done: błąd sprawdzania aktywności — {e}")

    _close_world_window()
    time.sleep(0.3)

    if not done:
        log_fn("⚔️  check_colossus_done: kolos jeszcze nie pokonany — kontynuuję")
        return False

    log_fn("✅ check_colossus_done: kolos już dziś pokonany")

    # Opuść grupę jeśli w niej jesteś
    try:
        kick = driver.find_element(By.CSS_SELECTOR, "div.kick-out-party.kick-out")
        if kick.is_displayed():
            driver.execute_script("arguments[0].click();", kick)
            log_fn("👋 check_colossus_done: opuściłem grupę")
            time.sleep(1.0)
    except Exception:
        pass

    # Nawiguj do exit_location
    if exit_location:
        log_fn(f"🗺️  check_colossus_done: nawiguję do '{exit_location}'…")
        try:
            from move import travel_to
            travel_to(driver, exit_location, stop_event=stop_event)
            log_fn(f"✅ check_colossus_done: dotarłem do '{exit_location}'")
        except Exception as e:
            log_fn(f"⚠️  check_colossus_done: błąd nawigacji — {e}")

    return True


def load_from_json(cfg: dict) -> dict:
    result = {}
    if "exit_location" in cfg:
        result["exit_location"] = cfg["exit_location"]
    return result
