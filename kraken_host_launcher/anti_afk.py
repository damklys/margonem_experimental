import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def _is_stasis(driver) -> bool:
    """Zwraca True jeśli widoczna jest belka STAN NIEAKTYWNOŚCI."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, ".stasis-overlay__caption")
        return el.is_displayed()
    except Exception:
        return False


def _is_stasis_incoming(driver) -> bool:
    """Zwraca True jeśli widoczny jest komunikat ostrzeżenia przed nieaktywnością."""
    try:
        el = driver.find_element(
            By.CSS_SELECTOR,
            ".stasis-incoming-overlay__text[data-trans='stasis-incoming']",
        )
        return el.is_displayed()
    except Exception:
        return False


def _click_minimap_direction(driver, direction: str) -> bool:
    """
    Klika minimapę jeden kafelek od bohatera w zadanym kierunku.
    Rozmiar kafelka = rozmiar elementu mmp-hero.
    direction: 'down' | 'up' | 'left' | 'right'
    """
    try:
        hero = driver.find_element(By.CSS_SELECTOR, ".mmpMapObject.mmp-hero")
        # Viewport center of hero
        rect = driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {left:r.left, top:r.top, width:r.width, height:r.height};",
            hero,
        )
        cx = rect["left"] + rect["width"]  / 2
        cy = rect["top"]  + rect["height"] / 2

        # CSS tile size (offsetWidth/offsetHeight = CSS px, niezależnie od devicePixelRatio)
        tile_w, tile_h = driver.execute_script(
            "return [arguments[0].offsetWidth, arguments[0].offsetHeight];", hero
        )

        # CSS position of hero from style attribute
        import re as _re
        style = hero.get_attribute("style") or ""
        tm = _re.search(r'top:\s*([\d.]+)px', style)
        lm = _re.search(r'left:\s*([\d.]+)px', style)
        hero_css_top  = float(tm.group(1)) if tm else 0.0
        hero_css_left = float(lm.group(1)) if lm else 0.0

        # Target = jedna kratka w CSS od bohatera; delta CSS → viewport
        if   direction == "down":  dt, dl = tile_h,    0
        elif direction == "up":    dt, dl = -tile_h,   0
        elif direction == "left":  dt, dl = 0,         -tile_w
        else:                      dt, dl = 0,          tile_w   # right

        tx = cx + dl
        ty = cy + dt

        mmap = driver.find_element(By.CSS_SELECTOR, ".mmpMap")
        driver.execute_script("""
            var el = arguments[0];
            var cx = arguments[1];
            var cy = arguments[2];
            ['mousedown', 'mouseup', 'click'].forEach(function(evType) {
                el.dispatchEvent(new MouseEvent(evType, {
                    bubbles: true, cancelable: true, view: window,
                    clientX: cx, clientY: cy
                }));
            });
        """, mmap, tx, ty)
        return True
    except Exception as e:
        print(f"⚠️  Anti-AFK minimap({direction}): {e}")
        return False


def _press_arrow(driver, key, name: str) -> None:
    try:
        ActionChains(driver).key_down(key).pause(0.8).key_up(key).perform()
    except Exception as e:
        print(f"⚠️  Anti-AFK strzałka {name}: {e}")


def _wake_from_stasis(driver) -> bool:
    """
    Próbuje wyjść ze stazy:
      1. Kliknięcia minimapy: dół → góra → lewo → prawo
      2. Fallback strzałki: ↓ ↑ ← →
    Zwraca True gdy staza zniknie.
    """
    for direction in ("down", "up", "left", "right"):
        print(f"🗺️  Anti-AFK: minimap {direction}")
        _click_minimap_direction(driver, direction)
        time.sleep(2.0)
        if not _is_stasis(driver):
            print(f"✅ Anti-AFK: wyszedłem ze stazy (minimap {direction})")
            return True

    for key, name in (
        (Keys.ARROW_DOWN,  "↓"),
        (Keys.ARROW_UP,    "↑"),
        (Keys.ARROW_LEFT,  "←"),
        (Keys.ARROW_RIGHT, "→"),
    ):
        print(f"⌨️  Anti-AFK: strzałka {name}")
        _press_arrow(driver, key, name)
        time.sleep(1.5)
        if not _is_stasis(driver):
            print(f"✅ Anti-AFK: wyszedłem ze stazy (strzałka {name})")
            return True

    print("⚠️  Anti-AFK: nie udało się wyjść ze stazy")
    return False


class AntiAFK:
    """Wykrywa STAN NIEAKTYWNOŚCI i budzi postać."""

    def __init__(self, min_interval: int = 120, max_interval: int = 300):
        # Parametry zachowane dla kompatybilności z istniejącym kodem
        self.min_interval = min_interval
        self.max_interval = max_interval
        print("🤖 Anti-AFK zainicjalizowany (tryb: detekcja stazy)")

    def check_and_move(self, driver) -> bool:
        """
        Sprawdza aktywny stan nieaktywności i ostrzeżenie przed nim. Budzi lub zapobiega.
        Zwraca True jeśli wykonano akcję.
        """
        if _is_stasis(driver):
            print("\n" + "=" * 50)
            print("😴 STAN NIEAKTYWNOŚCI wykryty — budzę postać...")
            print("=" * 50)
            result = _wake_from_stasis(driver)
            print("=" * 50 + "\n")
            return result

        if _is_stasis_incoming(driver):
            print("⚠️  Ostrzeżenie o nieaktywności — ruch prewencyjny...")
            _click_minimap_direction(driver, "down")
            time.sleep(0.4)
            _click_minimap_direction(driver, "up")
            return True

        return False


def check_interrupts(driver, logger=None) -> bool:
    """
    Sprawdza captchę i stan nieaktywności (ostrzeżenie + aktywny).
    Wywołuj w każdej pętli oczekiwania/nawigacji.
    Zwraca True jeśli coś zostało obsłużone.
    """
    def _log(msg):
        if logger:
            logger(msg)
        else:
            print(msg)

    handled = False

    try:
        from captcha import check_and_solve_captcha
        if check_and_solve_captcha(driver):
            handled = True
    except Exception as e:
        _log(f"⚠️  captcha check error: {e}")

    try:
        if _is_stasis(driver):
            _log("😴 STAN NIEAKTYWNOŚCI — budzę postać...")
            _wake_from_stasis(driver)
            handled = True
        elif _is_stasis_incoming(driver):
            _log("⚠️  Ostrzeżenie o nieaktywności — ruch prewencyjny...")
            _click_minimap_direction(driver, "down")
            time.sleep(0.4)
            _click_minimap_direction(driver, "up")
            handled = True
    except Exception as e:
        _log(f"⚠️  stasis check error: {e}")

    return handled
