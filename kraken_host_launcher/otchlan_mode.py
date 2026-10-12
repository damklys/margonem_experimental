"""Otchłań (matchmaking PvP) mode."""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


def _find(driver, selector):
    try:
        els = driver.find_elements(By.CSS_SELECTOR, selector)
        return els[0] if els else None
    except Exception:
        return None


def _real_click(driver, el):
    try:
        ActionChains(driver).move_to_element(el).click().perform()
        return True
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False


def _press_key(driver, key):
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(key)
    except Exception:
        pass


def _window_open(driver) -> bool:
    try:
        return bool(driver.find_elements(By.CSS_SELECTOR, ".c-window .text[name='Otchłań']"))
    except Exception:
        return False


def _queue_active(driver) -> bool:
    try:
        return bool(driver.find_elements(By.CSS_SELECTOR, ".matchmaking-tile.queue.active"))
    except Exception:
        return False


def _fight_invite(driver):
    """Zwraca przycisk WALCZ z okna zaproszenia do walki."""
    try:
        for el in driver.find_elements(By.CSS_SELECTOR, ".mAlert .alert-accept-hotkey"):
            if el.is_displayed():
                return el
    except Exception:
        pass
    return None


def _walcz_dalej(driver):
    """Zwraca przycisk 'Walcz dalej' jeśli widoczny (pojawia się po walce)."""
    try:
        for btn in driver.find_elements(By.CSS_SELECTOR, ".button, .alert-accept-hotkey"):
            try:
                label = btn.find_element(By.CSS_SELECTOR, ".label")
                if "Walcz dalej" in (label.text or "") and btn.is_displayed():
                    return btn
            except Exception:
                pass
        # fallback: szukaj po tekście label bezpośrednio
        for el in driver.find_elements(By.XPATH,
                "//*[contains(@class,'label') and contains(text(),'Walcz dalej')]"):
            try:
                if el.is_displayed():
                    parent = driver.execute_script(
                        "return arguments[0].closest('.button, .alert-accept-hotkey');", el)
                    return parent if parent else el
            except Exception:
                pass
    except Exception:
        pass
    return None


def _choose_eq_visible(driver) -> bool:
    try:
        panel = _find(driver, ".choose-eq.main-wnd")
        if panel is None:
            return False
        return "display: block" in (panel.get_attribute("style") or "")
    except Exception:
        return False


def _fight_button_active(driver):
    try:
        for c in driver.find_elements(By.CSS_SELECTOR, ".fight-button"):
            if "disable" not in (c.get_attribute("class") or ""):
                return _find(c, ".button") or c
    except Exception:
        pass
    return None


def run_otchlan(driver, stop_event, log=print):
    from captcha import check_and_solve_captcha

    log("⚔️  Otchłań: start")

    while not stop_event.is_set():
        check_and_solve_captcha(driver)

        # --- priorytet 1: Walcz dalej (pojawia się po każdej walce) ---
        btn_dalej = _walcz_dalej(driver)
        if btn_dalej:
            log("🔁 Otchłań: klikam 'Walcz dalej'")
            _real_click(driver, btn_dalej)
            time.sleep(1)
            continue

        # --- priorytet 2: zaproszenie do walki (WALCZ [↵]) ---
        btn_invite = _fight_invite(driver)
        if btn_invite:
            log("⚔️  Otchłań: znaleziono przeciwnika — WALCZ!")
            _real_click(driver, btn_invite)
            time.sleep(1)
            continue

        # --- priorytet 3: panel wyboru zestawu ---
        if _choose_eq_visible(driver):
            log("🎒 Otchłań: wybieram zestaw...")
            builds = driver.find_elements(By.CSS_SELECTOR, ".choose-eq.main-wnd .one-build")
            clicked = False
            for build in builds:
                classes = build.get_attribute("class") or ""
                if "disable" not in classes:
                    try:
                        overlay = build.find_element(By.CSS_SELECTOR, ".build-overlay")
                    except Exception:
                        overlay = build
                    _real_click(driver, overlay)
                    log(f"  kliknięto build")
                    clicked = True
                    break
            if not clicked:
                log("⚠️  Otchłań: wszystkie buildy mają disable — klikam pierwszy z brzegu")
                first = _find(driver, ".choose-eq.main-wnd .one-build .build-overlay")
                if first:
                    _real_click(driver, first)

            # Czekaj na aktywny Walcz
            t0 = time.time()
            while time.time() - t0 < 8 and not stop_event.is_set():
                btn_fight = _fight_button_active(driver)
                if btn_fight:
                    _real_click(driver, btn_fight)
                    log("⚔️  Otchłań: kliknięto 'Walcz'!")
                    time.sleep(1.5)
                    log("⚡ Otchłań: wciskam F (Szybka walka)")
                    _press_key(driver, "f")
                    break
                time.sleep(0.3)
            time.sleep(1)
            continue

        # --- priorytet 4: otwórz okno matchmakingu jeśli zamknięte ---
        if not _window_open(driver):
            log("🎯 Otchłań: klikam przycisk otchłani...")
            widget = _find(driver, ".widget-matchmaking-icon")
            if widget is None:
                log("⚠️  Otchłań: brak przycisku matchmakingu — retry za 3s")
                time.sleep(3)
                continue
            _real_click(driver, widget)
            t0 = time.time()
            while time.time() - t0 < 10 and not stop_event.is_set():
                if _window_open(driver):
                    log("✅ Otchłań: okno otwarte")
                    break
                time.sleep(0.5)
            else:
                log("🔄 Otchłań: okno nie pojawiło się — odświeżam stronę")
                try:
                    driver.refresh()
                except Exception:
                    pass
                time.sleep(4)
            continue

        # --- priorytet 5: dołącz do kolejki (klik w kafelek) ---
        if not _queue_active(driver):
            log("🔍 Otchłań: klikam 'Szukaj walki'...")
            tile = _find(driver, ".matchmaking-tile.queue")
            if tile is None:
                log("⚠️  Otchłań: nie znaleziono kafelka kolejki — retry za 2s")
                time.sleep(2)
                continue
            _real_click(driver, tile)
            t0 = time.time()
            while time.time() - t0 < 5 and not stop_event.is_set():
                if _queue_active(driver):
                    log("✅ Otchłań: kolejka aktywna")
                    break
                time.sleep(0.5)
            else:
                log("⚠️  Otchłań: kolejka nadal nieaktywna po kliknięciu — retry")
            continue

        # Kolejka aktywna — czekamy na przeciwnika
        time.sleep(1)

    log("🛑 Otchłań: stop")
