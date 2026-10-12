from selenium.webdriver.common.by import By
import time


def _parse_style_xy(style: str):
    try:
        parts = dict(
            item.strip().replace("px", "").split(": ")
            for item in style.split(";") if ":" in item
        )
        return float(parts["left"]), float(parts["top"])
    except Exception:
        return None, None


def _center_from_element(el):
    """
    Zwraca (cx, cy, tile) bazując na:
    - left/top ze style
    - width/height z rect
    tile = max(width,height)
    """
    style = el.get_attribute("style") or ""
    left, top = _parse_style_xy(style)
    if left is None or top is None:
        return None, None, None

    r = el.rect
    w = float(r.get("width") or 0)
    h = float(r.get("height") or 0)
    tile = max(w, h) if max(w, h) > 0 else 11.0

    cx = left + w / 2.0
    cy = top + h / 2.0
    return cx, cy, tile


def _in_attack_range(hero_c, heros_c, tile):
    """
    Zasięg ataku: obok + po przekątnej.
    Chebyshev distance <= 1 kafelek (+ tolerancja).
    """
    hx, hy = hero_c
    mx, my = heros_c

    dx = abs(hx - mx) / tile
    dy = abs(hy - my) / tile

    tol = 0.25
    return max(dx, dy) <= 1.0 + tol


def _find_hero(driver):
    return driver.find_element(By.CSS_SELECTOR, "div.mmpMapObject.mmp-hero")


def _find_heros(driver, tip_id: int):
    return driver.find_element(By.CSS_SELECTOR, f'div.mmpMapObject.mmp-heros[tip-id="{tip_id}"]')


def _safe_get_snapshot(driver, tip_id: int):
    """
    Snapshot: (hero_center, heros_center, tile) albo None jeśli brak/DOM się zmienia.
    """
    try:
        hero = _find_hero(driver)
        heros = _find_heros(driver, tip_id)
        hx, hy, tile = _center_from_element(hero)
        mx, my, _ = _center_from_element(heros)
    except Exception:
        return None

    if None in (hx, hy, mx, my, tile):
        return None

    return (hx, hy), (mx, my), tile


def _can_press_q(driver, cooldown_s: float) -> bool:
    """
    Globalny cooldown Q zapisany w driverze.
    """
    now = time.time()
    last = getattr(driver, "_last_q_heros_time", 0.0)
    if now - last >= cooldown_s:
        setattr(driver, "_last_q_heros_time", now)
        return True
    return False


def _press_q(driver):
    driver.find_element(By.TAG_NAME, "body").send_keys("q")


def kill_heros(
    driver,
    tip_id: int,
    poll: float = 0.12,
    max_time_s: float = 30.0,
    repath_if_stuck_s: float = 1.2,
    q_cooldown_s: float = 3.0,
):
    """
    Podchodzi do herosa i atakuje (Q).
    Analogiczna logika do kill_e2.
    """
    t0 = time.time()

    # początkowy klik
    try:
        heros = _find_heros(driver, tip_id)
        driver.execute_script("arguments[0].click();", heros)
        print(f"🎯 Klik heros {tip_id}")
    except Exception:
        print("❌ heros nie istnieje (start)")
        return False

    last_hero_pos = None
    last_move_time = time.time()
    last_repath_time = 0.0

    while True:
        if time.time() - t0 > max_time_s:
            print(f"⏱️ Timeout podejścia do heros {tip_id}")
            return False

        snap = _safe_get_snapshot(driver, tip_id)
        if snap is None:
            # sprawdź czy heros jeszcze istnieje
            try:
                _ = _find_heros(driver, tip_id)
            except Exception:
                print(f"⚰️ heros {tip_id} zniknął")
                return False

            time.sleep(poll)
            continue

        hero_c, heros_c, tile = snap

        # --- jeśli w zasięgu -> Q ---
        if _in_attack_range(hero_c, heros_c, tile):
            if _can_press_q(driver, q_cooldown_s):
                print(f"⚔️ Zasięg OK (tile={tile:.1f}) -> Q na heros")
                _press_q(driver)
                return True
            else:
                time.sleep(poll)
                continue

        # --- wykrywanie "stuck" + re-path ---
        now = time.time()
        if last_hero_pos is None:
            last_hero_pos = hero_c
            last_move_time = now
        else:
            moved = (abs(hero_c[0] - last_hero_pos[0]) > 0.8) or (abs(hero_c[1] - last_hero_pos[1]) > 0.8)
            if moved:
                last_hero_pos = hero_c
                last_move_time = now
            else:
                if (now - last_move_time >= repath_if_stuck_s) and (now - last_repath_time >= 0.8):
                    try:
                        heros = _find_heros(driver, tip_id)
                        driver.execute_script("arguments[0].click();", heros)
                        print(f"🔁 Re-path klik heros {tip_id}")
                        last_repath_time = now
                        last_move_time = now
                    except Exception:
                        print(f"⚰️ heros {tip_id} zniknął przy re-path")
                        return False

        time.sleep(poll)